"""Deterministic router that coordinates the agents -- NOT an LLM.

Plain Python decides which agent(s) run for a given message, based on
the intent the Support Agent detected plus deterministic signal checks
(an order number, refund/product keywords). Routing never depends solely
on the LLM's guess, so a misclassification can't drop a refund.

All replies are built deterministically from agent data -- refund
decisions, amounts, product names, prices, stock -- so the model can
never corrupt a number or invent a stock status. Replies are also fast:
once intent is known, no further model call is needed.
"""

import re

from loguru import logger

from app.agents.product_agent import ProductAgent
from app.agents.refund_agent import RefundAgent
from app.agents.support_agent import CAPABILITIES_REPLY, KEYWORD_INTENT_MAP, SupportAgent

REFUND_KEYWORDS = KEYWORD_INTENT_MAP["refund"]

# Signals that the customer also wants product suggestions, even when the
# primary intent is a refund (e.g. "refund order 5 and show me similar
# items"). Plain keywords keep routing deterministic.
PRODUCT_FOLLOWUP_KEYWORDS = ["similar", "recommend", "suggestion", "show me", "see other", "alternative"]

# Generic words in product names that shouldn't count as a match on their
# own (so "set" doesn't match every "... Set" order).
_STOPWORDS = {"set", "pack", "with", "and", "the", "for", "kit", "pro", "plus", "mah"}


class Orchestrator:
    """Owns the request lifecycle: detect -> route -> run -> merge -> phrase."""

    def __init__(self):
        self.support_agent = SupportAgent()
        self.refund_agent = RefundAgent()
        self.product_agent = ProductAgent()

    def handle_message(self, message: str, customer_id: int) -> dict:
        support_result = self.support_agent.run(message=message)
        intent = support_result.get("intent", "unknown")
        entities = support_result.get("entities", {})

        logger.info(f"Routing message with intent='{intent}' for customer={customer_id}")

        # FAQ short-circuits: the answer is already canned text, no agents
        # or LLM needed. Small-talk (greetings, thanks, "what can you do") is
        # handled the same way -- a canned answer, detected before the model.
        if intent in ("faq", "smalltalk"):
            answer = support_result.get("answer", "")
            return self._response(reply=answer, intent=intent, agent_outputs={}, formatted=False)

        agent_outputs: dict = {}

        # Refund routing is deterministic: an order number plus a refund
        # signal (LLM intent OR a refund keyword) runs the refund agent,
        # regardless of whether the LLM's single-label guess was "refund".
        order_id = entities.get("order_id")
        if order_id is not None and (intent == "refund" or self._mentions_refund(message)):
            agent_outputs["refund"] = self.refund_agent.run(
                order_id=order_id, customer_id=customer_id
            )
        elif intent == "refund":
            # Refund wanted but no order number given -- instead of just
            # asking for one, look up the customer's orders and either point
            # at the one they mean (e.g. "refund for kettle") or list them.
            agent_outputs["refund_help"] = self._refund_help(message, customer_id)

        if intent == "product_search" or self._wants_products_too(message):
            query = entities.get("product_query", message)
            agent_outputs["products"] = self.product_agent.run(query=query)

        if not agent_outputs:
            # No task and not small-talk: nudge toward what the assistant does.
            reply = (
                "I'm not sure I can help with that specific request, but here's what "
                f"I can do:\n\n{CAPABILITIES_REPLY}"
            )
            return self._response(reply=reply, intent=intent, agent_outputs={}, formatted=False)

        reply = self._build_factual_reply(agent_outputs)
        return self._response(
            reply=reply, intent=intent, agent_outputs=agent_outputs, formatted=False
        )

    def _refund_help(self, message: str, customer_id: int) -> dict:
        """Help a customer who wants a refund but didn't give an order number:
        match their message to one of their orders, or list recent orders."""
        orders = self.refund_agent.get_customer_orders(customer_id)
        if not orders:
            return {
                "text": "I don't see any orders on your account yet, so there's "
                "nothing to refund. Once you've placed an order I can help you return it."
            }

        matched = [o for o in orders if self._order_matches_message(o, message)]
        if len(matched) == 1:
            return {"text": self._describe_order_for_refund(matched[0])}
        if len(matched) > 1:
            return {
                "text": "I found a few orders that might match:\n"
                + self._orders_list(matched)
                + '\n\nWhich one? Reply with, for example, "refund order #'
                + str(matched[0]["id"])
                + '".'
            }
        # No product match -- show recent orders so they can choose.
        return {
            "text": "I couldn't tell which order you mean. Here are your recent orders:\n"
            + self._orders_list(orders[:5])
            + '\n\nWhich would you like to refund? Reply with, for example, '
            '"refund order #' + str(orders[0]["id"]) + '".'
        }

    def _order_matches_message(self, order: dict, message: str) -> bool:
        """True if a meaningful word from any product in the order appears in
        the message (e.g. "kettle" matches a "Stainless Steel Electric Kettle")."""
        lowered = message.lower()
        for name in order["products"]:
            for word in re.findall(r"[a-z]{3,}", name.lower()):
                if word not in _STOPWORDS and re.search(rf"\b{word}\b", lowered):
                    return True
        return False

    def _describe_order_for_refund(self, order: dict) -> str:
        items = ", ".join(order["products"])
        if order["eligible"]:
            return (
                f"I found your order #{order['id']}: {items} — ${order['total']:.2f}, "
                f"placed {order['age_days']} day(s) ago. It's eligible for a refund. "
                f'To go ahead, reply "refund order #{order["id"]}".'
            )
        if order["status"] == "refunded":
            reason = "it has already been refunded"
        else:
            reason = f"it's outside our 30-day return window (placed {order['age_days']} days ago)"
        return (
            f"I found your order #{order['id']}: {items} — ${order['total']:.2f}. "
            f"Unfortunately {reason}, so it isn't eligible for a refund."
        )

    def _orders_list(self, orders: list[dict]) -> str:
        lines = []
        for o in orders:
            items = ", ".join(o["products"])
            if o["status"] == "refunded":
                tag = " — already refunded"
            elif not o["eligible"]:
                tag = " — outside 30-day window"
            else:
                tag = " — eligible for refund"
            lines.append(f"- Order #{o['id']}: {items} — ${o['total']:.2f}{tag}")
        return "\n".join(lines)

    def _mentions_refund(self, message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in REFUND_KEYWORDS)

    def _wants_products_too(self, message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in PRODUCT_FOLLOWUP_KEYWORDS)

    def _build_factual_reply(self, agent_outputs: dict) -> str:
        """Assemble the reply from agent results. Fully deterministic --
        every number and name here comes straight from our data."""
        parts = []
        if "refund" in agent_outputs:
            parts.append(self._refund_text(agent_outputs["refund"]))
        if "refund_help" in agent_outputs:
            parts.append(agent_outputs["refund_help"]["text"])
        if "products" in agent_outputs:
            parts.append(self._products_text(agent_outputs["products"]))
        return "\n\n".join(part for part in parts if part)

    def _refund_text(self, refund: dict) -> str:
        if refund.get("approved"):
            amount = refund.get("refund_amount", 0)
            return f"Your refund has been approved. A total of ${amount:.2f} will be returned to you."

        reason_messages = {
            "order_not_found": "I couldn't find that order in our system.",
            "order_not_owned_by_customer": "That order doesn't appear to belong to your account.",
            "already_refunded": "That order has already been refunded.",
            "outside_refund_window": "That order is outside our 30-day refund window, so it isn't eligible.",
            "no_order_id": "I couldn't tell which order you'd like refunded -- could you share the order number?",
        }
        reason = refund.get("reason", "")
        return reason_messages.get(reason, "I wasn't able to process that refund request.")

    def _products_text(self, product_result: dict) -> str:
        results = product_result.get("results", [])
        if not results:
            return "I couldn't find any products matching that."

        lines = ["Here are some products that might interest you:"]
        for p in results:
            stock_note = " (low stock!)" if p.get("low_stock") else ""
            lines.append(f"- {p['name']} - ${p['price']:.2f}{stock_note}")
        return "\n".join(lines)

    def _response(self, reply: str, intent: str, agent_outputs: dict, formatted: bool) -> dict:
        return {
            "reply": reply,
            "intent": intent,
            "agent_outputs": agent_outputs,
            "llm_formatted": formatted,
        }
