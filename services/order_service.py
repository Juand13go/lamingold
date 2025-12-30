# services/order_service.py
import requests
from urllib.parse import quote
from config import config
from models.constants import TABLE_USERS, TABLE_ORDERS, TABLE_ORDER_ITEMS
from services.cart_service import get_cart, totals

WHATSAPP_NUMBER = "573160438565"  # 57 + numero negocio


def _headers():
    return {
        "X-Appwrite-Project": config.APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": config.APPWRITE_API_KEY,
        "Content-Type": "application/json",
    }


def _base():
    return (config.APPWRITE_ENDPOINT or "").rstrip("/")


def _collection_base(collection_id: str) -> str:
    return f"{_base()}/databases/{config.APPWRITE_DATABASE_ID}/collections/{collection_id}/documents"


def _create_document(collection_id: str, data: dict):
    url = _collection_base(collection_id)
    payload = {"documentId": "unique()", "data": data}

    r = requests.post(url, headers=_headers(), json=payload, timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(f"Appwrite create error {collection_id}: {r.status_code} {r.text}")
    return r.json()


def _update_document(collection_id: str, document_id: str, data: dict):
    document_id = (document_id or "").strip()
    if not document_id:
        raise ValueError("document_id requerido")

    url = f"{_collection_base(collection_id)}/{document_id}"
    payload = {"data": data}

    r = requests.patch(url, headers=_headers(), json=payload, timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(f"Appwrite update error {collection_id}: {r.status_code} {r.text}")
    return r.json()


def _list_documents(collection_id: str, queries=None, limit=25, offset=0):
    url = _collection_base(collection_id)
    params = {"limit": limit, "offset": offset}

    # IMPORTANTE: queries[] a veces en ciertos entornos da syntax error.
    # Hoy lo evitamos en order_items con filtro local.
    if queries:
        params["queries[]"] = queries

    r = requests.get(url, headers=_headers(), params=params, timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(f"Appwrite list error {collection_id}: {r.status_code} {r.text}")
    return r.json()


def _list_all_documents(collection_id: str, batch_size: int = 100, max_total: int = 2000):
    """
    Trae documentos paginando con offset/limit.
    max_total evita que se vuelva infinito si algo raro pasa.
    """
    all_docs = []
    offset = 0

    while True:
        res = _list_documents(collection_id, queries=None, limit=batch_size, offset=offset)
        docs = res.get("documents", []) or []
        total = res.get("total", None)

        all_docs.extend(docs)
        offset += len(docs)

        # corte por seguridad
        if len(all_docs) >= max_total:
            break

        # si no hay mas docs, paramos
        if not docs:
            break

        # si Appwrite nos da total, usamos ese
        if total is not None and offset >= int(total):
            break

    return all_docs


def _find_user_by_email(email: str):
    email = (email or "").strip().lower()
    if not email:
        return None

    # Si esto te falla por queries en algun momento, hacemos el mismo truco:
    # traemos users y filtramos local. Por ahora lo dejo con query.
    q = [f'equal("email", ["{email}"])']
    res = _list_documents(TABLE_USERS, queries=q, limit=1, offset=0)
    docs = res.get("documents", []) or []
    return docs[0] if docs else None


def _get_or_create_user(full_name: str, phone: str, email: str, city: str, address: str):
    email = (email or "").strip().lower()

    if not email:
        return _create_document(TABLE_USERS, {
            "full_name": full_name,
            "phone": phone,
            "email": "",
            "city": city,
            "address": address,
            "role": "buyer",
        })

    existing = _find_user_by_email(email)
    if existing:
        return _update_document(TABLE_USERS, existing.get("$id"), {
            "full_name": full_name or existing.get("full_name") or "",
            "phone": phone or existing.get("phone") or "",
            "city": city or existing.get("city") or "",
            "address": address or existing.get("address") or "",
            "role": existing.get("role") or "buyer",
        })

    return _create_document(TABLE_USERS, {
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "city": city,
        "address": address,
        "role": "buyer",
    })


def create_order_from_cart(form: dict, session_user: dict | None = None):
    cart = get_cart()
    if not cart or len(cart) == 0:
        raise ValueError("Carrito vacio")

    t = totals()

    full_name = (form.get("full_name") or "").strip()
    phone = (form.get("phone") or "").strip()
    email = (form.get("email") or "").strip().lower()
    city = (form.get("city") or "").strip()
    address = (form.get("address") or "").strip()
    notes = (form.get("notes") or "").strip()

    # si hay usuario logueado, usamos su id
    user_id = ""
    if session_user and session_user.get("id"):
        user_id = session_user.get("id")

    if not user_id:
        user_doc = _get_or_create_user(full_name, phone, email, city, address)
        user_id = user_doc.get("$id")

    # 1) Crear order
    order_doc = _create_document(TABLE_ORDERS, {
        "user_id": user_id,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "city": city,
        "address": address,
        "notes": notes,
        "status": "nuevo",
    })
    order_id = order_doc.get("$id")

    # 2) Crear order_items (con TODOS los required de tu tabla)
    for _, item in cart.items():
        qty = int(item.get("quantity") or 1)
        unit_price = float(item.get("unit_price") or 0)
        subtotal = unit_price * qty

        item_payload = {
            "order_id": order_id,  # required
            "product_id": str(item.get("product_id") or ""),  # required
            "variant_id": str(item.get("variant_id") or ""),  # opcional en DB (puede ir vacio)
            "product_name_snapshot": str(item.get("name") or "Producto"),  # required
            "variant_label_snapshot": str(item.get("variant_label") or ""),  # opcional
            "unit_price": unit_price,  # required
            "quantity": qty,  # required
            "subtotal": subtotal,  # required
        }

        _create_document(TABLE_ORDER_ITEMS, item_payload)

    # 3) WhatsApp link
    msg_lines = [
        "Hola! Quiero confirmar este pedido en Lamin Gold:",
        f"Pedido: {order_id}",
        f"Nombre: {full_name}",
        f"WhatsApp: {phone}",
        f"Ciudad: {city}",
        f"Direccion: {address}",
        "",
        "Items:"
    ]

    for _, item in cart.items():
        qty = int(item.get("quantity") or 1)
        unit_price = float(item.get("unit_price") or 0)
        line_total = unit_price * qty
        msg_lines.append(f"- {item.get('name','Producto')} x{qty} = $ {int(line_total)}")

    msg_lines += ["", f"Total: $ {int(t['subtotal'])}"]

    if notes:
        msg_lines.append(f"Notas: {notes}")

    text = quote("\n".join(msg_lines))
    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={text}"

    return {"order_id": order_id, "wa_url": wa_url}


def list_orders(limit: int = 50):
    try:
        q = ['orderDesc("$createdAt")']
        res = _list_documents(TABLE_ORDERS, queries=q, limit=limit, offset=0)
        return res.get("documents", []) or []
    except Exception:
        res = _list_documents(TABLE_ORDERS, queries=None, limit=limit, offset=0)
        return res.get("documents", []) or []


def get_order_items(order_id: str, limit: int = 200):
    """
    FIX MVP: NO usamos queries de Appwrite (porque te esta tirando Syntax error).
    Traemos order_items y filtramos en Python por order_id.
    """
    order_id = (order_id or "").strip()
    if not order_id:
        return []

    docs = _list_all_documents(TABLE_ORDER_ITEMS, batch_size=100, max_total=2000)

    items = []
    for d in docs:
        if (d.get("order_id") or "").strip() == order_id:
            items.append(d)

    # orden opcional por createdAt (si existe)
    try:
        items.sort(key=lambda x: x.get("$createdAt") or "")
    except Exception:
        pass

    # respetar limit por si hay muchos
    return items[:limit]


def update_order_status(order_id: str, status: str):
    order_id = (order_id or "").strip()
    status = (status or "").strip().lower()

    allowed = ["nuevo", "contactado", "en_proceso", "enviado", "entregado", "cancelado"]
    if status not in allowed:
        raise ValueError("Estado no permitido.")

    return _update_document(TABLE_ORDERS, order_id, {"status": status})
