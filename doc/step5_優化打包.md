# 第 5 步：優化、打包、測試、交付

## 一、目標

低佔用、可安裝、可開機啟動、穩定交付。完成後，晴兒可以打包成獨立安裝包，用戶雙擊即可使用。

完成後，你應該看到：
- 空閒時 CPU 佔用低，筆電不明顯耗電。
- 視窗不可見時停止渲染，不浪費資源。
- 打包成單一執行檔或安裝包，雙擊可運行。
- 可設定開機啟動，登入系統後晴兒自動出現。
- 長時間運行穩定，退出無殘留進程。

---

## 二、對應需求

- 3.4 優化與打包
- 3.2.1 常規（開機啟動）
- 七、測試清單（全部）

---

## 三、性能優化

### 3.1 視窗不可見時停止渲染

當晴兒被隱藏或最小化時，停止動畫更新與行為調度，避免無謂的 CPU 消耗。

```python
def hideEvent(self, event):
    self.scheduler.pause()
    self.anim_timer.stop()
    super().hideEvent(event)

def showEvent(self, event):
    self.scheduler.resume()
    self.anim_timer.start(1000 // self.config["fps"])
    super().showEvent(event)
```

### 3.2 限制 FPS

- 待機時可用 15 FPS，走動時用 30 FPS，拖拽時用 60 FPS。
- 根據當前狀態動態調整 `QTimer` 間隔。

```python
def _update_fps(self):
    state = self.state_machine.state
    fps_map = {"Idle": 15, "Walk": 30, "Click": 30, "Drag": 60}
    fps = fps_map.get(state, 30)
    self.anim_timer.setInterval(1000 // fps)
```

### 3.3 資源快取

- 所有 `QPixmap` 只載入一次，用 dict 快取。
- `QSoundEffect` 用 dict 快取，不要每次播放都新建。
- 序列帧載入時統一縮放到合理尺寸（最長邊 512–1024 px）。

```python
class ResourceCache:
    def __init__(self):
        self._pixmaps = {}
        self._sounds = {}

    def get_pixmap(self, path):
        if path not in self._pixmaps:
            self._pixmaps[path] = QPixmap(str(path))
        return self._pixmaps[path]

    def get_sound(self, path):
        if path not in self._sounds:
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(DEFAULT_VOLUME)
            self._sounds[path] = effect
        return self._sounds[path]
```

### 3.4 減少透明重繪

- 只在必要時 `update()`，不要每幀都強制重繪。
- 背景透明區域使用 `WA_TranslucentBackground`，避免不必要的合成。
- 交叉淡化結束後，隱藏舊圖層，避免持續繪製。

### 3.5 空閒時降低更新頻率

- 若晴兒連續 30 秒無互動且處於 Idle，可降到 10 FPS。
- 若系統進入省電模式，暫停非必要更新。

### 3.6 記憶體管理

- 定期清理不再使用的序列帧快取。
- 切換待機動畫時，若舊動畫短期內不會再用，可釋放其 `QPixmap`。
- 用 `weakref` 或 LRU 快取避免記憶體無限增長。

---

## 四、打包

### 4.1 PyInstaller 基本指令

```bash
pyinstaller --noconsole --add-data "文檔;文檔" --add-data "音效;音效" --add-data "圖標;圖標" main.py
```

macOS / Linux 用冒號分隔：

```bash
pyinstaller --noconsole --add-data "文檔:文檔" --add-data "音效:音效" --add-data "圖標:圖標" main.py
```

### 4.2 建議的 `.spec` 檔案

```python
# desktop_pet.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('文檔', '文檔'),
        ('音效', '音效'),
        ('圖標', '圖標'),
        ('greeting_local.json', '.'),
    ],
    hiddenimports=[
        'PySide6.QtMultimedia',
        'PySide6.QtNetwork',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='桌面伴侶',
    console=False,
    icon='圖標/app.ico',
)
```

用 spec 打包：

```bash
pyinstaller desktop_pet.spec
```

### 4.3 圖示與版本資訊

- Windows：用 `.ico` 格式。
- macOS：用 `.icns` 格式。
- 版本資訊可在 spec 中設定 `version_info`。

### 4.4 打包後測試

- 在乾淨的機器或虛擬機上測試。
- 確認 `文檔/晴兒.png`、`音效/`、`圖標/` 都能正確載入。
- 確認 `config.json` 能寫入（不要寫在程式目錄，應寫在用戶目錄）。

**重要**：打包後程式目錄可能唯讀，`config.json`、`greeting_cache.json`、`cache/` 應寫到用戶目錄：

```python
from pathlib import Path

APP_DIR = Path.home() / ".desktop_pet"
APP_DIR.mkdir(exist_ok=True)
CONFIG_PATH = APP_DIR / "config.json"
CACHE_PATH = APP_DIR / "greeting_cache.json"
```

---

## 五、開機啟動

### 5.1 Windows

用註冊表 `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`：

```python
import sys
import winreg

def enable_autostart_windows():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE,
    )
    exe_path = sys.executable
    winreg.SetValueEx(key, "DesktopPet", 0, winreg.REG_SZ, f'"{exe_path}"')
    winreg.CloseKey(key)

def disable_autostart_windows():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE,
    )
    try:
        winreg.DeleteValue(key, "DesktopPet")
    except FileNotFoundError:
        pass
    winreg.CloseKey(key)
```

### 5.2 macOS

建立 `~/Library/LaunchAgents/com.desktop.pet.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.desktop.pet</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/桌面伴侶.app/Contents/MacOS/桌面伴侶</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

載入：

```bash
launchctl load ~/Library/LaunchAgents/com.desktop.pet.plist
```

### 5.3 Linux

建立 `~/.config/autostart/desktop-pet.desktop`：

```ini
[Desktop Entry]
Type=Application
Name=桌面伴侶
Exec=/opt/desktop-pet/桌面伴侶
X-GNOME-Autostart-enabled=true
```

### 5.4 AutostartService

做成獨立 Service，設置窗口「常規」頁的開機啟動開關接入：

```python
class AutostartService(BaseService):
    def start(self):
        pass

    def stop(self):
        pass

    def apply_config(self, cfg):
        enabled = cfg.get("auto_start", False)
        if enabled:
            self.enable()
        else:
            self.disable()

    def enable(self):
        if sys.platform.startswith("win"):
            enable_autostart_windows()
        elif sys.platform == "darwin":
            self._enable_macos()
        else:
            self._enable_linux()

    def disable(self):
        # 對應移除
        ...
```

---

## 六、測試清單

### 6.1 核心功能
- [ ] 透明置頂正常
- [ ] 點擊穿透正常
- [ ] 拖拽跟手
- [ ] 多螢幕不跑丟
- [ ] 高 DPI 正常
- [ ] 托盤功能完整
- [ ] 設置保存正常

### 6.2 動畫與行為
- [ ] 待機、走動、點擊、拖拽動畫正常
- [ ] 拖拽跟手，放開回 Idle
- [ ] 不同動畫切換有交叉淡化
- [ ] 相同動畫不淡化
- [ ] 長時間循環首尾幀一致

### 6.3 待機動畫管理
- [ ] 導入動畫資料夾成功
- [ ] 導入多張圖片成功
- [ ] 自然排序正確（1, 2, 10）
- [ ] 導入後無需重編譯
- [ ] 隨機切換不頻繁
- [ ] 只有一個動畫時不切換

### 6.4 聲音
- [ ] 全局靜音生效
- [ ] 分類開關保留狀態
- [ ] 托盤與設置窗口同步
- [ ] 音量固定 0.8

### 6.5 擴展功能
- [ ] 定時關機可取消
- [ ] 粵語問候每日一次，可試聽
- [ ] 問候觸發：首次啟動後 5 分鐘
- [ ] 當日不重複
- [ ] 「是否聯網生成」開關生效
- [ ] 聯網失敗自動回退本地
- [ ] 緩存只保留最近 7 天
- [ ] 動態壁紙可啟停（Windows 優先）

### 6.6 性能
- [ ] 空閒 CPU 低於 3%
- [ ] 記憶體穩定，不持續增長
- [ ] 視窗隱藏時停止渲染
- [ ] 筆電不明顯耗電

### 6.7 打包與開機啟動
- [ ] 打包後可獨立運行
- [ ] 圖片、音效、圖標正確載入
- [ ] config 寫入用戶目錄
- [ ] 開機啟動可啟用/停用
- [ ] 退出無殘留進程

### 6.8 跨平台
- [ ] Windows 測試通過
- [ ] macOS 測試通過（若有環境）
- [ ] Linux 測試通過（若有環境）
- [ ] 動態壁紙在非 Windows 降級正常

---

## 七、效能監控

### 7.1 CPU 監控

用系統工作管理員或 `psutil`：

```python
import psutil
import os

def get_cpu_usage():
    p = psutil.Process(os.getpid())
    return p.cpu_percent(interval=1)
```

### 7.2 記憶體監控

```python
def get_memory_usage():
    p = psutil.Process(os.getpid())
    return p.memory_info().rss / 1024 / 1024  # MB
```

### 7.3 長時間運行測試

- 連續運行 24 小時，觀察 CPU、記憶體、溫度。
- 檢查是否有記憶體泄漏。
- 檢查是否有殘留的 QTimer 或 QThread。

---

## 八、交付清單

### 8.1 原始碼
- 完整專案目錄
- `docs/` 下的所有需求與步驟文件
- `.windsurfrules`
- `README.md`（簡要說明）

### 8.2 執行檔
- Windows：`桌面伴侶.exe` 或安裝包
- macOS：`桌面伴侶.app` 或 `.dmg`
- Linux：`桌面伴侶` 執行檔或 `.deb`

### 8.3 素材
- `文檔/晴兒.png`
- `文檔/animations/idle/` 下的待機動畫
- `音效/` 下的音效檔案
- `圖標/` 下的圖示

### 8.4 配置文件
- `config.json` 範本
- `greeting_local.json` 本地句子庫

### 8.5 說明文件
- 安裝說明
- 使用說明
- 常見問題

---

## 九、版本管理

### 9.1 Git 提交規範

```text
step1: 項目骨架 + 透明置頂窗口 + 托盤 + 配置
step2: 動畫狀態機 + 隨機行為
step3: 設置窗口 + 待機動畫管理 + 聲音
step4: 服務框架 + 定時關機 + 粵語問候 + 動態壁紙
step5: 優化 + 打包 + 測試 + 交付
```

### 9.2 版本號

`__version__ = "1.0.0"`

在設置窗口「關於」頁顯示。

### 9.3 標籤

```bash
git tag -a v1.0.0 -m "首個正式版本"
git push origin v1.0.0
```

---

## 十、發布

### 10.1 內部測試
- 自己先用一週，記錄所有問題。
- 修復後再發布。

### 10.2 發布管道
- GitHub Releases
- 個人網站
- 朋友測試

### 10.3 更新機制（可選）
- 啟動時檢查遠端版本號。
- 若有新版本，托盤通知。
- 第一版可先不做自動更新，手動下載替換。

---

## 十一、常見問題與提醒

1. **打包後圖片找不到**：用 `sys._MEIPASS` 取得臨時目錄。
   ```python
   def resource_path(relative):
       if hasattr(sys, "_MEIPASS"):
           return Path(sys._MEIPASS) / relative
       return Path(__file__).parent / relative
   ```
2. **config 寫入失敗**：打包後程式目錄可能唯讀，改用 `Path.home() / ".desktop_pet"`。
3. **PyInstaller 體積過大**：用 `--exclude-module` 排除不需要的模組；或用 `upx` 壓縮。
4. **開機啟動失效**：確認執行檔路徑正確，且用絕對路徑。
5. **macOS 簽名問題**：未簽名的 app 可能被 Gatekeeper 攔截，需公證或提示用戶右鍵開啟。
6. **Linux 依賴**：確認目標系統有 Qt 所需的多媒體庫。
7. **長時間運行崩潰**：檢查是否有未捕獲的異常，加全域 `sys.excepthook`。
8. **退出殘留進程**：確認所有 QTimer、QThread、QMediaPlayer 都正確停止。
9. **不要在最後才測試**：每一步完成都要測試，第 5 步只是最終驗收。
10. **保持文檔同步**：若開發中改了需求，同步更新 `docs/` 下的文件。

---

## 十二、完成後

第 5 步完成後，執行：

```bash
git add .
git commit -m "step5: 優化 + 打包 + 測試 + 交付"
git tag -a v1.0.0 -m "首個正式版本"
```

至此，桌面伴侶五步開發全部完成，晴兒正式上線。

---

**文件版本**：v1.0  
**對應需求**：桌面伴侶需求文檔 v2.1  
**最後更新**：2026-09-10