from flask import Blueprint, render_template
from services.product_service import (
    list_products,
    list_categories,
    list_products_by_category,
    get_product,
)

shop_bp = Blueprint("shop", __name__)

# Categorias fijas (MVP). El admin NO las toca.
# slug debe coincidir con lo que guardas en products.category (ej: "pulseras")
CATEGORIES = [
    {
        "slug": "pulseras",
        "label": "Pulseras",
        "title": "Pulseras en oro laminado",
        "desc": "Estilo premium para el dia a dia."
    },
    {
        "slug": "cadenas",
        "label": "Cadenas",
        "title": "Cadenas y collares",
        "desc": "Piezas elegantes para cualquier ocasion."
    },
    {
        "slug": "anillos",
        "label": "Anillos",
        "title": "Anillos",
        "desc": "Detalles finos, brillo y presencia."
    },
    {
        "slug": "aretes",
        "label": "Aretes",
        "title": "Aretes",
        "desc": "Minimalistas o llamativos, tu eliges."
    }
]


@shop_bp.get("/")
def home():
    # Para la home: mostramos las categorias existentes (si Appwrite aun esta vacio, igual funciona)
    categories = list_categories()

    # Preview: max 6 productos por categoria
    products_by_cat = {}
    for c in categories:
        products_by_cat[c] = (list_products_by_category(c) or [])[:6]

    return render_template(
        "home.html",
        categories=categories,
        products_by_cat=products_by_cat
    )


@shop_bp.get("/catalogo")
def catalogo():
    products = list_products()
    return render_template("catalog.html", products=products)


@shop_bp.get("/categoria/<slug>")
def category(slug):
    slug = (slug or "").strip().lower()

    # Validamos que exista dentro de nuestras categorias del MVP
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return render_template(
            "category.html",
            category_title="Categoria no encontrada",
            category_desc="Esa categoria no existe por ahora.",
            products=[]
        ), 404

    # Pedimos productos directamente por categoria (mas limpio que listar todo y filtrar)
    products = list_products_by_category(slug) or []

    return render_template(
        "category.html",
        category_title=cat["title"],
        category_desc=cat["desc"],
        products=products
    )


@shop_bp.get("/producto/<product_id>")
def producto_detalle(product_id):
    product_id = (product_id or "").strip()
    product = get_product(product_id)
    return render_template("product_detail.html", product=product)
