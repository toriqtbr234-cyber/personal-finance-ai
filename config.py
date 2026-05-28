import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-ganti-di-produksi")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"

    # In-memory storage (no database)
    # Data disimpan sementara di session Flask selama aplikasi berjalan
    MAX_EXPENSES = 500
    CURRENCY = "IDR"
    CURRENCY_SYMBOL = "Rp"
