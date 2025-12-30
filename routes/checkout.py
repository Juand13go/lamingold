from flask import Blueprint, render_template, request, redirect, session
from services.order_service import create_order_from_cart
from services.cart_service import totals, clear_cart, get_cart

checkout_bp = Blueprint("checkout", __name__)

@checkout_bp.get("/checkout")
def checkout_page():
    cart = get_cart()
    if not cart or len(cart) == 0:
        return redirect("/carrito")
    t = totals()
    return render_template("checkout.html", totals=t)

@checkout_bp.post("/checkout")
def checkout_submit():
    data = {
        "full_name": request.form.get("full_name", ""),
        "phone": request.form.get("phone", ""),
        "email": request.form.get("email", ""),
        "city": request.form.get("city", ""),
        "address": request.form.get("address", ""),
        "notes": request.form.get("notes", ""),
    }

    # ✅ PASAMOS session_user para no crear users duplicados si ya existe
    result = create_order_from_cart(data, session.get("user"))

    # vaciamos carrito al confirmar
    clear_cart()

    return render_template(
        "order_success.html",
        order_id=result["order_id"],
        wa_url=result["wa_url"]
    )
