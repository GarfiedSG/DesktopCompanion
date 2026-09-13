"""行為調度器模組"""

from PySide6.QtCore import QObject, QTimer


class BehaviorScheduler(QObject):
    """行為調度器"""
    
    def __init__(self, pet_window):
        super().__init__()
        self.pet = pet_window
        
        # 動畫更新 timer，30 FPS
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(1000 // 30)
    
    def _update_animation(self):
        """更新動畫"""
        # 更新待機移動（如果當前動畫有移動屬性）
        self.pet._update_idle_move()
        
        # 更新動畫幀
        pixmap, should_reschedule = self.pet.state_machine.next_frame()
        if pixmap:
            self.pet._set_pixmap(pixmap)
    
    def stop(self):
        """停止動畫更新"""
        self.anim_timer.stop()
