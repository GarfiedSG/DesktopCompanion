"""動畫庫模組"""

import json
import re
from pathlib import Path


DEFAULT_ANIM_CONFIG = {
    "name": None,           # 預設用資料夾名
    "enabled": True,
    "weight": 1,
    "move": False,
    "move_speed": 4,
    "move_range": 200,
}


def natural_key(path: Path):
    """自然排序鍵函數"""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", path.stem)]


class AnimationLibrary:
    """動畫庫類別"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.idle_dir = base_dir / "文檔" / "animations" / "idle"
    
    def scan(self) -> list:
        """掃描 idle 資料夾，回傳動畫清單"""
        animations = []
        if not self.idle_dir.exists():
            return animations
        
        for folder in sorted(self.idle_dir.iterdir()):
            if not folder.is_dir():
                continue
            
            frames = sorted(folder.glob("frame_*.png"), key=natural_key)
            if not frames:
                continue
            
            config_path = folder / "anim.json"
            anim = dict(DEFAULT_ANIM_CONFIG)
            if config_path.exists():
                try:
                    data = json.loads(config_path.read_text(encoding="utf-8"))
                    for k in DEFAULT_ANIM_CONFIG:
                        if k in data:
                            anim[k] = data[k]
                except (json.JSONDecodeError, OSError):
                    pass
            
            if anim["name"] is None:
                anim["name"] = folder.name
            
            # 統一路徑格式為正斜杠
            anim["path"] = str(folder.relative_to(self.base_dir / "文檔")).replace("\\", "/")
            anim["frames"] = [str(f) for f in frames]
            animations.append(anim)
        
        return animations
    
    def get_enabled(self) -> list:
        """回傳啟用的動畫清單"""
        return [a for a in self.scan() if a.get("enabled", True)]
    
    def reload(self):
        """重新掃描動畫（目前無需實現，直接呼叫 scan 即可）"""
        pass
