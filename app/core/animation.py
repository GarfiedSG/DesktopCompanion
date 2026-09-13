"""動畫狀態機模組"""

from PySide6.QtGui import QPixmap


class AnimationStateMachine:
    """動畫狀態機"""
    
    def __init__(self):
        self.state = "Idle"
        self.frames = {}  # state -> list[QPixmap]
        self.current_index = 0
        self.frame_count = 0
    
    def load_frames(self, state, paths):
        """載入某狀態的序列帧"""
        self.frames[state] = [QPixmap(str(p)) for p in paths]
    
    def set_state(self, new_state):
        """設定新狀態，返回是否狀態有變化"""
        if self.state == new_state:
            return False
        self.state = new_state
        self.current_index = 0
        self.frame_count = 0
        return True
    
    def next_frame(self):
        """取得下一幀，返回是否需要切換回 Idle"""
        frames = self.frames.get(self.state, [])
        if not frames:
            # 如果當前狀態沒有幀，fallback 到 Idle 的當前幀
            idle_frames = self.frames.get("Idle", [])
            if idle_frames:
                self.current_index = self.current_index % len(idle_frames)
                return idle_frames[self.current_index], False
            return None, False
        
        # 確保 current_index 在有效範圍內
        if self.current_index >= len(frames):
            self.current_index = 0
        
        pixmap = frames[self.current_index]
        self.frame_count += 1
        
        # 點擊動畫只播一次
        if self.state == "Click" and self.current_index == len(frames) - 1:
            self.set_state("Idle")
            return pixmap, True
        else:
            self.current_index = (self.current_index + 1) % len(frames)
            return pixmap, False
    
    def get_current_frame(self):
        """取得當前幀"""
        frames = self.frames.get(self.state, [])
        if not frames:
            return None
        return frames[self.current_index]
