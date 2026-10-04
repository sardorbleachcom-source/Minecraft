# -*- coding: utf-8 -*-
"""Sozlamalar: .env, yo'llar, kategoriyalar, logging."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env topilmasa env.txt ham ishlaydi (Pydroid'da yashirin fayl bilan muammo bo'lsa)
for _name in (".env", "env.txt"):
    if (BASE_DIR / _name).exists():
        load_dotenv(BASE_DIR / _name)
        break

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", "").split(",") if x.isdigit()}

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"
LOCALES_DIR = BASE_DIR / "locales"
SEED_PATH = BASE_DIR / "seed.json"

LANGS = ("uz", "en", "ru", "ar")
DEFAULT_LANG = "uz"
PAGE_SIZE = 4  # bir sahifada nechta buyruq

CATEGORIES = [
    "gamemode", "time", "weather", "teleport", "items", "effects", "mobs",
    "lightning", "tnt", "build", "nature", "village", "locate", "rules",
    "kill", "inventory", "xp", "cmdblocks", "structures",
]
MENU_ORDER = CATEGORIES + ["search", "about"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(DATA_DIR / "bot.log", encoding="utf-8"), logging.StreamHandler()],
)
