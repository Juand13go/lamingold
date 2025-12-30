import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")

    APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "").strip()
    APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "").strip()
    APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "").strip()
    APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "").strip()
    APPWRITE_BUCKET_PRODUCT_IMAGES = os.getenv("APPWRITE_BUCKET_PRODUCT_IMAGES", "product-images").strip()


config = Config()
