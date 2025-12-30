from flask import Blueprint, render_template, request, redirect, url_for
from services.cart_service import (
    get_cart, totals, add_item, inc, remove_item, clear_cart
)

cart_bp = Blueprint("cart", __name__)

@cart_bp.get("/carrito")
def cart_page():
    cart = get_cart()
    t = totals()
    return render_template("cart.html", cart=cart, totals=t)

@cart_bp.post("/carrito/add")
def cart_add():
    product_id = request.form.get("product_id", "")
    name = request.form.get("name", "")
    unit_price = request.form.get("unit_price", "0")
    image_url = request.form.get("image_url", "")
    qty = request.form.get("qty", "1")

    if not product_id or not name:
        return redirect(url_for("cart.cart_page"))

    add_item(
        product_id=product_id,
        name=name,
        unit_price=float(unit_price),
        image_url=image_url,
        qty=int(qty)
    )
    return redirect(url_for("cart.cart_page"))

@cart_bp.post("/carrito/update")
def cart_update():
    product_id = request.form.get("product_id", "")
    action = request.form.get("action", "")  # plus / minus

    if product_id and action == "plus":
        inc(product_id, +1)
    elif product_id and action == "minus":
        inc(product_id, -1)

    return redirect(url_for("cart.cart_page"))

@cart_bp.post("/carrito/remove")
def cart_remove():
    product_id = request.form.get("product_id", "")
    if product_id:
        remove_item(product_id)
    return redirect(url_for("cart.cart_page"))

@cart_bp.post("/carrito/clear")
def cart_clear():
    clear_cart()
    return redirect(url_for("cart.cart_page"))

@cart_bp.post("/carrito/agregar")
def carrito_agregar():
    product_id = request.form.get("product_id", "")
    name = request.form.get("name", "")
    unit_price = request.form.get("unit_price", "0")
    image_url = request.form.get("image_url", "")
    qty = request.form.get("qty", "1")

    if not product_id or not name:
        return redirect("/catalogo")

    add_item(product_id, name, float(unit_price), image_url, int(qty))
    return redirect("/carrito")
