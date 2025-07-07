import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

# Database
DB_FILE = os.getenv("DB_FILE")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

# API
API_TOKEN = os.getenv("API_TOKEN")
LOGO_DOWNLOAD_PATH = os.getenv("LOGO_DOWNLOAD_PATH")
BASE_URL = os.getenv("BASE_URL")

# Email
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


# Admin
ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE")