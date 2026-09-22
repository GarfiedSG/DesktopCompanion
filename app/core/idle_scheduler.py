"""待機動畫調度器模組"""

import random
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from app.core.animation_library import AnimationLibrary


# 常量定義
MIN_HOLD_SECONDS = 60         # 所有待機動畫至少持續 1 分鐘


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
        self.timer.timeout.connect(self._do_switch)
        
        self._load_animations()
    
    def _load_animations(self):
        """載入動畫清單"""
        self.enabled_anims = self.anim_library.get_enabled()
    
    def start(self):
        """開始調度"""
        if not self.enabled_anims:
            return
        
        # 立即隨機選擇一個動畫
        self.pick_random()
    
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
        
        # 確定切換間隔：MIN_HOLD_SECONDS 為絕對最小值
        min_interval = MIN_HOLD_SECONDS
        max_interval = max(min_interval, idle_switch.get("max_interval", 180))
        interval = random.randint(min_interval, max_interval) * 1000
        
        self.timer.start(interval)
    
    def _do_switch(self):
        """執行動畫切換（timer 到期時呼叫）"""
        if not self.enabled_anims:
            return
        
        # 選擇下一個動畫
        next_anim = self._select_next_animation()
        if next_anim:
            self.current_anim_path = next_anim["path"]
            self.switch_requested.emit(next_anim)
        
        # 排程下一次切換
        self._schedule_next()
    
    def _select_next_animation(self):
        """隨機選擇下一個動畫"""
        if not self.enabled_anims:
            return None
        
        idle_switch = self.config.get("idle_switch", {})
        avoid_repeat = idle_switch.get("avoid_repeat", True)
        
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
        
        # 計算權重：weight 越小，權重越高
        weights = [1 / max(anim.get("weight", 1), 1) for anim in available]
        
        return random.choices(available, weights=weights, k=1)[0]
    
    def set_current_anim(self, anim_path):
        """設定當前動畫路徑"""
        self.current_anim_path = anim_path
    
    def pick_random(self):
        """立即隨機選擇一個啟用動畫（不排除當前），並發出切換信號"""
        if not self.enabled_anims:
            return
        
        # 計算權重：weight 越小，權重越高
        weights = [1 / max(anim.get("weight", 1), 1) for anim in self.enabled_anims]
        chosen = random.choices(self.enabled_anims, weights=weights, k=1)[0]
        
        self.current_anim_path = chosen["path"]
        self.timer.stop()
        self.switch_requested.emit(chosen)
        self._schedule_next()
    
    def force_idle_standing(self):
        """強制切換到 idle_standing 並重置計時（保留供未來使用）"""
        # 此方法保留供未來使用，目前不實作
        pass
    
    def reload(self):
        """重新掃描動畫清單"""
        self._load_animations()
