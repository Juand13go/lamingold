from flask import Blueprint, render_template, redirect, session, flash, request
from services.product_service import list_products, create_product, get_product, delete_product_cascade
from services.order_service import list_orders, get_order_items, update_order_status

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def is_admin() -> bool:
    user = session.get("user") or {}
    return (user.get("role") or "").strip().lower() == "admin"


def require_admin():
    if not session.get("user"):
        flash("Debes iniciar sesion.", "error")
        return redirect("/login")
    if not is_admin():
        flash("No tienes permisos de administrador.", "error")
        return redirect("/catalogo")
    return None


@admin_bp.get("/")
def dashboard():
    guard = require_admin()
    if guard:
        return guard
    return render_template("admin/dashboard.html")


@admin_bp.get("/products")
def admin_products():
    guard = require_admin()
    if guard:
        return guard

    products = list_products()
    return render_template("admin/products.html", products=products)


@admin_bp.get("/products/new")
def admin_product_new():
    guard = require_admin()
    if guard:
        return guard
    return render_template("admin/product_form.html")


@admin_bp.post("/products/new")
def admin_product_create():
    guard = require_admin()
    if guard:
        return guard

    name = request.form.get("name") or ""
    base_price_raw = request.form.get("base_price") or ""
    category = request.form.get("category") or ""
    description = request.form.get("description") or ""
    color = request.form.get("color") or "Dorado"
    gold_type = request.form.get("gold_type") or "18k"
    is_active = True if request.form.get("is_active") == "on" else False

    try:
        base_price = float(base_price_raw)  # double
    except Exception:
        flash("Precio invalido. Debe ser un numero.", "error")
        return redirect("/admin/products/new")

    try:
        # 1) Crear producto
        product_doc = create_product(
            name=name,
            base_price=base_price,
            category=category,
            description=description,
            color=color,
            gold_type=gold_type,
            is_active=is_active
        )

        product_id = product_doc.get("$id")

        # 2) Imagen obligatoria (si no viene -> rollback)
        image_file = request.files.get("image_file")
        if not image_file or not image_file.filename:
            from services.product_service import delete_product
            delete_product(product_id)
            flash("La imagen es obligatoria. Producto no fue creado.", "error")
            return redirect("/admin/products/new")

        # 3) Subir imagen + linkear
        from services.product_images_service import upload_and_link_product_image
        upload_and_link_product_image(product_id, image_file)

        flash("Producto creado con imagen.", "success")
        return redirect("/admin/products")

    except Exception as e:
        flash(f"No se pudo crear el producto: {str(e)}", "error")
        return redirect("/admin/products/new")




@admin_bp.get("/orders")
def admin_orders():
    guard = require_admin()
    if guard:
        return guard

    orders = list_orders(limit=50)
    return render_template("admin/orders.html", orders=orders)


@admin_bp.get("/orders/<order_id>")
def admin_order_detail(order_id):
    guard = require_admin()
    if guard:
        return guard

    orders = list_orders(limit=200)
    order = None
    for o in orders:
        if (o.get("$id") or "") == order_id:
            order = o
            break

    if not order:
        flash("Pedido no encontrado.", "error")
        return redirect("/admin/orders")

    items = get_order_items(order_id)

    # ✅ Adjuntar imagen a cada item (usando product_id -> get_product -> image_url)
    from services.product_service import get_product

    total = 0
    for it in items:
        # total
        try:
            total += float(it.get("subtotal") or 0)
        except:
            pass

        # imagen
        pid = (it.get("product_id") or "").strip()
        if pid:
            p = get_product(pid)
            it["image_url"] = (p.get("image_url") or "").strip()
        else:
            it["image_url"] = ""

    return render_template(
        "admin/order_detail.html",
        order=order,
        items=items,
        total=int(total)
    )

@admin_bp.post("/orders/<order_id>/status")
def admin_order_status(order_id):
    guard = require_admin()
    if guard:
        return guard

    status = request.form.get("status") or ""
    try:
        update_order_status(order_id, status)
        flash("Estado actualizado.", "success")
    except Exception as e:
        flash(f"No se pudo actualizar: {str(e)}", "error")

    return redirect(f"/admin/orders/{order_id}")

@admin_bp.post("/products/<product_id>/delete")
def admin_product_delete(product_id):
    guard = require_admin()
    if guard:
        return guard

    try:
        delete_product_cascade(product_id)
        flash("Producto eliminado.", "success")
    except Exception as e:
        flash(f"No se pudo eliminar el producto: {str(e)}", "error")

    return redirect("/admin/products")
