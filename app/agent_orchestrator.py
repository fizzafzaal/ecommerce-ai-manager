"""Agentic orchestrator: Groq is the reasoning brain that delegates to the
specialist agents (product, refund) exposed as *tools*.

Key guarantees, unchanged from the deterministic design:
- Business decisions stay in Python. Groq can *call* request_refund, but the
  eligibility rules run in RefundAgent on real data -- Groq cannot approve a
  refund the rules would reject, or invent a product/price/order.
- The customer id is injected server-side from the logged-in session; it is
  NEVER a tool argument the model controls, so the model can't reach another
  customer's data.
- If Groq is unavailable (no key, network error), we fall back to the local
  phi-based Orchestrator, so the assistant still works offline.
"""

import json

from groq import Groq
from loguru import logger

from app.config import settings
from app.database import SessionLocal
from app.models import Customer, Product

SYSTEM_PROMPT = """You are a friendly, concise shopping assistant for an online store called "AI Store". \
You are chatting with {name}.

You can help with three things, using your tools:
- Finding products (search_products)
- Looking up this customer's own orders (get_my_orders)
- Processing refunds (request_refund)

Store policies:
- Refunds are allowed within 30 days of purchase, for orders that belong to the customer and haven't already been refunded.
- Standard shipping takes 3-5 business days.
- We accept all major credit cards and PayPal.

Important rules:
- ALWAYS use the tools to get real product, order, and refund information. NEVER make up products, prices, stock levels, order numbers, or refund outcomes.
- The refund decision is made by the store's rules via request_refund -- report exactly what the tool returns; never claim a refund succeeded unless the tool says so.
- If the customer wants a refund but didn't say which order, call get_my_orders and help them find it.
- Keep replies short, warm, and helpful. If something is unrelated to shopping, gently steer back to how you can help."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the store's product catalog by natural-language query. Use for any product discovery, recommendation, or 'do you have X' request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What the customer is looking for, e.g. 'warm winter jacket'",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Optional: only return products at or below this price.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter, e.g. 'Electronics'.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_orders",
            "description": "List the current customer's past orders with their items, totals, dates, and whether each is eligible for a refund. Use when the customer asks about their orders, or wants a refund without giving an order number.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_refund",
            "description": "Attempt a refund for one of the current customer's orders. The store's rules decide eligibility (within 30 days, belongs to the customer, not already refunded). Only call once you know the order id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "The id of the order to refund."}
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_marketing_copy",
            "description": "Generate catchy marketing copy / a promotional description for a store product. Use when asked to write an ad, tagline, or product description. Return the copy to the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "The product name (or id) to write copy for.",
                    },
                    "style": {
                        "type": "string",
                        "description": "Optional tone/style, e.g. 'luxury', 'playful', 'minimal'.",
                    },
                },
                "required": ["product"],
            },
        },
    },
]

MAX_TOOL_TURNS = 5
HISTORY_TURNS = 10  # how many prior messages to send back for context


class AgentOrchestrator:
    """Runs the Groq tool-calling loop, delegating to the specialist agents."""

    def __init__(self, product_agent, refund_agent, marketing_agent, fallback):
        self.product_agent = product_agent
        self.refund_agent = refund_agent
        self.marketing_agent = marketing_agent
        self.fallback = fallback  # the local Orchestrator, used if Groq fails
        self.client = Groq(api_key=settings.groq_api_key) if settings.groq_enabled else None

    def handle_message(self, message: str, customer_id: int, history: list | None = None) -> dict:
        if self.client is None:
            return self.fallback.handle_message(message, customer_id, history=history)
        try:
            return self._run_groq(message, customer_id, history or [])
        except Exception as e:
            logger.error(f"Groq orchestration failed, falling back to local: {e}")
            return self.fallback.handle_message(message, customer_id, history=history)

    # --- Groq tool-calling loop ---

    def _run_groq(self, message: str, customer_id: int, history: list) -> dict:
        name = self._customer_name(customer_id)
        messages = [{"role": "system", "content": SYSTEM_PROMPT.format(name=name)}]
        # Include recent prior turns so the assistant remembers context
        # (e.g. "yes, refund it" after it offered a specific order). Capped
        # to the last few turns to keep the request small.
        for turn in history[-HISTORY_TURNS:]:
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})
        tools_used = []

        for _ in range(MAX_TOOL_TURNS):
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=600,
                timeout=30,
            )
            choice = response.choices[0].message

            if not choice.tool_calls:
                return self._response(choice.content or "", tools_used)

            # Record the assistant's tool-call turn, then run each tool.
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in choice.tool_calls
                    ],
                }
            )
            for tc in choice.tool_calls:
                tools_used.append(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._execute_tool(tc.function.name, args, customer_id)
                logger.info(f"tool {tc.function.name}({args}) for customer={customer_id}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, default=str),
                    }
                )

        # Ran out of tool turns; ask the model for a final answer without tools.
        final = self.client.chat.completions.create(
            model=settings.groq_model, messages=messages, temperature=0.3, max_tokens=600, timeout=30
        )
        return self._response(final.choices[0].message.content or "", tools_used)

    # --- Tool implementations (delegate to the specialist agents) ---

    def _execute_tool(self, name: str, args: dict, customer_id: int) -> dict:
        if name == "search_products":
            result = self.product_agent.run(query=args.get("query", ""))
            products = result.get("results", [])
            category = args.get("category")
            if category:
                products = [p for p in products if p["category"].lower() == category.lower()]
            max_price = args.get("max_price")
            if max_price is not None:
                products = [p for p in products if p["price"] <= max_price]
            return {"products": products[:6]}

        if name == "get_my_orders":
            orders = self.refund_agent.get_customer_orders(customer_id)
            return {
                "orders": [
                    {
                        "order_id": o["id"],
                        "ordered": o["date"].strftime("%Y-%m-%d"),
                        "days_ago": o["age_days"],
                        "status": o["status"],
                        "total": o["total"],
                        "products": o["products"],
                        "eligible_for_refund": o["eligible"],
                    }
                    for o in orders
                ]
            }

        if name == "request_refund":
            order_id = args.get("order_id")
            if order_id is None:
                return {"error": "no order_id provided"}
            return self.refund_agent.run(order_id=int(order_id), customer_id=customer_id)

        if name == "write_marketing_copy":
            product_id = self._resolve_product_id(args.get("product", ""))
            if product_id is None:
                return {"error": "product not found"}
            return self.marketing_agent.run(product_id=product_id, style=args.get("style"))

        return {"error": f"unknown tool {name}"}

    def _resolve_product_id(self, product: str) -> int | None:
        """Resolve a product reference (an id or a name) to a product id."""
        product = str(product).strip()
        db = SessionLocal()
        try:
            if product.isdigit():
                found = db.get(Product, int(product))
                return found.id if found else None
            match = db.query(Product).filter(Product.name.ilike(f"%{product}%")).first()
            return match.id if match else None
        finally:
            db.close()

    def _customer_name(self, customer_id: int) -> str:
        db = SessionLocal()
        try:
            customer = db.get(Customer, customer_id)
            return customer.name if customer else "a customer"
        finally:
            db.close()

    def _response(self, reply: str, tools_used: list[str]) -> dict:
        return {
            "reply": reply,
            "intent": tools_used[-1] if tools_used else "chat",
            "llm_formatted": True,
        }
