"""寵物窗口模組"""

from pathlib import Path
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPixmap, QAction, QGuiApplication
from PySide6.QtWidgets import QWidget, QLabel, QMenu, QApplication

from app.config import save_config
from app.core.animation import AnimationStateMachine
from app.core.behavior import BehaviorScheduler
from app.core.idle_scheduler import IdleScheduler


class PetWindow(QWidget):
    """透明置頂寵物窗口"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._drag_offset = None
        self._press_pos = None
        self._dragging = False
        
        # 初始化動畫狀態機
        self.state_machine = AnimationStateMachine()
        
        # 初始化行為調度器
        self.scheduler = BehaviorScheduler(self)
        
        # 初始化待機調度器
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.idle_scheduler = IdleScheduler(BASE_DIR, config)
        self.idle_scheduler.switch_requested.connect(self._on_idle_switch_wrapper)
        
        # 待機移動相關屬性
        self._idle_move_origin = None  # 移動原點
        self._idle_move_direction = 1  # 移動方向：1 或 -1
        self._idle_move_speed = 4  # 移動速度（像素/幀）
        self._idle_move_range = 200  # 移動範圍（像素）
        self._idle_move_enabled = False  # 是否啟用待機移動
        self._current_idle_path = None  # 當前待機動畫路徑
        
        self._init_ui()
        self._load_image()
        self._init_animation_frames()
        self._apply_config()
        self._load_first_idle_animation()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
    
    def _load_image(self):
        """載入圖片"""
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        IMAGE_PATH = BASE_DIR / "文檔" / "晴兒.png"
        
        pixmap = QPixmap(str(IMAGE_PATH))
        if pixmap.isNull():
            raise FileNotFoundError(f"找不到圖片：{IMAGE_PATH}")
        
        self.original_pixmap = pixmap
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.size())
        self.resize(pixmap.size())
    
    def _init_animation_frames(self):
        """初始化動畫帧"""
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        
        # Click 和 Drag 狀態用單張圖片（稍後會動態載入）
        image_path = BASE_DIR / "文檔" / "晴兒.png"
        self.state_machine.load_frames("Click", [image_path])
        self._load_drag_animation(BASE_DIR)
    
    def _load_drag_animation(self, base_dir):
        """載入 Drag 動畫"""
        drag_path = base_dir / "文檔" / "animations" / "drag"
        if drag_path.exists():
            frame_files = sorted(drag_path.glob("frame_*.png"))
            if frame_files:
                self.state_machine.load_frames("Drag", frame_files)
            else:
                # 沒有 Drag 動畫，用單張圖片
                image_path = base_dir / "文檔" / "晴兒.png"
                self.state_machine.load_frames("Drag", [image_path])
        else:
            # Drag 資料夾不存在，用單張圖片
            image_path = base_dir / "文檔" / "晴兒.png"
            self.state_machine.load_frames("Drag", [image_path])
    
    def _load_first_idle_animation(self):
        """載入第一個待機動畫"""
        # 隨機選擇初始動畫
        self.idle_scheduler.start()
    
    def _on_idle_switch_wrapper(self, anim):
        """包裝方法，從信號中提取 force 參數"""
        force = anim.get("force", False)
        self._on_idle_switch(anim, force)
    
    def _load_animation_from_config(self, anim):
        """從配置載入動畫"""
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        
        # 使用 anim dict 中的 frames 路徑
        frame_paths = anim.get("frames", [])
        if frame_paths:
            # 將相對路徑轉換為絕對路徑
            frame_files = [BASE_DIR / "文檔" / path for path in frame_paths]
            self.state_machine.load_frames("Idle", frame_files)
        else:
            # 沒有動畫帧，用單張圖片
            image_path = BASE_DIR / "文檔" / "晴兒.png"
            self.state_machine.load_frames("Idle", [image_path])
        
        # 重置動畫索引
        self.state_machine.current_index = 0
        self.state_machine.frame_count = 0
        
        # 更新當前動畫路徑
        self._current_idle_path = anim["path"]
        self.idle_scheduler.set_current_anim(anim["path"])
        
        # 處理移動屬性
        move = anim.get("move", False)
        if move:
            self._start_idle_move(
                anim.get("move_speed", 4),
                anim.get("move_range", 200)
            )
        else:
            self._stop_idle_move(restore_origin=False)
    
    def _on_idle_switch(self, anim, force=False):
        """處理待機動畫切換
        
        Args:
            anim: 動畫配置 dict
            force: 是否強制切換（忽略相同動畫判斷）
        """
        # 如果與當前動畫相同且非強制切換，跳過
        if not force and anim.get("path") == self._current_idle_path:
            return
        
        # 停止舊的移動（不回到原點）
        self._stop_idle_move(restore_origin=False)
        
        # 載入新動畫
        self._load_animation_from_config(anim)
        
        # 強制切換時，確保狀態機處於 Idle 狀態並顯示第一幀
        if force:
            self.state_machine.set_state("Idle")
            self.state_machine.current_index = 0
            idle_frames = self.state_machine.frames.get("Idle", [])
            if idle_frames:
                self._set_pixmap(idle_frames[0])
        else:
            # 正常切換也立即顯示第一幀
            self.state_machine.set_state("Idle")
            self.state_machine.current_index = 0
            idle_frames = self.state_machine.frames.get("Idle", [])
            if idle_frames:
                self._set_pixmap(idle_frames[0])
    
    def _set_pixmap(self, pixmap):
        """設定當前幀"""
        scale = self.config.get("scale", 1.0)
        if scale != 1.0:
            scaled_pixmap = pixmap.scaled(
                int(pixmap.width() * scale),
                int(pixmap.height() * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
            self.label.resize(scaled_pixmap.size())
            self.resize(scaled_pixmap.size())
        else:
            self.label.setPixmap(pixmap)
            self.label.resize(pixmap.size())
            self.resize(pixmap.size())
    
    def _start_idle_move(self, speed, move_range):
        """開始待機移動"""
        self._idle_move_enabled = True
        self._idle_move_speed = speed
        self._idle_move_range = move_range
        self._idle_move_origin = QPoint(self.x(), self.y())
        self._idle_move_direction = 1
    
    def _stop_idle_move(self, restore_origin=False):
        """停止待機移動
        
        Args:
            restore_origin: 是否回到移動原點
        """
        self._idle_move_enabled = False
        if restore_origin and self._idle_move_origin:
            self.move(self._idle_move_origin)
        self._idle_move_origin = None
    
    def _update_idle_move(self):
        """每幀更新待機移動位置"""
        if not self._idle_move_enabled or getattr(self, "_dragging", False):
            return
        
        if self._idle_move_origin is None:
            self._idle_move_origin = QPoint(self.x(), self.y())
        
        # 水平來回移動
        current_x = self.x()
        origin_x = self._idle_move_origin.x()
        
        # 計算新的 X 位置
        new_x = current_x + (self._idle_move_speed * self._idle_move_direction)
        
        # 檢查是否超出範圍
        if new_x > origin_x + self._idle_move_range:
            new_x = origin_x + self._idle_move_range
            self._idle_move_direction = -1
        elif new_x < origin_x - self._idle_move_range:
            new_x = origin_x - self._idle_move_range
            self._idle_move_direction = 1
        
        self.move(new_x, self.y())
    
    def _apply_config(self):
        """套用配置"""
        scale = self.config.get("scale", 1.0)
        opacity = self.config.get("opacity", 1.0)
        x = self.config.get("x", 1200)
        y = self.config.get("y", 800)
        always_on_top = self.config.get("always_on_top", True)
        locked = self.config.get("locked", False)
        
        # 套用縮放
        if scale != 1.0:
            scaled_pixmap = self.original_pixmap.scaled(
                int(self.original_pixmap.width() * scale),
                int(self.original_pixmap.height() * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
            self.label.resize(scaled_pixmap.size())
            self.resize(scaled_pixmap.size())
        
        # 套用透明度
        self.setWindowOpacity(opacity)
        
        # 套用置頂
        if always_on_top:
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
        else:
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.Tool
            )
        
        # 檢查位置是否在螢幕範圍內
        screen = QGuiApplication.screenAt(QPoint(x, y))
        if screen is None:
            # 位置不在任何螢幕上，回到主螢幕中央
            screen = QGuiApplication.primaryScreen()
            if screen:
                geometry = screen.availableGeometry()
                x = geometry.center().x() - self.width() // 2
                y = geometry.center().y() - self.height() // 2
        
        self.move(x, y)
        self.show()
    
    def mousePressEvent(self, event):
        """滑鼠按下事件"""
        if self.config.get("locked", False):
            return
        
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._dragging = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if self.config.get("locked", False):
            return
        
        if event.buttons() & Qt.LeftButton and hasattr(self, "_press_pos"):
            cur = event.globalPosition().toPoint()
            if not self._dragging:
                if (cur - self._press_pos).manhattanLength() > 5:
                    self._dragging = True
                    self.state_machine.set_state("Drag")
                    if hasattr(self, "idle_scheduler"):
                        self.idle_scheduler.pause()
                    # 拖拽時更新移動原點為當前位置
                    self._idle_move_origin = QPoint(self.x(), self.y())
                    # 捕捉滑鼠，確保 release 事件不會漏掉
                    self.grabMouse()
            if self._dragging:
                self.move(cur - self._drag_offset)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件"""
        if event.button() == Qt.LeftButton:
            if getattr(self, "_dragging", False):
                # 保存位置到 config
                self.config["x"] = self.x()
                self.config["y"] = self.y()
                save_config(self.config)
                
                # 立即切回待機
                self.state_machine.set_state("Idle")
                self.state_machine.current_index = 0
                
                # 隨機選擇新動畫
                if hasattr(self, "idle_scheduler") and self.idle_scheduler:
                    self.idle_scheduler.pick_random()
                else:
                    # fallback：手動載入當前待機動畫第一幀
                    idle_frames = self.state_machine.frames.get("Idle", [])
                    if idle_frames:
                        self._set_pixmap(idle_frames[0])
                
                # 釋放滑鼠捕捉
                try:
                    self.releaseMouse()
                except Exception:
                    pass
                
                self._dragging = False
            else:
                # 視為點擊
                self.state_machine.set_state("Click")
            
            # 清理臨時屬性
            for attr in ("_press_pos", "_drag_offset"):
                if hasattr(self, attr):
                    delattr(self, attr)
            event.accept()
    
    def contextMenuEvent(self, event):
        """右鍵選單事件"""
        menu = QMenu(self)
        
        action_show = QAction("顯示/隱藏", self)
        action_show.triggered.connect(self.toggle_visibility)
        menu.addAction(action_show)
        
        action_lock = QAction("鎖定位置", self, checkable=True)
        action_lock.setChecked(self.config.get("locked", False))
        action_lock.triggered.connect(self.toggle_lock)
        menu.addAction(action_lock)
        
        action_top = QAction("永遠置頂", self, checkable=True)
        action_top.setChecked(self.config.get("always_on_top", True))
        action_top.triggered.connect(self.toggle_on_top)
        menu.addAction(action_top)
        
        scale_menu = menu.addMenu("縮放")
        for pct in (50, 75, 100, 125, 150):
            action = QAction(f"{pct}%", self)
            action.triggered.connect(lambda _, p=pct: self.set_scale(p / 100))
            scale_menu.addAction(action)
        
        menu.addSeparator()
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.quit_app)
        menu.addAction(action_quit)
        
        menu.exec(event.globalPos())
    
    def toggle_visibility(self):
        """切換顯示/隱藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
    
    def toggle_lock(self):
        """切換鎖定狀態"""
        self.config["locked"] = not self.config.get("locked", False)
        save_config(self.config)
    
    def toggle_on_top(self):
        """切換置頂狀態"""
        self.config["always_on_top"] = not self.config.get("always_on_top", True)
        save_config(self.config)
        self._apply_config()
    
    def set_scale(self, scale):
        """設定縮放比例"""
        self.config["scale"] = scale
        save_config(self.config)
        self._apply_config()
    
    def quit_app(self):
        """退出程式"""
        self.scheduler.stop()
        self.idle_scheduler.stop()
        self._stop_idle_move(restore_origin=False)
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        save_config(self.config)
        QApplication.quit()
