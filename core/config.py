"""Application configuration"""
import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # Data Configuration
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_PATH: Path = BASE_DIR / "data" / "pre-re"
    ITEMS_USABLE_FILE: Path = DATA_PATH / "item_db_usable.yml"
    ITEMS_EQUIP_FILE: Path = DATA_PATH / "item_db_equip.yml"
    ITEMS_ETC_FILE: Path = DATA_PATH / "item_db_etc.yml"
    MONSTERS_FILE: Path = DATA_PATH / "mob_db.yml"
    ITEMINFO_FILE: Path = BASE_DIR / "data" / "itemInfo.lua"
    IMAGES_DIR: Path = BASE_DIR / "data" / "images"
    POPULARITY_FILE: Path = BASE_DIR / "data" / "popularity_data.json"
    
    @classmethod
    def ensure_data_directory(cls):
        """Ensure data directory exists"""
        cls.DATA_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
