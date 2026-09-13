"""待機動畫調度器模組"""

import random
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from app.core.animation_library import AnimationLibrary


# 常量定義
MIN_HOLD_SECONDS = 60         # 所有待機動畫至少持續 1 分鐘
IDLE_STANDING_BOOST = 3      # idle_standing 權重倍數
IDLE_STANDING_PATH = "animations/idle/idle_standing"  # 統一使用正斜杠


class IdleScheduler(QObject):
    """待機動畫調度器"""
    
    switch_requested = Signal(dict)  # 信號：傳遞動畫配置 dict
    
    def __init__(self, base_dir, config):
        super().__init__()
        self.base_dir = base_dir
        self.config = config
        self.anim_library = AnimationLibrary(base_dir)
        
        self.current_anim_path = None
        self.enabled_anims = []
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._schedule_next)
        
        self._load_animations()
    
    def _load_animations(self):
        """載入動畫清單"""
        self.enabled_anims = self.anim_library.get_enabled()
    
    def start(self, current_path=None):
        """開始調度
        
        Args:
            current_path: 當前動畫路徑，若為 None 則不設定
        """
        if not self.enabled_anims:
            return
        
        # 設定當前動畫路徑
        if current_path:
            self.current_anim_path = current_path
        
        # 排程下一次切換
        self._schedule_next()
    
    def stop(self):
        """停止調度"""
        self.timer.stop()
    
    def pause(self):
        """暫停調度"""
        self.timer.stop()
    
    def resume(self):
        """恢復調度"""
        if self.enabled_anims:
            self._schedule_next()
    
    def _schedule_next(self):
        """排程下一次切換"""
        if not self.enabled_anims:
            return
        
        idle_switch = self.config.get("idle_switch", {})
        
        # 確定切換間隔
        min_interval = max(MIN_HOLD_SECONDS, idle_switch.get("min_interval", 30))
        max_interval = max(min_interval, idle_switch.get("max_interval", 180))
        interval = random.randint(min_interval, max_interval) * 1000
        
        self.timer.start(interval)
        
        # 選擇下一個動畫
        next_anim = self._select_next_animation()
        if next_anim:
            self.current_anim_path = next_anim["path"]
            self.switch_requested.emit(next_anim)
    
    def _select_next_animation(self):
        """隨機選擇下一個動畫"""
        if not self.enabled_anims:
            return None
        
        idle_switch = self.config.get("idle_switch", {})
        avoid_repeat = idle_switch.get("avoid_repeat", True)
        idle_standing_boost = idle_switch.get("idle_standing_boost", IDLE_STANDING_BOOST)
        
        # 篩選可選動畫
        if avoid_repeat and self.current_anim_path:
            available = [
                anim for anim in self.enabled_anims
                if anim.get("path") != self.current_anim_path
            ]
        else:
            available = self.enabled_anims
        
        if not available:
            # 如果沒有可選動畫（只有一個啟用），返回當前動畫
            return self.enabled_anims[0] if self.enabled_anims else None
        
        # 計算權重：idle_standing 權重提升
        weights = []
        for anim in available:
            weight = anim.get("weight", 1)
            if anim.get("path") == IDLE_STANDING_PATH:
                weight *= idle_standing_boost
            weights.append(weight)
        
        return random.choices(available, weights=weights, k=1)[0]
    
    def set_current_anim(self, anim_path):
        """設定當前動畫路徑"""
        self.current_anim_path = anim_path
    
    def _get_idle_standing_anim(self):
        """取得 idle_standing 動畫配置"""
        for anim in self.enabled_anims:
            if anim.get("path") == IDLE_STANDING_PATH:
                return anim
        return None
    
    def reset_to(self, path: str):
        """將當前動畫設為指定路徑，並重置計時器"""
        self.current_anim_path = path
        self.timer.stop()
        self._schedule_next()
    
    def force_idle_standing(self):
        """強制切換到 idle_standing 並重置計時"""
        standing_anim = self._get_idle_standing_anim()
        if standing_anim:
            self.current_anim_path = standing_anim["path"]
            # 複製 anim dict 並添加 force 標記
            anim_with_force = dict(standing_anim)
            anim_with_force["force"] = True
            self.switch_requested.emit(anim_with_force)
            # 重置計時為最小保持時間
            self.timer.stop()
            self.timer.start(MIN_HOLD_SECONDS * 1000)
    
    def reload(self):
        """重新掃描動畫清單"""
        self._load_animations()
