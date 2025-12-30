from flask import session

CART_KEY = "cart"  # dict: {product_id: {product_id,name,unit_price,quantity,image_url}}

def get_cart() -> dict:
    cart = session.get(CART_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[CART_KEY] = cart
    return cart

def save_cart(cart: dict):
    session[CART_KEY] = cart
    session.modified = True

def clear_cart():
    session[CART_KEY] = {}
    session.modified = True

def add_item(product_id: str, name: str, unit_price: float, image_url: str = "", qty: int = 1):
    cart = get_cart()
    if product_id not in cart:
        cart[product_id] = {
            "product_id": product_id,
            "name": name,
            "unit_price": float(unit_price),
            "quantity": int(qty),
            "image_url": image_url or ""
        }
    else:
        cart[product_id]["quantity"] = int(cart[product_id]["quantity"]) + int(qty)

    # evitar negativos/cero
    if cart[product_id]["quantity"] <= 0:
        cart.pop(product_id, None)

    save_cart(cart)

def set_quantity(product_id: str, quantity: int):
    cart = get_cart()
    if product_id in cart:
        q = int(quantity)
        if q <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id]["quantity"] = q
        save_cart(cart)

def inc(product_id: str, delta: int = 1):
    cart = get_cart()
    if product_id in cart:
        cart[product_id]["quantity"] = int(cart[product_id]["quantity"]) + int(delta)
        if cart[product_id]["quantity"] <= 0:
            cart.pop(product_id, None)
        save_cart(cart)

def remove_item(product_id: str):
    cart = get_cart()
    cart.pop(product_id, None)
    save_cart(cart)

def totals():
    cart = get_cart()
    subtotal = 0.0
    items_count = 0

    for _, item in cart.items():
        qty = int(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        subtotal += price * qty
        items_count += qty

    return {"subtotal": subtotal, "items_count": items_count}
