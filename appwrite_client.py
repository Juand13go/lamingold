from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID

from config import config


def get_appwrite_client() -> Client:
    client = Client()
    client.set_endpoint(config.APPWRITE_ENDPOINT)
    client.set_project(config.APPWRITE_PROJECT_ID)
    client.set_key(config.APPWRITE_API_KEY)
    return client


def get_databases_service() -> Databases:
    client = get_appwrite_client()
    return Databases(client)


def get_storage_service() -> Storage:
    client = get_appwrite_client()
    return Storage(client)


# Helper para ID (lo usaremos despues para crear documentos)
AppwriteID = ID
