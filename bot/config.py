"""Bot konfiguratsiyasi. Barcha qiymatlar .env faylidan olinadi."""

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# DATABASE_URL berilsa, u ustunlik qiladi. Aks holda alohida DB_* o'zgaruvchilar ishlatiladi.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "quiz_bot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Daraja bo'yicha achko (ball) miqdori. C1 va C2 ikkalasi ham 5 achko.
LEVEL_POINTS = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 5,
}
LEVELS = list(LEVEL_POINTS.keys())

MEDAL_GOLD = 90
MEDAL_SILVER = 75
MEDAL_BRONZE = 65

if not BOT_TOKEN:
    raise RuntimeError(".env faylida BOT_TOKEN ko'rsatilmagan")
if not ADMIN_ID:
    raise RuntimeError(".env faylida ADMIN_ID ko'rsatilmagan")
