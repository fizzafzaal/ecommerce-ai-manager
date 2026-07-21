"""Generate mock data with Faker and insert it into the database.

Run once from the project root (venv activated):
    python -m app.seed
Re-run with --force to wipe existing data and reseed from scratch.
"""

import argparse
import random
from datetime import datetime, timedelta

from faker import Faker

from app.database import Base, SessionLocal, engine
from app.models import Conversation, Customer, Inventory, Message, Order, Product, Refund

fake = Faker()

NUM_CUSTOMERS = 15
NUM_ORDERS = 25
NUM_REFUNDS = 8

# Curated product catalog (not random Faker words) so the Product Agent's
# semantic search later has real names/descriptions worth embedding.
PRODUCTS = [
    # Clothing
    {"name": "Men's Warm Puffer Jacket", "description": "Insulated winter jacket with water-resistant shell, ideal for cold weather.", "category": "Clothing", "price": 89.99},
    {"name": "Women's Fleece-Lined Winter Coat", "description": "Long fleece-lined coat that keeps you warm in freezing temperatures.", "category": "Clothing", "price": 109.99},
    {"name": "Unisex Wool Beanie", "description": "Soft wool beanie for extra warmth on cold days.", "category": "Clothing", "price": 14.99},
    {"name": "Men's Slim Fit Jeans", "description": "Classic slim fit denim jeans, machine washable.", "category": "Clothing", "price": 39.99},
    {"name": "Women's Summer Floral Dress", "description": "Lightweight floral dress, perfect for warm summer days.", "category": "Clothing", "price": 34.99},
    {"name": "Men's Cotton T-Shirt (3-Pack)", "description": "Breathable cotton t-shirts in classic colors.", "category": "Clothing", "price": 19.99},
    {"name": "Waterproof Rain Jacket", "description": "Lightweight waterproof jacket, packable for travel.", "category": "Clothing", "price": 59.99},
    {"name": "Thermal Base Layer Set", "description": "Moisture-wicking thermal top and bottom for cold outdoor activities.", "category": "Clothing", "price": 44.99},
    # Electronics
    {"name": "Wireless Bluetooth Headphones", "description": "Over-ear noise-cancelling headphones with 30-hour battery life.", "category": "Electronics", "price": 79.99},
    {"name": "Smartphone Fast Charger (USB-C)", "description": "25W fast charging adapter compatible with most modern phones.", "category": "Electronics", "price": 17.99},
    {"name": "Portable Bluetooth Speaker", "description": "Compact waterproof speaker with deep bass and 12-hour battery.", "category": "Electronics", "price": 45.99},
    {"name": "4K Webcam", "description": "USB webcam with autofocus, ideal for video calls and streaming.", "category": "Electronics", "price": 54.99},
    {"name": "Mechanical Gaming Keyboard", "description": "RGB backlit mechanical keyboard with tactile switches.", "category": "Electronics", "price": 69.99},
    {"name": "Wireless Ergonomic Mouse", "description": "Comfortable wireless mouse with adjustable DPI settings.", "category": "Electronics", "price": 24.99},
    {"name": "Smartwatch Fitness Tracker", "description": "Tracks steps, heart rate, and sleep with a 7-day battery life.", "category": "Electronics", "price": 99.99},
    {"name": "Portable Power Bank 20000mAh", "description": "High-capacity power bank with dual USB output ports.", "category": "Electronics", "price": 29.99},
    # Home & Kitchen
    {"name": "Stainless Steel Electric Kettle", "description": "1.7L kettle with auto shut-off and boil-dry protection.", "category": "Home & Kitchen", "price": 32.99},
    {"name": "Non-Stick Frying Pan Set", "description": "3-piece non-stick frying pan set, dishwasher safe.", "category": "Home & Kitchen", "price": 42.99},
    {"name": "Memory Foam Pillow", "description": "Contour memory foam pillow for neck and shoulder support.", "category": "Home & Kitchen", "price": 27.99},
    {"name": "Cozy Fleece Throw Blanket", "description": "Extra-warm fleece blanket, machine washable, great for winter nights.", "category": "Home & Kitchen", "price": 22.99},
    {"name": "Ceramic Coffee Mug Set (4-Pack)", "description": "Set of 4 ceramic mugs, microwave and dishwasher safe.", "category": "Home & Kitchen", "price": 19.99},
    {"name": "Robot Vacuum Cleaner", "description": "Automatic robot vacuum with smart navigation and app control.", "category": "Home & Kitchen", "price": 179.99},
    {"name": "Air Fryer 5.5L", "description": "Large capacity air fryer for healthier oil-free cooking.", "category": "Home & Kitchen", "price": 74.99},
    {"name": "Digital Kitchen Scale", "description": "Precise digital scale for baking and cooking measurements.", "category": "Home & Kitchen", "price": 15.99},
    # Sports & Outdoors
    {"name": "Yoga Mat with Carrying Strap", "description": "Non-slip yoga mat, extra thick for comfort.", "category": "Sports & Outdoors", "price": 24.99},
    {"name": "Adjustable Dumbbell Set", "description": "Space-saving adjustable dumbbells, 5 to 25 lbs per hand.", "category": "Sports & Outdoors", "price": 129.99},
    {"name": "Insulated Water Bottle", "description": "Keeps drinks cold for 24 hours or hot for 12 hours.", "category": "Sports & Outdoors", "price": 18.99},
    {"name": "Camping Tent (2-Person)", "description": "Waterproof lightweight tent, easy to set up for camping trips.", "category": "Sports & Outdoors", "price": 89.99},
    {"name": "Hiking Backpack 40L", "description": "Durable hiking backpack with multiple compartments and rain cover.", "category": "Sports & Outdoors", "price": 64.99},
    {"name": "Resistance Bands Set", "description": "5 resistance bands of varying strength for home workouts.", "category": "Sports & Outdoors", "price": 16.99},
    {"name": "Running Shoes", "description": "Lightweight breathable running shoes with cushioned sole.", "category": "Sports & Outdoors", "price": 79.99},
    {"name": "Winter Ski Gloves", "description": "Waterproof insulated gloves for skiing and cold outdoor activities.", "category": "Sports & Outdoors", "price": 29.99},
    # Beauty & Personal Care
    {"name": "Electric Toothbrush", "description": "Rechargeable toothbrush with 3 cleaning modes.", "category": "Beauty & Personal Care", "price": 34.99},
    {"name": "Hair Dryer with Diffuser", "description": "Fast-drying hair dryer with multiple heat settings.", "category": "Beauty & Personal Care", "price": 39.99},
    {"name": "Facial Cleansing Brush", "description": "Silicone facial brush for gentle daily cleansing.", "category": "Beauty & Personal Care", "price": 21.99},
    {"name": "Moisturizing Face Cream", "description": "Daily face cream with SPF for hydrated, protected skin.", "category": "Beauty & Personal Care", "price": 16.99},
    {"name": "Nail Care Kit", "description": "Complete manicure and pedicure kit with case.", "category": "Beauty & Personal Care", "price": 12.99},
    {"name": "Electric Shaver", "description": "Cordless rechargeable shaver for a smooth, close shave.", "category": "Beauty & Personal Care", "price": 44.99},
    {"name": "Aromatherapy Essential Oil Set", "description": "6 essential oils for relaxation and diffuser use.", "category": "Beauty & Personal Care", "price": 23.99},
    {"name": "Bluetooth Hair Straightener Brush", "description": "Ceramic straightening brush for smooth, frizz-free hair.", "category": "Beauty & Personal Care", "price": 27.99},
]


def seed_customers(db):
    customers = []
    for _ in range(NUM_CUSTOMERS):
        customer = Customer(name=fake.name(), email=fake.unique.email())
        db.add(customer)
        customers.append(customer)
    db.flush()  # assigns IDs without committing yet
    return customers


def seed_products_and_inventory(db):
    products = []
    for item in PRODUCTS:
        product = Product(
            name=item["name"],
            description=item["description"],
            category=item["category"],
            price=item["price"],
        )
        db.add(product)
        products.append(product)
    db.flush()

    for product in products:
        # ~20% of products deliberately land under 5 units so the Product
        # Agent's low-stock flag (<5) has real cases to catch, without
        # making low stock the norm.
        if random.random() < 0.2:
            stock = random.randint(0, 4)
        else:
            stock = random.randint(5, 60)
        db.add(Inventory(product_id=product.id, stock_quantity=stock))

    return products


def seed_orders(db, customers, products):
    orders = []
    for _ in range(NUM_ORDERS):
        customer = random.choice(customers)
        product = random.choice(products)
        quantity = random.randint(1, 3)
        # Spread order dates over the last 60 days so some orders fall
        # outside the refund policy's 30-day window and some don't.
        days_ago = random.randint(0, 60)
        order = Order(
            customer_id=customer.id,
            product_id=product.id,
            quantity=quantity,
            total_amount=round(product.price * quantity, 2),
            status="completed",
            order_date=datetime.utcnow() - timedelta(days=days_ago),
        )
        db.add(order)
        orders.append(order)
    db.flush()
    return orders


def seed_refunds(db, orders):
    # Only orders within 30 days are realistic candidates for an already-
    # approved refund; older ones would violate the eligibility rule the
    # Refund Agent enforces.
    eligible_orders = [o for o in orders if (datetime.utcnow() - o.order_date).days <= 30]
    sample_size = min(NUM_REFUNDS, len(eligible_orders))
    chosen_orders = random.sample(eligible_orders, sample_size)

    for order in chosen_orders:
        db.add(
            Refund(
                order_id=order.id,
                reason=fake.sentence(nb_words=8),
                status="approved",
                refund_date=order.order_date + timedelta(days=random.randint(1, 5)),
            )
        )
        order.status = "refunded"


def already_seeded(db) -> bool:
    return db.query(Customer).first() is not None


def run_seed(force: bool = False):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if already_seeded(db) and not force:
            print("Database already has data. Re-run with --force to wipe and reseed.")
            return

        if force:
            for model in (Message, Conversation, Refund, Order, Inventory, Product, Customer):
                db.query(model).delete()
            db.commit()

        customers = seed_customers(db)
        products = seed_products_and_inventory(db)
        orders = seed_orders(db, customers, products)
        seed_refunds(db, orders)
        db.commit()

        print(
            f"Seeded {len(customers)} customers, {len(products)} products, "
            f"{len(orders)} orders, {NUM_REFUNDS} refunds."
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with mock data.")
    parser.add_argument("--force", action="store_true", help="Wipe existing data before seeding.")
    args = parser.parse_args()
    run_seed(force=args.force)
