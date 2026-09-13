# 第 1 步：項目骨架 + 透明置頂窗口 + 托盤 + 配置

## 一、目標

桌面出現「晴兒」，透明、置頂、可拖拽、可退出，重開後記住位置。

完成後，你應該看到：
- 螢幕上出現晴兒的圖片，背景透明。
- 可以用滑鼠左鍵拖動晴兒。
- 右鍵晴兒有選單。
- 系統托盤有圖示，可以顯示/隱藏晴兒、退出。
- 關閉程式再開，晴兒回到上次的位置。

---

## 二、對應需求

- 3.1.1 透明置頂窗口
- 3.1.4 基礎互動（拖拽、右鍵、托盤）
- 4.1 config.json
- 4.2 圖片路徑注意事項

---

## 三、要建立的檔案與結構

```text
桌面伴侶/
├─ main.py
├─ config.json
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ ui/
│  │  ├─ __init__.py
│  │  ├─ pet_window.py
│  │  └─ tray.py
└─ 文檔/
   └─ 晴兒.png
```

**說明**：
- `__init__.py` 可以是空檔案，讓 Python 認得這是套件。
- `config.json` 第一次啟動時可自動生成，也可以手動預先建立。
- `文檔/晴兒.png` 由你自己放入，這是唯一的圖片素材。

---

## 四、具體任務

### 4.1 建立透明置頂窗口

用 `QWidget` 做透明置頂窗口，設定以下 flags 與屬性：

- `Qt.FramelessWindowHint`：無邊框
- `Qt.WindowStaysOnTopHint`：永遠置頂
- `Qt.Tool`：不顯示在工作列
- `WA_TranslucentBackground`：背景透明
- `WA_NoSystemBackground`：不繪製系統背景

載入圖片：

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 依實際層級調整
IMAGE_PATH = BASE_DIR / "文檔" / "晴兒.png"
```

視窗大小根據圖片尺寸設定，並套用 `scale`（縮放）與 `opacity`（透明度）。

### 4.2 實現左鍵拖拽

- `mousePressEvent`：記錄滑鼠按下時相對窗口左上角的偏移。
- `mouseMoveEvent`：按住左鍵時，根據全域滑鼠位置移動窗口。
- `mouseReleaseEvent`：清除拖拽狀態，保存新位置到 config。

### 4.3 實現右鍵選單

用 `QMenu`，包含：
- 顯示 / 隱藏
- 鎖定位置（勾選）
- 永遠置頂（勾選）
- 縮放（子選單：50% / 75% / 100% / 125% / 150%）
- 退出

### 4.4 實現系統托盤

用 `QSystemTrayIcon` + `QMenu`，包含：
- 顯示 / 隱藏晴兒
- 靜音（勾選，預留，第 3 步接入 AudioManager）
- 設置（預留，第 3 步接入設置窗口）
- 退出

托盤圖示從 `圖標/tray.png` 載入；若檔案不存在，用預設圖示代替。

### 4.5 實現 ConfigManager

用 JSON 保存以下欄位：

| 欄位 | 型別 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `pet_name` | str | `"晴兒"` | 寵物名稱 |
| `image_path` | str | `"文檔/晴兒.png"` | 圖片相對路徑 |
| `x` | int | 1200 | 窗口左上角 X |
| `y` | int | 800 | 窗口左上角 Y |
| `scale` | float | 1.0 | 縮放比例 |
| `opacity` | float | 1.0 | 透明度 |
| `always_on_top` | bool | true | 是否置頂 |
| `locked` | bool | false | 是否鎖定位置 |

流程：
- 啟動時 `load_config()`，讀取並補齊缺失欄位。
- 關閉時 `save_config()`，寫入目前狀態。
- 拖拽結束、縮放改變、置頂切換時即時保存。

### 4.6 多螢幕與工作區

- 窗口位置限制在「工作區」內，避開工具列。
- 可用 `QGuiApplication.screenAt()` 取得目前所在螢幕。
- 保存位置時，一併記錄螢幕 ID（可選，但建議）。
- 啟動時若保存的位置不在任何螢幕範圍內，回到主螢幕中央。

### 4.7 透明區域點擊穿透

- Windows：設定 `WS_EX_LAYERED | WS_EX_TRANSPARENT`。
- 或者做動態命中測試：滑鼠在圖片非透明像素範圍內才接收點擊，否則穿透。
- 第一版可先不做穿透，確保拖拽正常；穿透作為增強項。

---

## 五、關鍵代碼要點

### 5.1 窗口 flags 與屬性

```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

class PetWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
```

### 5.2 載入圖片

```python
from pathlib import Path
from PySide6.QtGui import QPixmap

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_PATH = BASE_DIR / "文檔" / "晴兒.png"

pixmap = QPixmap(str(IMAGE_PATH))
if pixmap.isNull():
    raise FileNotFoundError(f"找不到圖片：{IMAGE_PATH}")
```

### 5.3 ConfigManager

```python
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
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
```

### 5.4 拖拽

```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self._drag_offset = (
            event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        )
        event.accept()

def mouseMoveEvent(self, event):
    if event.buttons() & Qt.LeftButton and hasattr(self, "_drag_offset"):
        new_pos = event.globalPosition().toPoint() - self._drag_offset
        self.move(new_pos)
        event.accept()

def mouseReleaseEvent(self, event):
    if event.button() == Qt.LeftButton:
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        save_config(self.config)
        if hasattr(self, "_drag_offset"):
            del self._drag_offset
        event.accept()
```

### 5.5 右鍵選單

```python
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

def contextMenuEvent(self, event):
    menu = QMenu(self)
    menu.addAction("顯示/隱藏", self.toggle_visibility)
    menu.addAction("鎖定位置", self.toggle_lock)
    menu.addAction("永遠置頂", self.toggle_on_top)

    scale_menu = menu.addMenu("縮放")
    for pct in (50, 75, 100, 125, 150):
        action = QAction(f"{pct}%", self)
        action.triggered.connect(lambda _, p=pct: self.set_scale(p / 100))
        scale_menu.addAction(action)

    menu.addSeparator()
    menu.addAction("退出", self.quit_app)
    menu.exec(event.globalPos())
```

### 5.6 系統托盤

```python
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

class Tray(QSystemTrayIcon):
    def __init__(self, pet_window, config, parent=None):
        super().__init__(parent)
        self.pet = pet_window
        self.config = config

        icon_path = Path("圖標") / "tray.png"
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.style().standardIcon(...)
        self.setIcon(icon)
        self.setToolTip("桌面伴侶 — 晴兒")

        menu = QMenu()
        menu.addAction("顯示/隱藏晴兒", self.pet.toggle_visibility)
        self.action_mute = QAction("靜音", self, checkable=True)
        self.action_mute.setChecked(config.get("audio", {}).get("muted", False))
        menu.addAction(self.action_mute)
        menu.addAction("設置", self.open_settings)  # 第 3 步接入
        menu.addSeparator()
        menu.addAction("退出", self.pet.quit_app)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.pet.toggle_visibility()

    def open_settings(self):
        # 第 3 步接入設置窗口
        pass
```

### 5.7 main.py 入口

```python
import sys
from PySide6.QtWidgets import QApplication
from app.config import load_config
from app.ui.pet_window import PetWindow
from app.ui.tray import Tray

def main():
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
```

### 5.8 退出流程

```python
def quit_app(self):
    from app.config import save_config
    self.config["x"] = self.x()
    self.config["y"] = self.y()
    save_config(self.config)
    QApplication.quit()
```

---

## 六、驗收標準

完成第 1 步後，逐項檢查：

- [ ] 晴兒顯示正常，背景透明，無黑底或白底。
- [ ] 晴兒永遠置頂，切換到其他視窗仍然可見。
- [ ] 晴兒不顯示在工作列。
- [ ] 左鍵拖拽跟手，放開後位置固定。
- [ ] 右鍵選單可用：顯示/隱藏、鎖定、置頂、縮放、退出。
- [ ] 系統托盤圖示顯示，右鍵選單可用。
- [ ] 點擊托盤圖示可切換顯示/隱藏。
- [ ] 關閉程式再開，晴兒回到上次的位置。
- [ ] `config.json` 正確寫入位置、縮放、透明度、置頂、鎖定。
- [ ] 多螢幕環境下，晴兒不會跑到螢幕外。
- [ ] 高 DPI 環境下，晴兒大小正常，不模糊。
- [ ] 退出後無殘留進程。

---

## 七、常見問題與提醒

1. **圖片載入失敗**：確認 `文檔/晴兒.png` 存在，且路徑用 `Path` 拼接，不要寫死反斜杠。
2. **背景不透明**：確認同時設定了 `WA_TranslucentBackground` 和 `WA_NoSystemBackground`。
3. **窗口一閃就消失**：確認 `QApplication.setQuitOnLastWindowClosed(False)`，托盤程式不應因關窗而退出。
4. **托盤圖示不顯示**：確認 `圖標/tray.png` 存在；若不存在，用系統標準圖示代替。
5. **拖拽跳位**：確認 `_drag_offset` 用的是 `globalPosition()` 而非 `position()`。
6. **多螢幕跑丟**：啟動時檢查保存的 `x, y` 是否在任何螢幕的工作區內，否則回到主螢幕中央。
7. **快捷鍵衝突**：第一版不加全域快捷鍵，等第 3 步再考慮。
8. **不要提前做動畫**：第 1 步只顯示靜態圖片，動畫留到第 2 步。

---

## 八、完成後

第 1 步完成後，執行：
```bash
git add .
git commit -m "step1: 項目骨架 + 透明置頂窗口 + 托盤 + 配置"
```

然後進入第 2 步：`docs/step2_動畫與行為.md`。

---

**文件版本**：v1.0  
**對應需求**：桌面伴侶需求文檔 v2.1  
**最後更新**：2026-09-10