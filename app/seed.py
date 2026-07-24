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
from app.models import (
    CartItem,
    Conversation,
    Customer,
    Inventory,
    Message,
    Order,
    OrderItem,
    Product,
    Refund,
)

fake = Faker()

NUM_CUSTOMERS = 15
NUM_ORDERS = 25
NUM_REFUNDS = 8

# Curated product catalog (not random Faker words) so the Product Agent's
# semantic search later has real names/descriptions worth embedding.
# Each product carries an `img` keyword used to build a stock-photo URL
# (see seed_products_and_inventory) so the storefront shows realistic
# images. The frontend falls back to an emoji tile if an image fails.
PRODUCTS = [
    # Clothing
    {"name": "Men's Warm Puffer Jacket", "description": "Insulated winter jacket with water-resistant shell, ideal for cold weather.", "category": "Clothing", "price": 89.99, "img": "jacket"},
    {"name": "Women's Fleece-Lined Winter Coat", "description": "Long fleece-lined coat that keeps you warm in freezing temperatures.", "category": "Clothing", "price": 109.99, "img": "coat"},
    {"name": "Unisex Wool Beanie", "description": "Soft wool beanie for extra warmth on cold days.", "category": "Clothing", "price": 14.99, "img": "beanie"},
    {"name": "Men's Slim Fit Jeans", "description": "Classic slim fit denim jeans, machine washable.", "category": "Clothing", "price": 39.99, "img": "jeans"},
    {"name": "Women's Summer Floral Dress", "description": "Lightweight floral dress, perfect for warm summer days.", "category": "Clothing", "price": 34.99, "img": "dress"},
    {"name": "Men's Cotton T-Shirt (3-Pack)", "description": "Breathable cotton t-shirts in classic colors.", "category": "Clothing", "price": 19.99, "img": "tshirt"},
    {"name": "Waterproof Rain Jacket", "description": "Lightweight waterproof jacket, packable for travel.", "category": "Clothing", "price": 59.99, "img": "raincoat"},
    {"name": "Thermal Base Layer Set", "description": "Moisture-wicking thermal top and bottom for cold outdoor activities.", "category": "Clothing", "price": 44.99, "img": "activewear"},
    # Electronics
    {"name": "Wireless Bluetooth Headphones", "description": "Over-ear noise-cancelling headphones with 30-hour battery life.", "category": "Electronics", "price": 79.99, "img": "headphones"},
    {"name": "Smartphone Fast Charger (USB-C)", "description": "25W fast charging adapter compatible with most modern phones.", "category": "Electronics", "price": 17.99, "img": "charger"},
    {"name": "Portable Bluetooth Speaker", "description": "Compact waterproof speaker with deep bass and 12-hour battery.", "category": "Electronics", "price": 45.99, "img": "speaker"},
    {"name": "4K Webcam", "description": "USB webcam with autofocus, ideal for video calls and streaming.", "category": "Electronics", "price": 54.99, "img": "webcam"},
    {"name": "Mechanical Gaming Keyboard", "description": "RGB backlit mechanical keyboard with tactile switches.", "category": "Electronics", "price": 69.99, "img": "keyboard"},
    {"name": "Wireless Ergonomic Mouse", "description": "Comfortable wireless mouse with adjustable DPI settings.", "category": "Electronics", "price": 24.99, "img": "mouse"},
    {"name": "Smartwatch Fitness Tracker", "description": "Tracks steps, heart rate, and sleep with a 7-day battery life.", "category": "Electronics", "price": 99.99, "img": "smartwatch"},
    {"name": "Portable Power Bank 20000mAh", "description": "High-capacity power bank with dual USB output ports.", "category": "Electronics", "price": 29.99, "img": "powerbank"},
    # Home & Kitchen
    {"name": "Stainless Steel Electric Kettle", "description": "1.7L kettle with auto shut-off and boil-dry protection.", "category": "Home & Kitchen", "price": 32.99, "img": "kettle"},
    {"name": "Non-Stick Frying Pan Set", "description": "3-piece non-stick frying pan set, dishwasher safe.", "category": "Home & Kitchen", "price": 42.99, "img": "cookware"},
    {"name": "Memory Foam Pillow", "description": "Contour memory foam pillow for neck and shoulder support.", "category": "Home & Kitchen", "price": 27.99, "img": "pillow"},
    {"name": "Cozy Fleece Throw Blanket", "description": "Extra-warm fleece blanket, machine washable, great for winter nights.", "category": "Home & Kitchen", "price": 22.99, "img": "blanket"},
    {"name": "Ceramic Coffee Mug Set (4-Pack)", "description": "Set of 4 ceramic mugs, microwave and dishwasher safe.", "category": "Home & Kitchen", "price": 19.99, "img": "mug"},
    {"name": "Robot Vacuum Cleaner", "description": "Automatic robot vacuum with smart navigation and app control.", "category": "Home & Kitchen", "price": 179.99, "img": "vacuum"},
    {"name": "Air Fryer 5.5L", "description": "Large capacity air fryer for healthier oil-free cooking.", "category": "Home & Kitchen", "price": 74.99, "img": "fryer"},
    {"name": "Digital Kitchen Scale", "description": "Precise digital scale for baking and cooking measurements.", "category": "Home & Kitchen", "price": 15.99, "img": "scale"},
    # Sports & Outdoors
    {"name": "Yoga Mat with Carrying Strap", "description": "Non-slip yoga mat, extra thick for comfort.", "category": "Sports & Outdoors", "price": 24.99, "img": "yoga"},
    {"name": "Adjustable Dumbbell Set", "description": "Space-saving adjustable dumbbells, 5 to 25 lbs per hand.", "category": "Sports & Outdoors", "price": 129.99, "img": "dumbbell"},
    {"name": "Insulated Water Bottle", "description": "Keeps drinks cold for 24 hours or hot for 12 hours.", "category": "Sports & Outdoors", "price": 18.99, "img": "waterbottle"},
    {"name": "Camping Tent (2-Person)", "description": "Waterproof lightweight tent, easy to set up for camping trips.", "category": "Sports & Outdoors", "price": 89.99, "img": "tent"},
    {"name": "Hiking Backpack 40L", "description": "Durable hiking backpack with multiple compartments and rain cover.", "category": "Sports & Outdoors", "price": 64.99, "img": "backpack"},
    {"name": "Resistance Bands Set", "description": "5 resistance bands of varying strength for home workouts.", "category": "Sports & Outdoors", "price": 16.99, "img": "fitness"},
    {"name": "Running Shoes", "description": "Lightweight breathable running shoes with cushioned sole.", "category": "Sports & Outdoors", "price": 79.99, "img": "sneakers"},
    {"name": "Winter Ski Gloves", "description": "Waterproof insulated gloves for skiing and cold outdoor activities.", "category": "Sports & Outdoors", "price": 29.99, "img": "gloves"},
    # Beauty & Personal Care
    {"name": "Electric Toothbrush", "description": "Rechargeable toothbrush with 3 cleaning modes.", "category": "Beauty & Personal Care", "price": 34.99, "img": "toothbrush"},
    {"name": "Hair Dryer with Diffuser", "description": "Fast-drying hair dryer with multiple heat settings.", "category": "Beauty & Personal Care", "price": 39.99, "img": "hairdryer"},
    {"name": "Facial Cleansing Brush", "description": "Silicone facial brush for gentle daily cleansing.", "category": "Beauty & Personal Care", "price": 21.99, "img": "skincare"},
    {"name": "Moisturizing Face Cream", "description": "Daily face cream with SPF for hydrated, protected skin.", "category": "Beauty & Personal Care", "price": 16.99, "img": "cosmetics"},
    {"name": "Nail Care Kit", "description": "Complete manicure and pedicure kit with case.", "category": "Beauty & Personal Care", "price": 12.99, "img": "manicure"},
    {"name": "Electric Shaver", "description": "Cordless rechargeable shaver for a smooth, close shave.", "category": "Beauty & Personal Care", "price": 44.99, "img": "razor"},
    {"name": "Aromatherapy Essential Oil Set", "description": "6 essential oils for relaxation and diffuser use.", "category": "Beauty & Personal Care", "price": 23.99, "img": "aromatherapy"},
    {"name": "Bluetooth Hair Straightener Brush", "description": "Ceramic straightening brush for smooth, frizz-free hair.", "category": "Beauty & Personal Care", "price": 27.99, "img": "haircare"},
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
    for i, item in enumerate(PRODUCTS, start=1):
        # Product photos are committed under storefront/public/products/,
        # named by product id, and served locally by the frontend (reliable
        # and offline-friendly). The frontend falls back to an emoji tile if
        # an image is ever missing.
        image_url = f"/products/{i}.jpg"
        product = Product(
            name=item["name"],
            description=item["description"],
            category=item["category"],
            price=item["price"],
            image_url=image_url,
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
    for i in range(NUM_ORDERS):
        customer = random.choice(customers)
        # Deterministic split so we always have both buckets for demos:
        # the first ~60% of orders fall inside the 30-day refund window
        # (eligible), the rest fall outside it (rejected as out-of-window).
        if i < int(NUM_ORDERS * 0.6):
            days_ago = random.randint(1, 28)
        else:
            days_ago = random.randint(31, 60)

        # Most orders are single-item; some have two distinct products, so
        # the new multi-item order model has real examples to show.
        line_products = random.sample(products, random.randint(1, 2))
        items = [
            OrderItem(
                product_id=p.id,
                quantity=random.randint(1, 3),
                unit_price=p.price,
            )
            for p in line_products
        ]
        total = round(sum(item.unit_price * item.quantity for item in items), 2)

        order = Order(
            customer_id=customer.id,
            total_amount=total,
            status="completed",
            order_date=datetime.utcnow() - timedelta(days=days_ago),
            items=items,
        )
        db.add(order)
        orders.append(order)
    db.flush()
    return orders


ELIGIBLE_BUFFER = 5  # eligible orders left un-refunded, for live refund demos


def seed_refunds(db, orders):
    # Only orders within 30 days are realistic candidates for an already-
    # approved refund; older ones would violate the eligibility rule the
    # Refund Agent enforces.
    eligible_orders = [o for o in orders if (datetime.utcnow() - o.order_date).days <= 30]
    # Leave a buffer of eligible orders un-refunded so a live demo always
    # has completed, in-window orders that will actually get approved --
    # otherwise refunds would consume every eligible order and every demo
    # refund would be rejected as already-refunded or out-of-window.
    refundable = max(0, len(eligible_orders) - ELIGIBLE_BUFFER)
    sample_size = min(NUM_REFUNDS, refundable)
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

    return len(chosen_orders)


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
            # Delete child tables before their parents to respect foreign keys.
            for model in (
                Message,
                Conversation,
                Refund,
                OrderItem,
                Order,
                CartItem,
                Inventory,
                Product,
                Customer,
            ):
                db.query(model).delete()
            db.commit()

        customers = seed_customers(db)
        products = seed_products_and_inventory(db)
        orders = seed_orders(db, customers, products)
        num_refunds = seed_refunds(db, orders)
        db.commit()

        print(
            f"Seeded {len(customers)} customers, {len(products)} products, "
            f"{len(orders)} orders, {num_refunds} refunds."
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with mock data.")
    parser.add_argument("--force", action="store_true", help="Wipe existing data before seeding.")
    args = parser.parse_args()
    run_seed(force=args.force)
