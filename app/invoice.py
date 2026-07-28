"""Generate a simple invoice image (PNG) for an order using Pillow.

The invoice is what a customer can download and later upload back for
verification. It shows the order number, date, customer, line items, and
total -- the fields the verification step reads and checks against the DB.
"""

import io

from PIL import Image, ImageDraw, ImageFont

BRAND = (79, 70, 229)  # indigo
DARK = (15, 23, 42)
MUTED = (100, 116, 139)
LINE = (226, 232, 240)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a common system font, falling back to Pillow's default."""
    candidates = (
        ["arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_invoice_png(*, order_id, date_str, customer_name, items, total) -> bytes:
    """Render an invoice PNG. `items` is a list of dicts with name, qty,
    unit_price, line_total."""
    width = 720
    top = 250  # header + meta + table header
    row_h = 36
    height = top + len(items) * row_h + 160

    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)

    # --- Header bar ---
    d.rectangle([0, 0, width, 90], fill=BRAND)
    d.text((32, 28), "ShopSphere", font=_font(32, bold=True), fill="white")
    d.text((width - 32, 34), "INVOICE", font=_font(24, bold=True), fill="white", anchor="ra")

    # --- Order meta ---
    d.text((32, 120), f"Invoice / Order #{order_id}", font=_font(20, bold=True), fill=DARK)
    d.text((32, 152), f"Date placed: {date_str}", font=_font(16), fill=MUTED)
    d.text((32, 176), f"Billed to: {customer_name}", font=_font(16), fill=MUTED)

    # --- Table header ---
    y = 224
    d.line([32, y - 8, width - 32, y - 8], fill=LINE, width=2)
    d.text((32, y), "Item", font=_font(14, bold=True), fill=MUTED)
    d.text((470, y), "Qty", font=_font(14, bold=True), fill=MUTED, anchor="ra")
    d.text((580, y), "Price", font=_font(14, bold=True), fill=MUTED, anchor="ra")
    d.text((688, y), "Total", font=_font(14, bold=True), fill=MUTED, anchor="ra")

    # --- Items ---
    y = top
    for it in items:
        d.text((32, y), str(it["name"])[:44], font=_font(15), fill=DARK)
        d.text((470, y), str(it["qty"]), font=_font(15), fill=DARK, anchor="ra")
        d.text((580, y), f"${it['unit_price']:.2f}", font=_font(15), fill=DARK, anchor="ra")
        d.text((688, y), f"${it['line_total']:.2f}", font=_font(15), fill=DARK, anchor="ra")
        y += row_h

    # --- Total ---
    d.line([32, y + 6, width - 32, y + 6], fill=LINE, width=2)
    d.text((470, y + 22), "TOTAL", font=_font(18, bold=True), fill=DARK)
    d.text((688, y + 20), f"${total:.2f}", font=_font(20, bold=True), fill=BRAND, anchor="ra")

    # --- Footer ---
    d.text(
        (width / 2, height - 40),
        "Thank you for shopping with ShopSphere!",
        font=_font(14),
        fill=MUTED,
        anchor="ma",
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
