from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 8000))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./solarsats.db")
    SATOSHIS_PER_KWH = int(os.getenv("SATOSHIS_PER_KWH", 50))
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    LND_ADDRESS = os.getenv("LND_ADDRESS", "localhost:10009")

config = Config()

def load_config():
    print(f"✅ Config loaded: Port={config.PORT}, Sats/kWh={config.SATOSHIS_PER_KWH}")
    return config
