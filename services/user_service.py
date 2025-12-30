from werkzeug.security import generate_password_hash, check_password_hash

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

from config import config
from models.constants import TABLE_USERS


def _client() -> Client:
    """
    Crea cliente Appwrite (SDK).
    Reemplaza todo lo que antes hacíamos con requests + headers.
    """
    if not config.APPWRITE_API_KEY:
        raise RuntimeError("APPWRITE_API_KEY no cargada (revisa .env)")
    if not config.APPWRITE_ENDPOINT or not config.APPWRITE_PROJECT_ID:
        raise RuntimeError("Faltan APPWRITE_ENDPOINT / APPWRITE_PROJECT_ID (revisa .env)")

    client = Client()
    client.set_endpoint(config.APPWRITE_ENDPOINT)
    client.set_project(config.APPWRITE_PROJECT_ID)
    client.set_key(config.APPWRITE_API_KEY)
    return client


def _db() -> Databases:
    """
    Servicio Databases del SDK.
    """
    return Databases(_client())


def _list_documents(collection_id: str, queries=None, limit=25):
    queries = queries or []

    # ✅ En tu SDK: el limite se manda como Query.limit()
    queries = queries + [Query.limit(limit)]

    return _db().list_documents(
        config.APPWRITE_DATABASE_ID,
        collection_id,
        queries
    )



def _create_document(collection_id: str, data: dict):
    """
    Igual que antes, pero con SDK.
    """
    try:
        return _db().create_document(
            database_id=config.APPWRITE_DATABASE_ID,
            collection_id=collection_id,
            document_id="unique()",
            data=data
        )
    except Exception as e:
        print("APPWRITE ERROR (create):", str(e))
        raise


def get_user_by_email(email: str):
    email = (email or "").strip().lower()
    if not email:
        return None

    # ✅ Esta es la forma correcta en tu Appwrite: Query.equal del SDK
    res = _list_documents(
        TABLE_USERS,
        queries=[Query.equal("email", email)],
        limit=1
    )
    docs = res.get("documents", []) or []
    return docs[0] if docs else None


def create_user(full_name: str, email: str, password: str, role="buyer", phone="", city="", address=""):
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not full_name or not email or not password:
        raise ValueError("Faltan campos obligatorios (full_name, email, password).")

    password_hash = generate_password_hash(password)

    data = {
        "full_name": full_name,
        "email": email,
        "password_hash": password_hash,
        "phone": phone,
        "city": city,
        "address": address,
        "role": role or "buyer",
    }

    return _create_document(TABLE_USERS, data)


def verify_password(user_doc: dict, password: str) -> bool:
    if not user_doc:
        return False
    stored = user_doc.get("password_hash") or ""
    if not stored:
        return False
    return check_password_hash(stored, password or "")


def public_user_session(user_doc: dict) -> dict:
    return {
        "id": user_doc.get("$id"),
        "full_name": user_doc.get("full_name"),
        "email": user_doc.get("email"),
        "role": user_doc.get("role", "buyer"),
    }
