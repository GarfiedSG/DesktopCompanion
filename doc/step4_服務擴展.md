# 第 4 步：服務框架 + 三個擴展功能

## 一、目標

建立可插拔的 Service 框架，並接入三個擴展功能：定時關機、每日粵語問候、動態桌面壁紙。所有擴展獨立可開關，移除任何擴展都不影響晴兒核心。

完成後，你應該看到：
- 設置窗口「擴展」頁有三個獨立區塊，各自可啟用/停用。
- 定時關機到點彈出倒計時，可取消。
- 每日首次啟動 5 分鐘後，晴兒顯示粵語問候並播放 TTS。
- 動態壁紙可啟停（Windows 優先，其他平台降級為靜態）。

---

## 二、對應需求

- 3.3 擴展服務（全部）
- 3.3.1 ShutdownService 定時關機
- 3.3.2 GreetingService 每日粵語問候
- 3.3.3 WallpaperService 動態桌面壁紙
- 5.4 服務管理

---

## 三、要建立的檔案與結構

```text
桌面伴侶/
├─ app/
│  ├─ service_manager.py
│  └─ services/
│     ├─ __init__.py
│     ├─ base.py
│     ├─ shutdown_service.py
│     ├─ greeting_service.py
│     └─ wallpaper_service.py
├─ greeting_cache.json
├─ greeting_local.json
└─ cache/
   └─ greeting_YYYYMMDD.mp3
```

---

## 四、Service 框架

### 4.1 BaseService

```python
class BaseService:
    def start(self):
        """啟動服務。"""
        pass

    def stop(self):
        """停止服務。"""
        pass

    def apply_config(self, cfg):
        """套用新設定。"""
        pass

    def settings_schema(self) -> list:
        """回傳設置表單的描述，供設置窗口動態生成。"""
        return []
```

### 4.2 ServiceManager

```python
class ServiceManager:
    def __init__(self):
        self.services = {}

    def register(self, name, service):
        self.services[name] = service

    def start_all(self):
        for s in self.services.values():
            s.start()

    def stop_all(self):
        for s in self.services.values():
            s.stop()

    def apply_config(self, cfg):
        for s in self.services.values():
            s.apply_config(cfg)

    def get(self, name):
        return self.services.get(name)
```

### 4.3 設置窗口動態表單

設置窗口「擴展」頁遍歷每個 Service 的 `settings_schema()`，根據描述動態生成表單控件。

Schema 格式建議：

```python
[
    {"key": "shutdown_enabled", "type": "bool", "label": "啟用定時關機", "default": False},
    {"key": "shutdown_time", "type": "time", "label": "關機時間", "default": "23:00"},
    {"key": "shutdown_countdown", "type": "int", "label": "倒計時秒數", "default": 60},
]
```

支援型別：`bool`、`int`、`time`、`str`、`path`、`choice`。

---

## 五、ShutdownService 定時關機

### 5.1 功能
- 到達設定時間，彈出 60 秒倒計時。
- 倒計時期間可取消。
- 倒計時結束執行系統關機。
- 托盤通知提示。

### 5.2 設定項
- `shutdown_enabled`：啟用
- `shutdown_time`：關機時間（HH:MM）
- `shutdown_countdown`：倒計時秒數（預設 60）
- `shutdown_repeat`：是否每天重複

### 5.3 邏輯

```text
QTimer 每 30 秒檢查
  ↓
當前時間 >= shutdown_time？
  ├─ 否 → 繼續等待
  └─ 是 → 檢查今日是否已執行
            ├─ 是 → 跳過
            └─ 否 → 彈出倒計時對話框
                     ↓
                   用戶取消？
                     ├─ 是 → 取消，記錄已處理
                     └─ 否 → 倒計時結束執行關機
```

### 5.4 系統命令

Windows：
```bash
shutdown /s /t 60
shutdown /a        # 取消
```

macOS：
```bash
sudo shutdown -h +1
sudo killall shutdown   # 取消（視情況）
```

Linux：
```bash
shutdown -h +1
shutdown -c             # 取消
```

### 5.5 關鍵代碼

```python
import subprocess
import sys
from datetime import datetime
from PySide6.QtCore import QObject, QTimer


class ShutdownService(BaseService):
    def __init__(self, config, tray=None, audio=None):
        self.config = config
        self.tray = tray
        self.audio = audio
        self.last_fired_date = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._check)
        self.countdown_seconds = 60

    def start(self):
        self.timer.start(30_000)

    def stop(self):
        self.timer.stop()

    def apply_config(self, cfg):
        self.config = cfg

    def _check(self):
        if not self.config.get("shutdown_enabled"):
            return
        target = self.config.get("shutdown_time", "23:00")
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        if self.last_fired_date == today:
            return

        hh, mm = map(int, target.split(":"))
        if now.hour == hh and now.minute == mm:
            self.last_fired_date = today
            self._start_countdown()

    def _start_countdown(self):
        self.countdown_seconds = self.config.get("shutdown_countdown", 60)
        self._notify("定時關機", f"{self.countdown_seconds} 秒後關機")
        # 這裡用 QDialog 或 QMessageBox 顯示倒計時，可取消
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox()
        box.setWindowTitle("定時關機")
        box.setText(f"{self.countdown_seconds} 秒後將關機，是否取消？")
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Cancel)

        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(lambda: self._tick(box))
        self._countdown_timer.start(1000)
        box.exec()

    def _tick(self, box):
        self.countdown_seconds -= 1
        if self.countdown_seconds <= 0:
            self._countdown_timer.stop()
            box.accept()
            self._do_shutdown()
        else:
            box.setText(f"{self.countdown_seconds} 秒後將關機，是否取消？")

    def _do_shutdown(self):
        if sys.platform.startswith("win"):
            subprocess.Popen("shutdown /s /t 0", shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen("sudo shutdown -h now", shell=True)
        else:
            subprocess.Popen("shutdown -h now", shell=True)

    def _notify(self, title, msg):
        if self.tray:
            self.tray.showMessage(title, msg)
```

### 5.6 驗收
- 到點彈出倒計時對話框。
- 可取消，取消後當天不再觸發。
- 不取消則執行關機命令（測試時可把命令改為 `echo`）。
- 托盤有通知。

---

## 六、GreetingService 每日粵語問候

### 6.1 功能
- 每日首次啟動後 5 分鐘觸發。
- 當日已觸發則跳過。
- 格式：`你好，今日係{日期}，{星期}。{治愈溫馨句子}`
- 可聯網生成（Gemini 免費層）或本地句子庫。
- 生成粵語 TTS 並播放。
- 氣泡/托盤通知顯示。
- 緩存保留最近 7 天。

### 6.2 設定項
- `greeting_enabled`：啟用
- `greeting_delay_minutes`：啟動後延遲（預設 5）
- `greeting_online`：是否聯網生成
- `greeting_fallback_local`：聯網失敗回退本地
- `greeting_tts`：是否播放 TTS
- `greeting_bubble`：是否顯示氣泡
- `greeting_gemini_api_key`：API Key
- `greeting_gemini_model`：`gemini-2.5-flash`

### 6.3 觸發流程

```text
程序啟動
  ↓
啟動 5 分鐘計時器
  ↓
5 分鐘後檢查：今日是否已問候？
  ├─ 是 → 跳過
  └─ 否 → 檢查「是否聯網生成」開關
            ├─ 開 → 調用 Gemini 免費層生成
            │        ├─ 成功 → 使用生成句子
            │        └─ 失敗/超時 → 回退本地句子庫
            └─ 關 → 直接使用本地句子庫
  ↓
組合完整問候
  ↓
TTS 生成粵語 mp3（若啟用）
  ↓
氣泡 / 托盤通知 + 播放
  ↓
寫入緩存
```

### 6.4 問候組合

```python
from datetime import datetime

def build_greeting(warm_sentence: str) -> str:
    now = datetime.now()
    date_text = f"{now.year}年{now.month}月{now.day}日"
    weekday_map = ["星期一", "星期二", "星期三", "星期四",
                   "星期五", "星期六", "星期日"]
    weekday = weekday_map[now.weekday()]
    return f"你好，今日係{date_text}，{weekday}。{warm_sentence}"
```

### 6.5 Gemini 聯網生成

```python
import json
import urllib.request

def generate_with_gemini(api_key, model, date_text, weekday):
    prompt = f"""請用香港粵語口語寫一句治癒、溫馨、正向的短句，適合每日早晨問候。

要求：
1. 長度 15–35 字。
2. 用粵語口語用字，例如：係、唔、嘅、啲、咗、喺。
3. 語氣溫暖、輕鬆、有陪伴感。
4. 不要表情符號、不要政治、醫療、投資建議。
5. 不要重複以往句子。
6. 直接輸出句子，不要解釋。

今天是 {date_text}，{weekday}。"""

    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{model}:generateContent?key={api_key}")
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
```

### 6.6 本地回退

`greeting_local.json`：

```json
{
  "sentences": [
    "今日都要對自己好啲，唔好逼得太緊。",
    "慢慢嚟，唔使急，最緊要舒服。",
    "記得飲多啲水，照顧好自己。",
    "今日嘅你都已經好努力，畀個讚自己。",
    "無論今日點，聽日都會有陽光。",
    "深呼吸一下，一切都會慢慢變好。",
    "畀自己一個微笑，今日會更好。",
    "唔使同人比較，你已經喺自己嘅節奏上。"
  ]
}
```

```python
import json
import random
from pathlib import Path

def pick_local():
    path = Path("greeting_local.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return random.choice(data["sentences"])
    return "今日都要對自己好啲。"
```

### 6.7 TTS 生成與播放

```python
import asyncio
import subprocess
from pathlib import Path

def generate_tts(text: str, out_path: Path):
    """用 edge-tts 生成粵語 mp3。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "edge-tts",
        "--voice", "zh-HK-HiuMaanNeural",
        "--text", text,
        "--write-media", str(out_path),
    ], check=True)
```

播放時用 `AudioManager.play_voice(str(out_path))`。

### 6.8 緩存與清理

`greeting_cache.json`：

```json
{
  "2026-09-10": {
    "date_text": "2026年9月10日",
    "weekday": "星期四",
    "warm_sentence": "今日都要對自己好啲，慢慢嚟，一切都會好起來。",
    "full_text": "你好，今日係2026年9月10日，星期四。今日都要對自己好啲，慢慢嚟，一切都會好起來。",
    "audio": "cache/greeting_20260910.mp3",
    "played": true
  }
}
```

清理策略：保留最近 7 天，程式啟動時執行一次。

```python
import json
from datetime import datetime, timedelta
from pathlib import Path

CACHE_PATH = Path("greeting_cache.json")
KEEP_DAYS = 7

def cleanup_cache():
    if not CACHE_PATH.exists():
        return
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        CACHE_PATH.write_text("{}", encoding="utf-8")
        return

    cutoff = (datetime.now() - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    cleaned = {k: v for k, v in data.items() if k >= cutoff}

    if len(cleaned) != len(data):
        CACHE_PATH.write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
```

### 6.9 氣泡顯示

可在晴兒旁邊彈出一個無邊框小氣泡，顯示問候文字，3–5 秒後淡出。

```python
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation

class GreetingBubble(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background: rgba(255, 255, 255, 230);
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 14px;
            color: #333;
        """)
        self.setWordWrap(True)
        self.setMaximumWidth(320)

    def show_near(self, pet_window, duration=5000):
        self.adjustSize()
        self.move(pet_window.x() + pet_window.width() + 10, pet_window.y())
        self.show()
        QTimer.singleShot(duration, self.close)
```

### 6.10 驗收
- 首次啟動 5 分鐘後觸發問候。
- 當日不重複觸發。
- 格式正確：`你好，今日係YYYY年M月D日，星期X。+治愈句子`。
- 「是否聯網生成」開啟時調用 Gemini；關閉時用本地庫。
- 聯網失敗自動回退本地。
- 粵語 TTS 可播放，全局靜音時不播。
- 緩存只保留最近 7 天。

---

## 七、WallpaperService 動態桌面壁紙

### 7.1 功能
- 靜態壁紙 / 幻燈片：跨平台支援。
- 動態視頻壁紙：Windows 優先，其他平台降級。
- 可設定路徑、靜音、循環、多螢幕策略、開機自動播放。

### 7.2 設定項
- `wallpaper_enabled`：啟用
- `wallpaper_mode`：`static` / `slideshow` / `video`
- `wallpaper_path`：檔案或資料夾路徑
- `wallpaper_muted`：視頻是否靜音
- `wallpaper_loop`：是否循環
- `wallpaper_interval`：幻燈片切換間隔（秒）

### 7.3 靜態壁紙（跨平台）

Windows：
```python
import ctypes

def set_wallpaper_windows(path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path), 3)
```

macOS：
```python
import subprocess

def set_wallpaper_macos(path):
    script = f'''
    tell application "System Events"
        tell every desktop
            set picture to "{path}"
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
```

Linux：
依桌面環境不同，GNOME 用 `gsettings`，KDE 用 `qdbus`。

```python
def set_wallpaper_linux(path):
    subprocess.run([
        "gsettings", "set", "org.gnome.desktop.background",
        "picture-uri", f"file://{path}"
    ])
```

### 7.4 動態壁紙（Windows 優先）

Windows 動態壁紙用 `WorkerW` 嵌入 `QMediaPlayer`：

```python
import ctypes
from ctypes import wintypes

def find_workerw():
    """找到 WorkerW 窗口句柄。"""
    user32 = ctypes.windll.user32
    progman = user32.FindWindowW("Progman", None)
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)

    workerw = wintypes.HWND()

    def enum_cb(hwnd, lparam):
        p = ctypes.create_unicode_buffer(256)
        user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
            workerw.value = user32.FindWindowExW(None, hwnd, "WorkerW", None)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return workerw.value
```

然後把 `QMediaPlayer` 的 `QVideoWidget` 設為 WorkerW 的子窗口：

```python
video_widget.winId()  # 取得窗口句柄
ctypes.windll.user32.SetParent(int(video_widget.winId()), workerw)
```

其他平台：
- 先降級為靜態壁紙或幻燈片。
- 提示用戶該平台暫不支援動態壁紙。

### 7.5 驗收
- 靜態壁紙可設定，立即生效。
- 幻燈片按間隔切換。
- Windows 動態壁紙可播放，可停止。
- 其他平台降級為靜態壁紙，不報錯。
- 視頻靜音選項生效。
- 多螢幕策略正確。

---

## 八、設置窗口「擴展」頁

用 `QGroupBox` 分三塊：

### 8.1 定時關機
- 啟用開關
- 關機時間（`QTimeEdit`）
- 倒計時秒數（`QSpinBox`）
- 每天重複開關

### 8.2 每日粵語問候
- 啟用開關
- 啟動後延遲分鐘（`QSpinBox`）
- **是否聯網生成問候**（開關）
- 本地句子庫回退（開關）
- 粵語 TTS（開關）
- 氣泡顯示（開關）
- Gemini API Key（密碼輸入框）
- 試聽按鈕
- 立即生成一次（測試用）

**當「是否聯網生成問候」關閉時**：
- 不調用 Gemini API
- 直接使用本地句子庫
- Gemini API Key 輸入框變灰

### 8.3 動態桌面壁紙
- 啟用開關
- 模式選擇：靜態 / 幻燈片 / 視頻
- 路徑選擇
- 靜音開關
- 循環開關
- 幻燈片間隔（秒）
- 應用按鈕
- 停止按鈕

---

## 九、config.json 更新

在第 3 步基礎上加入：

```json
{
  "shutdown_enabled": false,
  "shutdown_time": "23:00",
  "shutdown_countdown": 60,
  "shutdown_repeat": true,
  "greeting_enabled": false,
  "greeting_delay_minutes": 5,
  "greeting_online": true,
  "greeting_fallback_local": true,
  "greeting_tts": true,
  "greeting_bubble": true,
  "greeting_gemini_api_key": "",
  "greeting_gemini_model": "gemini-2.5-flash",
  "wallpaper_enabled": false,
  "wallpaper_mode": "static",
  "wallpaper_path": "",
  "wallpaper_muted": true,
  "wallpaper_loop": true,
  "wallpaper_interval": 30
}
```

---

## 十、驗收標準

完成第 4 步後，逐項檢查：

- [ ] 三個 Service 各自獨立可啟用/停用。
- [ ] 移除任一 Service，晴兒核心不受影響。
- [ ] 定時關機到點彈出倒計時，可取消。
- [ ] 定時關機托盤有通知。
- [ ] 每日問候首次啟動 5 分鐘後觸發。
- [ ] 當日不重複觸發。
- [ ] 問候格式正確。
- [ ] 「是否聯網生成」開關生效，關閉時不發網絡請求。
- [ ] 聯網失敗自動回退本地句子庫。
- [ ] 粵語 TTS 可播放，全局靜音時不播。
- [ ] 緩存只保留最近 7 天。
- [ ] 靜態壁紙可設定。
- [ ] Windows 動態壁紙可播放可停止。
- [ ] 其他平台動態壁紙降級為靜態，不報錯。
- [ ] 所有設定即時生效並持久化。

---

## 十一、常見問題與提醒

1. **關機命令測試**：先把 `_do_shutdown` 改成 `print`，確認倒計時邏輯正確再啟用真實命令。
2. **Gemini API Key 安全**：不要硬編碼，存 `config.json`，提示用戶自行填入。
3. **Gemini 免費層隱私**：免費層數據可能被 Google 用於模型改進。設置窗口加提示文字。
4. **TTS 依賴**：`edge-tts` 需要網絡，離線時回退到不播放或系統 TTS。
5. **動態壁紙兼容性**：Windows 優先，其他平台先降級，不要強行支援。
6. **緩存目錄**：`cache/` 目錄若不存在，生成 TTS 前先 `mkdir(parents=True, exist_ok=True)`。
7. **Service 生命週期**：`stop_all()` 要在程式退出時呼叫，避免殘留 timer。
8. **設置窗口動態表單**：若 schema 太複雜，可先寫死表單，schema 留作後續優化。
9. **氣泡位置**：氣泡要跟隨晴兒移動，或至少在顯示時對齊晴兒位置。
10. **不要提前做第 5 步**：優化、打包、測試留到第 5 步。

---

## 十二、完成後

第 4 步完成後，執行：
```bash
git add .
git commit -m "step4: 服務框架 + 定時關機 + 粵語問候 + 動態壁紙"
```

然後進入第 5 步：`docs/step5_優化打包.md`。

---

**文件版本**：v1.0  
**對應需求**：桌面伴侶需求文檔 v2.1  
**最後更新**：2026-09-10