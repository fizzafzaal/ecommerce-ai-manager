"""Deterministic router that coordinates the agents -- NOT an LLM.

Plain Python decides which agent(s) run for a given message, based on
the intent the Support Agent detected plus deterministic signal checks
(an order number, refund/product keywords). Routing never depends solely
on the LLM's guess, so a misclassification can't drop a refund.

The only LLM use here is generating a short, friendly opening line. All
facts -- refund decisions, amounts, product names, prices, stock -- are
built deterministically from agent data and are NEVER sent through the
LLM to be reworded, so the model cannot corrupt a number or invent a
stock status. If the LLM is slow or unavailable, we simply drop the
opener and return the factual reply on its own.
"""

from loguru import logger

from app.agents.product_agent import ProductAgent
from app.agents.refund_agent import RefundAgent
from app.agents.support_agent import KEYWORD_INTENT_MAP, SupportAgent
from app.config import settings
from app.llm import FALLBACK_MESSAGE, ask_llm

REFUND_KEYWORDS = KEYWORD_INTENT_MAP["refund"]

# Signals that the customer also wants product suggestions, even when the
# primary intent is a refund (e.g. "refund order 5 and show me similar
# items"). Plain keywords keep routing deterministic.
PRODUCT_FOLLOWUP_KEYWORDS = ["similar", "recommend", "suggestion", "show me", "see other", "alternative"]

INTRO_PROMPT = (
    "Write one short, warm, friendly opening sentence for a customer-service "
    "reply. Do not mention any specific products, prices, or order details -- "
    "just a greeting that leads into helping them. Situation: {situation}.\n"
    "Sentence:"
)


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
        # or LLM needed.
        if intent == "faq":
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
            # Refund clearly wanted, but we couldn't find an order number.
            agent_outputs["refund"] = {"approved": False, "reason": "no_order_id"}

        if intent == "product_search" or self._wants_products_too(message):
            query = entities.get("product_query", message)
            agent_outputs["products"] = self.product_agent.run(query=query)

        if not agent_outputs:
            reply = (
                "I'm not sure I understood that. I can help with refunds, "
                "product searches, and general questions -- could you rephrase?"
            )
            return self._response(reply=reply, intent=intent, agent_outputs={}, formatted=False)

        facts = self._build_factual_reply(agent_outputs)
        intro = self._friendly_intro(agent_outputs)
        reply = f"{intro}\n\n{facts}" if intro else facts
        return self._response(
            reply=reply, intent=intent, agent_outputs=agent_outputs, formatted=bool(intro)
        )

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

    def _friendly_intro(self, agent_outputs: dict) -> str:
        """One friendly opening line from the LLM. Returns '' on any
        failure -- or when the LLM is disabled (safe mode) -- so the
        factual reply can stand on its own."""
        if not settings.use_llm:
            return ""
        situation = self._describe_situation(agent_outputs)
        intro = ask_llm(INTRO_PROMPT.format(situation=situation), max_tokens=40)
        if not intro or intro == FALLBACK_MESSAGE:
            return ""
        # Guard against a rambling model: keep only the first line.
        return intro.strip().splitlines()[0].strip()

    def _describe_situation(self, agent_outputs: dict) -> str:
        bits = []
        if "refund" in agent_outputs:
            bits.append("responding to a refund request")
        if "products" in agent_outputs:
            bits.append("sharing some product suggestions")
        return " and ".join(bits) if bits else "helping a customer"

    def _response(self, reply: str, intent: str, agent_outputs: dict, formatted: bool) -> dict:
        return {
            "reply": reply,
            "intent": intent,
            "agent_outputs": agent_outputs,
            "llm_formatted": formatted,
        }
