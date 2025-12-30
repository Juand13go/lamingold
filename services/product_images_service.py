# services/product_images_service.py
import requests
from config import config
from models.constants import TABLE_PRODUCT_IMAGES


def _headers_json():
    return {
        "X-Appwrite-Project": config.APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": config.APPWRITE_API_KEY,
        "Content-Type": "application/json",
    }


def _headers_file():
    return {
        "X-Appwrite-Project": config.APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": config.APPWRITE_API_KEY,
    }


def _base():
    return (config.APPWRITE_ENDPOINT or "").strip().rstrip("/")


def _collection_base(collection_id: str) -> str:
    return f"{_base()}/databases/{config.APPWRITE_DATABASE_ID}/collections/{collection_id}/documents"


def _storage_upload_url(bucket_id: str) -> str:
    return f"{_base()}/storage/buckets/{bucket_id}/files"


def upload_file_to_bucket(file_storage) -> str:
    bucket_id = (config.APPWRITE_BUCKET_PRODUCT_IMAGES or "").strip()
    if not bucket_id:
        raise RuntimeError("Falta APPWRITE_BUCKET_PRODUCT_IMAGES en .env")

    url = _storage_upload_url(bucket_id)

    files = {
        "file": (file_storage.filename, file_storage.stream, file_storage.mimetype)
    }
    data = {"fileId": "unique()"}

    r = requests.post(url, headers=_headers_file(), files=files, data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(r.text)

    file_id = (r.json().get("$id") or "").strip()
    if not file_id:
        raise RuntimeError("No se recibio file_id al subir la imagen.")
    return file_id


def link_product_image(product_id: str, file_id: str):
    product_id = (product_id or "").strip()
    file_id = (file_id or "").strip()
    if not product_id or not file_id:
        raise ValueError("product_id y file_id son requeridos")

    url = _collection_base(TABLE_PRODUCT_IMAGES)
    payload = {
        "documentId": "unique()",
        "data": {
            "product_id": product_id,
            "file_id": file_id
        }
    }

    r = requests.post(url, headers=_headers_json(), json=payload, timeout=25)
    if r.status_code >= 400:
        raise RuntimeError(r.text)
    return r.json()


def upload_and_link_product_image(product_id: str, file_storage):
    # 1) Subir al bucket -> obtener file_id
    file_id = upload_file_to_bucket(file_storage)

    # 2) Crear fila en product_images (SIN queries)
    return link_product_image(product_id, file_id)
