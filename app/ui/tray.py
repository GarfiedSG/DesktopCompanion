"""系統托盤模組"""

from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction


class Tray(QSystemTrayIcon):
    """系統托盤"""
    
    def __init__(self, pet_window, config, parent=None):
        super().__init__(parent)
        self.pet = pet_window
        self.config = config
        
        self._init_icon()
        self._init_menu()
        
        self.activated.connect(self._on_activated)
    
    def _init_icon(self):
        """初始化托盤圖示"""
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        icon_path = BASE_DIR / "圖標" / "tray.png"
        
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # 使用空白圖示作為後備
            icon = QIcon()
        
        self.setIcon(icon)
        self.setToolTip("桌面伴侶 — 晴兒")
    
    def _init_menu(self):
        """初始化托盤選單"""
        menu = QMenu()
        
        action_show = QAction("顯示/隱藏晴兒", self)
        action_show.triggered.connect(self.pet.toggle_visibility)
        menu.addAction(action_show)
        
        self.action_mute = QAction("靜音", self, checkable=True)
        self.action_mute.setChecked(self.config.get("audio", {}).get("muted", False))
        self.action_mute.setEnabled(False)  # 第 3 步接入 AudioManager
        menu.addAction(self.action_mute)
        
        action_settings = QAction("設置", self)
        action_settings.setEnabled(False)  # 第 3 步接入設置窗口
        menu.addAction(action_settings)
        
        menu.addSeparator()
        
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.pet.quit_app)
        menu.addAction(action_quit)
        
        self.setContextMenu(menu)
    
    def _on_activated(self, reason):
        """托盤圖示被點擊"""
        if reason == QSystemTrayIcon.Trigger:
            self.pet.toggle_visibility()
