```markdown
# 桌面伴侶 — 晴兒

一個以 Python + PySide6 開發的桌面寵物應用，寵物名為「晴兒」。
晴兒會待在桌面上，透明置頂、可拖拽、會呼吸、會隨機切換待機動畫，並支援定時關機、每日粵語問候、動態桌面壁紙等擴展功能。

---

## 功能特色

### 核心
- **透明置頂窗口**：無邊框、背景透明、永遠置頂、不顯示在工作列。
- **基礎互動**：左鍵拖拽、單擊反應、右鍵選單、系統托盤。
- **動畫狀態機**：待機、點擊、拖拽三種狀態，切換自然。
- **動畫自動掃描**：`文檔/animations/idle/` 下所有子資料夾自動識別，無需手動維護清單，也無需重新編譯。
- **每個動畫獨立配置**：每個動畫資料夾內的 `anim.json` 控制名稱、啟用、權重、是否移動等。
- **隨機待機**：啟動後與拖拽釋放後，都從所有啟用動畫中隨機選擇一個。
- **權重規則**：`anim.json` 中的 `weight` 值**越小，權重越高**（weight=1 比 weight=3 更常出現）。
- **持續時間**：同一待機動畫至少持續 1 分鐘（拖拽動畫除外）。
- **拖拽停留**：拖拽晴兒到新位置放開後，晴兒停留在新位置，不回到原位。
- **附帶移動**：特定待機動畫（`move=true`）在限定範圍內來回移動，以當前位置為新起點。

### 設置窗口
- **常規**：開機啟動、顯示托盤、語言、退出確認。
- **外觀**：縮放、透明度、置頂、鎖定、FPS、動畫速度。
- **互動**：點擊穿透、拖拽、雙擊隱藏、右鍵選單。
- **待機動畫管理**：導入資料夾或多張圖片，自動排序、重命名、生成 `anim.json`。
- **聲音**：全局靜音開關 + 分類開關（點擊、拖拽、走動、問候、關機提示），不設音量調節。
- **擴展**：定時關機、每日粵語問候、動態桌面壁紙。
- **關於**：版本、配置路徑、重置設定。

### 擴展功能
- **定時關機**：到達設定時間彈出 60 秒倒計時，可取消。
- **每日粵語問候**：每日首次啟動 5 分鐘後觸發，格式為「你好，今日係{日期}，{星期}。{治愈溫馨句子}」。句子可聯網生成（Gemini 免費層）或使用本地句子庫，支援粵語 TTS。
- **動態桌面壁紙**：Windows 優先支援視頻壁紙，其他平台降級為靜態壁紙或幻燈片。

---

## 技術棧

| 項目 | 內容 |
| :--- | :--- |
| 語言 | Python 3.11+ |
| GUI | PySide6 |
| 配置 | JSON |
| 打包 | PyInstaller |
| TTS | edge-tts（粵語：`zh-HK-HiuMaanNeural`） |
| 圖片處理 | Pillow |
| 聯網生成 | Google Gemini 免費層（`gemini-2.5-flash`） |

---

## 專案結構

```text
桌面伴侶/
├─ main.py
├─ config.json
├─ greeting_cache.json
├─ greeting_local.json
├─ app/
│  ├─ config.py
│  ├─ service_manager.py
│  ├─ audio_manager.py
│  ├─ ui/
│  │  ├─ pet_window.py
│  │  ├─ settings_window.py
│  │  └─ tray.py
│  ├─ core/
│  │  ├─ animation.py
│  │  ├─ behavior.py
│  │  ├─ animation_library.py
│  │  ├─ idle_scheduler.py
│  │  └─ idle_importer.py
│  └─ services/
│     ├─ base.py
│     ├─ autostart_service.py
│     ├─ shutdown_service.py
│     ├─ greeting_service.py
│     └─ wallpaper_service.py
├─ 文檔/
│  ├─ 晴兒.png
│  └─ animations/
│     └─ idle/
│        ├─ idle_standing/
│        │  ├─ anim.json
│        │  ├─ frame_000.png
│        │  └─ ...
│        ├─ idle_walking/
│        │  ├─ anim.json
│        │  ├─ frame_000.png
│        │  └─ ...
│        └─ idle_cat/
│           ├─ anim.json
│           ├─ frame_000.png
│           └─ ...
├─ 音效/
│  ├─ click.wav
│  ├─ drag.wav
│  ├─ walk.wav
│  ├─ greeting.mp3
│  └─ shutdown.wav
├─ 圖標/
│  ├─ tray.png
│  └─ tray_mute.png
└─ docs/
   ├─ 需求文檔.md
   ├─ step1_骨架與窗口.md
   ├─ step2_動畫與行為.md
   ├─ step3_設置與聲音.md
   ├─ step4_服務擴展.md
   ├─ step5_優化打包.md
   └─ 給Windsurf的提示詞.md
```

---

## 安裝

### 1. 複製專案

```bash
git clone <your-repo-url> 桌面伴侶
cd 桌面伴侶
```

### 2. 建立虛擬環境（建議）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. 安裝依賴

```bash
pip install PySide6 edge-tts pillow
```

### 4. 準備素材

- 將晴兒的圖片放入 `文檔/晴兒.png`。
- 將待機動畫放入 `文檔/animations/idle/<動畫名>/`，每個資料夾內包含：
  - `anim.json`（可選，若無則用預設值）
  - `frame_000.png`、`frame_001.png`…（至少一張）
- 將音效放入 `音效/`。
- 將托盤圖示放入 `圖標/`。

---

## 運行

```bash
python main.py
```

啟動後，晴兒會出現在桌面上。系統托盤會出現圖示，可從托盤右鍵選單打開設置或退出。

---

## 使用方式

### 滑鼠操作
- **左鍵拖拽**：移動晴兒。放開後停留在新位置。
- **左鍵單擊**：播放點擊反應動畫。
- **右鍵單擊**：打開右鍵選單。
- **滾輪**：縮放（可選）。

### 托盤選單
- 顯示/隱藏晴兒
- 靜音開關
- 打開設置
- 退出

### 設置窗口
從托盤選單打開「設置」，可調整外觀、互動、行為、待機動畫、聲音與擴展功能。所有設定即時生效並自動保存。

### 新增待機動畫
1. 在 `文檔/animations/idle/` 下建立一個新資料夾，例如 `idle_reading/`。
2. 放入 `frame_000.png`、`frame_001.png`…（至少一張）。
3. 可選：建立 `anim.json` 設定名稱、啟用、權重、是否移動等。
   ```json
   {
     "name": "看書",
     "enabled": true,
     "weight": 1,
     "move": false,
     "move_speed": 4,
     "move_range": 200
   }
   ```
4. 重啟程式，晴兒就會隨機切換到這個新動畫，無需重新編譯。

### 暫時關閉某動畫
將該動畫資料夾內的 `anim.json` 中 `enabled` 設為 `false`，例如：
```json
{
  "name": "走動",
  "enabled": false,
  "weight": 1,
  "move": true,
  "move_speed": 4,
  "move_range": 200
}
```
重啟程式後，該動畫不會被選中。

### 調整動畫出現頻率
`anim.json` 中的 `weight` 值**越小，權重越高**。例如：
- `weight: 1` 的動畫會比 `weight: 3` 的動畫更常出現。
- 想讓某動畫少出現，把 `weight` 設大，例如 `5` 或 `10`。

---

## 開發

本專案採用五步開發流程，詳細步驟見 `docs/` 目錄：

1. **第 1 步**：項目骨架 + 透明置頂窗口 + 托盤 + 配置
2. **第 2 步**：動畫狀態機 + 待機行為（動畫自動掃描、隨機調度、拖拽停留）
3. **第 3 步**：設置窗口 + 待機動畫管理 + 聲音
4. **第 4 步**：服務框架 + 定時關機 + 粵語問候 + 動態壁紙
5. **第 5 步**：優化 + 打包 + 測試 + 交付

建議使用 Windsurf 作為主力開發工具，並搭配 `.windsurfrules` 與 `docs/給Windsurf的提示詞.md` 逐步實現。

---

## 打包

### PyInstaller

```bash
pyinstaller --noconsole --add-data "文檔;文檔" --add-data "音效;音效" --add-data "圖標;圖標" main.py
```

macOS / Linux 請將 `;` 改為 `:`：

```bash
pyinstaller --noconsole --add-data "文檔:文檔" --add-data "音效:音效" --add-data "圖標:圖標" main.py
```

打包後的執行檔在 `dist/` 目錄下。

**注意**：打包後 `config.json`、`greeting_cache.json`、`cache/` 應寫入用戶目錄（例如 `~/.desktop_pet/`），不要寫在程式目錄。

---

## 開機啟動

- **Windows**：寫入註冊表 `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`。
- **macOS**：建立 `~/Library/LaunchAgents/com.desktop.pet.plist`。
- **Linux**：建立 `~/.config/autostart/desktop-pet.desktop`。

設置窗口「常規」頁提供開機啟動開關。

---

## 常見問題

**Q：晴兒背景不透明，有黑底或白底？**  
A：確認窗口同時設定了 `WA_TranslucentBackground` 與 `WA_NoSystemBackground`。

**Q：托盤圖示不顯示？**  
A：確認 `圖標/tray.png` 存在；若不存在，程式會使用系統標準圖示。

**Q：新增待機動畫後沒有生效？**  
A：確認動畫資料夾放在 `文檔/animations/idle/` 下，且內含至少一張 `frame_*.png`。重啟程式後應自動掃描到。

**Q：拖拽晴兒後，她回到了原位？**  
A：確認 `stop_idle_move()` 沒有傳入 `restore_origin=True`，且 `start_idle_move()` 以當前位置為新起點。拖拽釋放後應停留在新位置。

**Q：粵語問候沒有聲音？**  
A：確認全域靜音未開啟，且「粵語問候語音」分類開關已啟用。`edge-tts` 需要網絡。

**Q：動態壁紙在 macOS / Linux 無法使用？**  
A：動態壁紙目前以 Windows 優先，其他平台會降級為靜態壁紙或幻燈片。

**Q：打包後程式無法寫入 config？**  
A：打包後程式目錄可能唯讀，請將 config 與 cache 寫到 `Path.home() / ".desktop_pet"`。

---

## 授權

本專案為個人專案，可自由使用與修改。若需商用，請自行確認相關素材與依賴的授權。

---

## 致謝

- [PySide6](https://doc.qt.io/qtforpython/)：Qt for Python
- [edge-tts](https://github.com/rany2/edge-tts)：微軟 Edge TTS 封裝
- [Pillow](https://python-pillow.org/)：Python 圖片處理
- [Google Gemini](https://ai.google.dev/)：免費層 LLM API

---

**版本**：v2.3  
**最後更新**：2026-09-14  
**狀態**：需求凍結，可進入開發
```