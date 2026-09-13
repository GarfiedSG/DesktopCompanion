"""桌面伴侶主程式入口"""

import sys
from PySide6.QtWidgets import QApplication
from app.config import load_config
from app.ui.pet_window import PetWindow
from app.ui.tray import Tray


def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 托盤程式，關窗不退出
    
    config = load_config()
    
    pet = PetWindow(config)
    pet.show()
    
    tray = Tray(pet, config)
    tray.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
