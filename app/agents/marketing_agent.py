"""Generates marketing copy for a product, grounded in its real details.

Unlike the refund/product agents (which make decisions or fetch data), this
agent's whole job is *language*: it turns a product's real facts into catchy
promotional copy. It never invents features -- the prompt is built from the
product's actual name, category, price, and description in the database.
"""

from app.agents.base_agent import BaseAgent
from app.database import SessionLocal
from app.llm import generate_text
from app.models import Product

MARKETING_PROMPT = """You are a marketing copywriter for an online store. Write a short, catchy \
product description to display on the store, based only on the real details below. \
Keep it to 2-3 upbeat, persuasive sentences. Do not invent features or specs beyond what's given.

Product name: {name}
Category: {category}
Price: ${price:.2f}
Details: {description}
{style_line}
Marketing description:"""


class MarketingAgent(BaseAgent):
    name = "marketing_agent"
    timeout_seconds = 35.0

    def process(self, product_id: int, style: str | None = None) -> dict:
        db = SessionLocal()
        try:
            product = db.get(Product, product_id)
            if product is None:
                return {"success": False, "error": "product_not_found"}

            style_line = f"Preferred tone/style: {style}." if style else ""
            prompt = MARKETING_PROMPT.format(
                name=product.name,
                category=product.category,
                price=product.price,
                description=product.description,
                style_line=style_line,
            )
            copy = generate_text(prompt, max_tokens=256, temperature=0.8)
            return {"product": product.name, "marketing_copy": copy}
        finally:
            db.close()
