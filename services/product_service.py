import requests
from config import config
from models.constants import TABLE_PRODUCTS, TABLE_PRODUCT_IMAGES
import re

def build_image_url(file_id: str) -> str:
    file_id = (file_id or "").strip()
    if not file_id:
        return ""

    bucket_id = (config.APPWRITE_BUCKET_PRODUCT_IMAGES or "").strip()
    if not bucket_id:
        return ""

    endpoint = (config.APPWRITE_ENDPOINT or "").rstrip("/")
    project = (config.APPWRITE_PROJECT_ID or "").strip()

    # "view" funciona si el bucket/archivo tiene permisos de lectura pública
    return f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/view?project={project}"


# MOCK temporal (pero ya en el formato FINAL del proyecto):
# image_url apunta a /static/img/products/...
# category usa slugs para que /categoria/<slug> filtre bien
MOCK_PRODUCTS = [
    {
        "$id": "p1",
        "name": "Pulsera Oro Laminado Clasica",
        "base_price": 35000,
        "image_url": "/static/img/products/pulsera_1.jpg",
        "description": "Acabado elegante, comoda y resistente.",
        "category": "pulseras",
        "color": "Dorado",
        "gold_type": "18k",
        "slug": "pulsera-oro-laminado-clasica",
    },
    {
        "$id": "p2",
        "name": "Cadena Premium",
        "base_price": 42000,
        "image_url": "/static/img/products/cadena_1.jpg",
        "description": "Estilo sobrio y moderno.",
        "category": "cadenas",
        "color": "Dorado",
        "gold_type": "18k",
        "slug": "cadena-premium",
    },
    {
        "$id": "p3",
        "name": "Anillo Brillo",
        "base_price": 63000,
        "image_url": "/static/img/products/anillo_1.jpg",
        "description": "Para destacar, full brillo.",
        "category": "anillos",
        "color": "Dorado",
        "gold_type": "18k",
        "slug": "anillo-brillo",
    },
    {
        "$id": "p4",
        "name": "Aretes Minimal",
        "base_price": 28000,
        "image_url": "/static/img/products/aretes_1.jpg",
        "description": "Minimalistas y elegantes.",
        "category": "aretes",
        "color": "Dorado",
        "gold_type": "18k",
        "slug": "aretes-minimal",
    },
]


def _headers():
    return {
        "X-Appwrite-Project": config.APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": config.APPWRITE_API_KEY,
        "Content-Type": "application/json",
    }


def _base():
    return config.APPWRITE_ENDPOINT.rstrip("/")


def _collection_base(collection_id: str) -> str:
    return f"{_base()}/databases/{config.APPWRITE_DATABASE_ID}/collections/{collection_id}/documents"


def _list_all_documents(collection_id: str, limit: int = 100):
    """
    Trae TODOS los documentos de una collection usando paginación (offset/limit).
    """
    all_docs = []
    offset = 0

    while True:
        url = _collection_base(collection_id)
        params = {"limit": limit, "offset": offset}

        r = requests.get(url, headers=_headers(), params=params, timeout=20)
        if r.status_code >= 400:
            raise RuntimeError(r.text)

        data = r.json()
        docs = data.get("documents", []) or []
        total = data.get("total", len(docs))

        all_docs.extend(docs)

        offset += len(docs)
        if offset >= total or not docs:
            break

    return all_docs


def _product_images_map():
    """
    Devuelve dict: { product_id: file_id }
    Si un producto tiene varias imágenes, usamos la primera que encontremos.
    """
    docs = _list_all_documents(TABLE_PRODUCT_IMAGES, limit=100)

    mapping = {}
    for d in docs:
        pid = (d.get("product_id") or "").strip()
        fid = (d.get("file_id") or "").strip()
        if pid and fid and pid not in mapping:
            mapping[pid] = fid

    return mapping


def _normalize_product(doc: dict, image_file_id: str = "") -> dict:
    image_file_id = (image_file_id or "").strip()

    # si el producto ya trae image_url por algun motivo, se respeta
    image_url = (doc.get("image_url") or doc.get("image") or "").strip()

    # si no hay url y tenemos file_id, construimos url
    if not image_url and image_file_id:
        image_url = build_image_url(image_file_id)

    return {
        "$id": doc.get("$id") or doc.get("id") or "",
        "name": doc.get("name", "Producto"),
        "base_price": doc.get("base_price", doc.get("price", 0)) or 0,
        "image_url": image_url,
        "description": doc.get("description", "") or "",
        "category": doc.get("category", "") or "",
        "color": doc.get("color", "Dorado") or "Dorado",
        "gold_type": doc.get("gold_type", "18k") or "18k",
        "slug": doc.get("slug", "") or "",
    }


def list_products():
    """
    Lista productos desde Appwrite.
    Además, une products + product_images para construir image_url.
    Si falla cualquier cosa, retorna MOCK_PRODUCTS.
    """
    try:
        # 1) Traer TODOS los productos
        docs = _list_all_documents(TABLE_PRODUCTS, limit=100)

        # si Appwrite no tiene nada, mock
        if not docs:
            return []

        # 2) Traer mapa product_id -> file_id (desde product_images)
        images_map = _product_images_map()

        # 3) Normalizar, inyectando file_id desde el mapa
        products = []
        for d in docs:
            pid = d.get("$id") or d.get("id") or ""
            file_id = images_map.get(pid, "")
            products.append(_normalize_product(d, image_file_id=file_id))

        return products

    except Exception as e:
        print("ERROR list_products:", e)
        return []  # nada de mock en producción



def get_product(product_id: str):
    product_id = (product_id or "").strip()
    products = list_products()

    for p in products:
        if p.get("$id") == product_id:
            return p

    # fallback “no encontrado” (pero con formato correcto)
    return {
        "$id": product_id,
        "name": "Producto no encontrado",
        "base_price": 0,
        "image_url": "",
        "description": "",
        "category": "",
        "color": "Dorado",
        "gold_type": "18k",
        "slug": "",
    }


def list_products_by_category(category: str):
    category = (category or "").strip().lower()
    products = list_products()

    if not category:
        return products

    return [
        p for p in products
        if (p.get("category") or "").strip().lower() == category
    ]


def list_categories():
    products = list_products()
    categories = []

    for p in products:
        c = (p.get("category") or "").strip()
        if c and c not in categories:
            categories.append(c)

    categories.sort()
    return categories

def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def create_product(
    name: str,
    base_price: int,
    category: str,
    description: str = "",
    color: str = "Dorado",
    gold_type: str = "18k",
    # image_url: str = "",
    is_active: bool = True
):
    """
    Crea producto en Appwrite (TABLE_PRODUCTS).
    En MVP: image_url opcional (puede ser URL externa o vacio).
    """
    name = (name or "").strip()
    category = (category or "").strip().lower()
    description = (description or "").strip()
    color = (color or "Dorado").strip()
    gold_type = (gold_type or "18k").strip()
    # image_url = (image_url or "").strip()

    try:
        base_price = int(base_price)
    except:
        base_price = 0

    if not name or base_price <= 0 or not category:
        raise ValueError("Nombre, precio y categoria son obligatorios.")

    slug = _slugify(name)

    url = _collection_base(TABLE_PRODUCTS)
    payload = {
        "documentId": "unique()",
        "data": {
            "name": name,
            "base_price": base_price,
            "category": category,
            "description": description,
            "color": color,
            "gold_type": gold_type,
            "slug": slug,
            # "image_url": image_url,
            "is_active": bool(is_active)
        }
    }

    r = requests.post(url, headers=_headers(), json=payload, timeout=20)
    if r.status_code >= 400:
        print("APPWRITE ERROR create_product:", r.status_code, r.text)
        raise RuntimeError(r.text)
    return r.json()

def delete_product(product_id: str):
    product_id = (product_id or "").strip()
    if not product_id:
        raise ValueError("product_id requerido")

    url = f"{_collection_base(TABLE_PRODUCTS)}/{product_id}"
    r = requests.delete(url, headers=_headers(), timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(r.text)
    return True
