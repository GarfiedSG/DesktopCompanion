"""配置管理模組"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "pet_name": "晴兒",
    "image_path": "文檔/晴兒.png",
    "x": 1200,
    "y": 800,
    "scale": 1.0,
    "opacity": 1.0,
    "always_on_top": True,
    "locked": False,
}


def load_config():
    """載入配置檔案，補齊缺失欄位"""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    
    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    
    return data


def save_config(cfg):
    """保存配置到檔案"""
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
