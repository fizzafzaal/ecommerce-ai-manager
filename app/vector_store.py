"""ChromaDB vector store for semantic product search.

build_product_index() is a one-time (or re-runnable) job that embeds
every product's name + description and stores it in a local, persistent
Chroma collection. The Product Agent queries this collection instead of
re-embedding products on every search.
"""

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from app.config import settings
from app.database import SessionLocal
from app.models import Product

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "products"

# ChromaDB 0.5.x still fires telemetry events even with them disabled,
# spamming harmless "Failed to send telemetry event" errors (a posthog
# version mismatch). Silencing that specific logger keeps our output
# clean without touching anything functional.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

_client = chromadb.PersistentClient(
    path=CHROMA_DIR, settings=ChromaSettings(anonymized_telemetry=False)
)
_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)


def get_collection():
    return _client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=_embedding_function
    )


def build_product_index() -> None:
    """Embed every product in the database and store it in Chroma.

    Uses upsert, so re-running this after products change just
    overwrites the existing entries instead of duplicating them.
    """
    collection = get_collection()
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            print("No products found in the database -- run app.seed first.")
            return

        collection.upsert(
            ids=[str(p.id) for p in products],
            documents=[f"{p.name}. {p.description}" for p in products],
            metadatas=[
                {"name": p.name, "category": p.category, "price": p.price} for p in products
            ],
        )
        print(f"Indexed {len(products)} products into Chroma.")
    finally:
        db.close()


def search_products(query: str, n_results: int = 5) -> dict:
    """Return the top semantic matches for a free-text query."""
    collection = get_collection()
    return collection.query(query_texts=[query], n_results=n_results)


if __name__ == "__main__":
    build_product_index()
