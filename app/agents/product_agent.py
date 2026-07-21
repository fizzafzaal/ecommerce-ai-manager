"""Semantic product search + live stock check.

Searches the Chroma product index for a free-text query, then joins
each hit back to SQLite for current stock numbers and flags anything
under LOW_STOCK_THRESHOLD.
"""

from app.agents.base_agent import BaseAgent
from app.database import SessionLocal
from app.models import Product
from app.vector_store import search_products

LOW_STOCK_THRESHOLD = 5


class ProductAgent(BaseAgent):
    name = "product_agent"
    timeout_seconds = 15.0

    def process(self, query: str, n_results: int = 5) -> dict:
        results = search_products(query, n_results=n_results)
        product_ids = results["ids"][0] if results["ids"] else []

        db = SessionLocal()
        try:
            products = []
            for product_id in product_ids:
                product = db.get(Product, int(product_id))
                if product is None:
                    continue
                stock = product.inventory.stock_quantity if product.inventory else 0
                products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "category": product.category,
                        "price": product.price,
                        "stock": stock,
                        "low_stock": stock < LOW_STOCK_THRESHOLD,
                    }
                )
            return {"query": query, "results": products}
        finally:
            db.close()
