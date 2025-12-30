# from flask import Blueprint, render_template
# from services.product_service import list_categories, list_products_by_category

# pages_bp = Blueprint("pages", __name__)

# @pages_bp.get("/")
# def home():
#     categories = list_categories()

#     products_by_cat = {}
#     for c in categories:
#         # preview: mostramos max 6 por categoria
#         products_by_cat[c] = list_products_by_category(c)[:6]

#     return render_template("home.html", categories=categories, products_by_cat=products_by_cat)


# @pages_bp.get("/categoria/<slug>")
# def category_page(slug):
#     # slug tipo: "oro-laminado" -> "oro laminado"
#     category = slug.replace("-", " ").strip().lower()

#     products = list_products_by_category(category)

#     # Para mostrar bonito el titulo
#     title = category.title()

#     return render_template("category.html", category=title, products=products)
