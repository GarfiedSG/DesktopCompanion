# 第 3 步：設置窗口 + 待機動畫管理 + 聲音

## 一、目標

可視化設置晴兒，設定即時生效並持久化；支援從外部導入待機動畫，無需重新編譯；加入全局靜音與分類開關。

完成後，你應該看到：
- 托盤「設置」可打開設置窗口，分頁完整。
- 改任何設定，晴兒即時反應，重開保留。
- 設置窗口可導入動畫資料夾或多張圖片，自動重命名並加入待機清單。
- 待機動畫隨機切換，間隔可控，相同動畫不淡化。
- 聲音有全局靜音與分類開關，無音量調節。

---

## 二、對應需求

- 3.2 設置窗口（全部子頁）
- 3.2.5 待機動畫管理
- 3.2.6 聲音
- 5.1 交叉淡化實現
- 5.2 自然排序
- 5.3 AudioManager
- 5.4 服務管理（僅建立框架，實際擴展留到第 4 步）
- 5.5 待機動畫導入
- 5.6 待機動畫調度

---

## 三、要建立的檔案與結構

```text
桌面伴侶/
├─ app/
│  ├─ audio_manager.py
│  ├─ service_manager.py
│  ├─ ui/
│  │  └─ settings_window.py
│  └─ core/
│     ├─ idle_scheduler.py
│     └─ idle_importer.py
├─ 文檔/
│  └─ animations/
│     └─ idle/
│        ├─ idle_standing/
│        └─ idle_cat/
├─ 音效/
│  ├─ click.wav
│  ├─ drag.wav
│  ├─ walk.wav
│  ├─ greeting.mp3
│  └─ shutdown.wav
└─ 圖標/
   ├─ tray.png
   └─ tray_mute.png
```

---

## 四、具體任務

### 4.1 設置窗口

用 `QDialog + QTabWidget`，分頁如下：

#### 4.1.1 常規
- 開機啟動
- 顯示托盤
- 語言：繁體中文 / 粵語
- 退出確認

#### 4.1.2 外觀
- 寵物縮放
- 透明度
- 是否置頂
- 是否鎖定位置
- FPS：15 / 30 / 60
- 動畫速度

#### 4.1.3 互動
- 點擊穿透
- 拖拽
- 雙擊隱藏
- 右鍵選單

#### 4.1.4 行為
- 隨機走動開關
- 待機時間範圍
- 走動速度
- 活動範圍
- 邊緣反彈

#### 4.1.5 待機動畫管理
- 見 4.2

#### 4.1.6 聲音
- 見 4.4

#### 4.1.7 擴展
- 定時關機、每日粵語問候、動態壁紙
- 本步驟只顯示佔位，第 4 步接入

#### 4.1.8 關於
- 版本
- 配置路徑
- 重置設定

**流程**：

```text
SettingsWindow.config_changed
  -> ConfigManager.save()
  -> ServiceManager.apply_config()
```

### 4.2 待機動畫管理

#### 4.2.1 列表顯示
- 每個待機動畫顯示名稱與啟用狀態。
- 用 `QListWidget`，每項帶 `Qt.UserRole` 存路徑。

#### 4.2.2 按鈕
- **導入動畫資料夾**：`QFileDialog.getExistingDirectory`，掃描圖片。
- **導入多張圖片**：`QFileDialog.getOpenFileNames`，多選。
- **重新掃描**：掃描 `文檔/animations/idle/` 下所有資料夾。
- **移除選中**：只從清單移除，或同時刪除檔案。
- **啟用/停用**：透過勾選狀態控制。

#### 4.2.3 導入流程

```text
用戶點導入
  ↓
選擇資料夾或多選圖片
  ↓
彈窗輸入動畫名稱（預設用資料夾名）
  ↓
掃描所有圖片，自然排序
  ↓
統一轉為 RGBA PNG
  ↓
複製到 文檔/animations/idle/<動畫名>/
  ↓
重命名為 frame_000.png, frame_001.png ...
  ↓
寫入 config.json
  ↓
刷新設置窗口列表 + 通知調度器
```

#### 4.2.4 重名處理
若目標目錄已存在，彈出三選項：
- 覆蓋
- 重命名（自動加 `_2`）
- 取消

#### 4.2.5 進度反饋
幀數多時用 `QProgressDialog`，支援取消；取消時清理已複製的部分檔案。

### 4.3 待機動畫調度

#### 4.3.1 IdleScheduler

- 從 `config["idle_animations"]` 中篩選 `enabled=True` 的動畫。
- 排除當前動畫，按 `weight` 隨機選擇。
- 隨機間隔 `min_interval` 至 `max_interval` 秒。
- 相同動畫不切換、不淡化。
- 只有一個啟用動畫時不切換。
- 不同動畫切換使用交叉淡化 0.2–0.4 秒。

#### 4.3.2 防止頻繁切換

- `min_interval` 下限 10 秒。
- 每次切換後重新抽下一次時間。
- 拖拽、點擊時暫停調度，放開後重新排程。

### 4.4 聲音

#### 4.4.1 全局靜音與分類開關
- **全局靜音開關**（優先級最高）
- 分類開關：
  - 點擊音效
  - 拖拽音效
  - 走動音效
  - 粵語問候語音
  - 定時關機提示音
- **不設音量調節**，音量固定 `DEFAULT_VOLUME = 0.8`
- 全局靜音時，分類開關變灰但保留狀態

#### 4.4.2 托盤同步
托盤加「靜音」勾選項，與設置窗口雙向同步。

#### 4.4.3 AudioManager
所有聲音播放必須經過 `AudioManager`，不要在各處直接 `new QSoundEffect`。

### 4.5 ServiceManager 框架

本步驟只建立框架，實際擴展留到第 4 步。

```python
class BaseService:
    def start(self): ...
    def stop(self): ...
    def apply_config(self, cfg): ...
    def settings_schema(self) -> list: ...
```

- `ServiceManager` 統一啟動、停止、套用設定。
- 設置窗口「擴展」頁根據 `settings_schema()` 動態生成表單（第 4 步接入）。

### 4.6 多螢幕與 DPI

- 窗口位置限制在工作區內。
- 保存位置時記錄螢幕 ID（可選）。
- 啟動時若保存的位置不在任何螢幕範圍內，回到主螢幕中央。
- 高 DPI 縮放正常。

---

## 五、關鍵代碼要點

### 5.1 AudioManager

```python
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput

DEFAULT_VOLUME = 0.8


class AudioManager(QObject):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._short_effects = {}
        self._player = QMediaPlayer()
        self._audio_out = QAudioOutput()
        self._audio_out.setVolume(DEFAULT_VOLUME)
        self._player.setAudioOutput(self._audio_out)

    def is_muted(self):
        return self.config["audio"]["muted"]

    def set_muted(self, muted):
        self.config["audio"]["muted"] = muted
        if muted:
            self._player.stop()

    def play_sfx(self, category, file_path):
        if self.is_muted():
            return
        if not self.config["audio"].get(category, False):
            return
        effect = self._short_effects.get(file_path)
        if effect is None:
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(file_path))
            effect.setVolume(DEFAULT_VOLUME)
            self._short_effects[file_path] = effect
        effect.play()

    def play_voice(self, file_path):
        if self.is_muted():
            return
        if not self.config["audio"].get("greeting_tts", False):
            return
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self._player.play()

    def stop_all(self):
        self._player.stop()
        for effect in self._short_effects.values():
            effect.stop()
```

### 5.2 自然排序

```python
import re


def natural_key(path):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", path.stem)]
```

### 5.3 導入動畫核心

```python
import shutil
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import (
    QFileDialog, QInputDialog, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class IdleImporter:
    def __init__(self, base_dir: Path, config: dict, on_finished):
        self.base_dir = base_dir
        self.idle_dir = base_dir / "文檔" / "animations" / "idle"
        self.idle_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.on_finished = on_finished

    def import_folder(self, parent_widget):
        folder = QFileDialog.getExistingDirectory(parent_widget, "選擇動畫資料夾")
        if not folder:
            return
        folder = Path(folder)
        files = [f for f in folder.iterdir()
                 if f.is_file() and f.suffix.lower() in SUPPORTED_EXT]
        files.sort(key=natural_key)
        if not files:
            QMessageBox.warning(parent_widget, "提示", "資料夾內沒有支援的圖片。")
            return
        self._do_import(parent_widget, files, folder.name)

    def import_files(self, parent_widget):
        files, _ = QFileDialog.getOpenFileNames(
            parent_widget, "選擇動畫圖片", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not files:
            return
        files = [Path(f) for f in files]
        files.sort(key=natural_key)
        default_name = files[0].parent.name or "新動畫"
        self._do_import(parent_widget, files, default_name)

    def _do_import(self, parent_widget, files, default_name):
        name, ok = QInputDialog.getText(
            parent_widget, "動畫名稱", "請輸入動畫名稱：", text=default_name
        )
        if not ok or not name.strip():
            return
        name = self._sanitize_name(name.strip())

        target = self.idle_dir / name
        if target.exists():
            choice = QMessageBox.question(
                parent_widget, "已存在",
                f"動畫「{name}」已存在，是否覆蓋？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if choice == QMessageBox.Cancel:
                return
            if choice == QMessageBox.No:
                target = self._unique_dir(name)
            else:
                shutil.rmtree(target)

        target.mkdir(parents=True, exist_ok=True)

        progress = QProgressDialog("正在導入...", "取消", 0, len(files), parent_widget)
        progress.setWindowModality(Qt.WindowModal)

        for i, src in enumerate(files):
            if progress.wasCanceled():
                shutil.rmtree(target, ignore_errors=True)
                return
            dst = target / f"frame_{i:03d}.png"
            try:
                with Image.open(src) as img:
                    img.convert("RGBA").save(dst, "PNG")
            except Exception as e:
                QMessageBox.warning(parent_widget, "錯誤", f"處理 {src.name} 失敗：{e}")
            progress.setValue(i + 1)
        progress.close()

        rel_path = str(target.relative_to(self.base_dir / "文檔"))
        self.config.setdefault("idle_animations", []).append({
            "name": name,
            "path": rel_path,
            "enabled": True,
            "weight": 1,
        })
        QMessageBox.information(
            parent_widget, "完成",
            f"已導入 {len(files)} 幀到「{name}」。"
        )
        self.on_finished()

    @staticmethod
    def _sanitize_name(name: str) -> str:
        import re
        return re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "新動畫"

    def _unique_dir(self, name: str) -> Path:
        i = 2
        while True:
            candidate = self.idle_dir / f"{name}_{i}"
            if not candidate.exists():
                return candidate
            i += 1
```

### 5.4 IdleScheduler

```python
import random
from PySide6.QtCore import QObject, QTimer, Signal


class IdleScheduler(QObject):
    switch_requested = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_path = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._pick_next)

    def start(self, current_path: str):
        self.current_path = current_path
        self._schedule_next()

    def _schedule_next(self):
        lo = self.config["idle_switch"]["min_interval"]
        hi = self.config["idle_switch"]["max_interval"]
        self.timer.start(random.randint(lo, hi) * 1000)

    def _pick_next(self):
        candidates = [
            a for a in self.config.get("idle_animations", [])
            if a.get("enabled", True) and a["path"] != self.current_path
        ]
        if not candidates:
            self._schedule_next()
            return
        weights = [a.get("weight", 1) for a in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        self.current_path = chosen["path"]
        self.switch_requested.emit(chosen["path"])
        self._schedule_next()

    def pause(self):
        self.timer.stop()

    def resume(self):
        self._schedule_next()
```

### 5.5 交叉淡化

```python
def crossfade_to(self, new_pixmap, duration=300):
    self.label_new.setPixmap(new_pixmap)
    self.label_new.show()
    self.label_new.raise_()

    anim_old = QPropertyAnimation(self.effect_old, b"opacity")
    anim_old.setDuration(duration)
    anim_old.setStartValue(1.0)
    anim_old.setEndValue(0.0)

    anim_new = QPropertyAnimation(self.effect_new, b"opacity")
    anim_new.setDuration(duration)
    anim_new.setStartValue(0.0)
    anim_new.setEndValue(1.0)

    group = QParallelAnimationGroup()
    group.addAnimation(anim_old)
    group.addAnimation(anim_new)
    group.finished.connect(self._on_crossfade_finished)
    group.start()
    self._anim_group = group
```

### 5.6 聲音設置頁

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QCheckBox, QGroupBox
)


class AudioSettingsPage(QWidget):
    def __init__(self, config, audio_manager, on_change):
        super().__init__()
        self.config = config
        self.audio = audio_manager
        self.on_change = on_change

        layout = QVBoxLayout(self)

        group_global = QGroupBox("全局")
        form_global = QFormLayout(group_global)
        self.chk_muted = QCheckBox("靜音（關閉所有聲音）")
        self.chk_muted.setChecked(config["audio"]["muted"])
        form_global.addRow(self.chk_muted)

        group_cat = QGroupBox("分類開關")
        form_cat = QFormLayout(group_cat)

        self.chk_click = QCheckBox("點擊音效")
        self.chk_drag = QCheckBox("拖拽音效")
        self.chk_walk = QCheckBox("走動音效")
        self.chk_greeting = QCheckBox("粵語問候語音")
        self.chk_shutdown = QCheckBox("定時關機提示音")

        self.chk_click.setChecked(config["audio"]["click_sfx"])
        self.chk_drag.setChecked(config["audio"]["drag_sfx"])
        self.chk_walk.setChecked(config["audio"]["walk_sfx"])
        self.chk_greeting.setChecked(config["audio"]["greeting_tts"])
        self.chk_shutdown.setChecked(config["audio"]["shutdown_sfx"])

        form_cat.addRow(self.chk_click)
        form_cat.addRow(self.chk_drag)
        form_cat.addRow(self.chk_walk)
        form_cat.addRow(self.chk_greeting)
        form_cat.addRow(self.chk_shutdown)

        layout.addWidget(group_global)
        layout.addWidget(group_cat)
        layout.addStretch()

        self.chk_muted.toggled.connect(self._on_muted)
        self.chk_click.toggled.connect(lambda v: self._set("click_sfx", v))
        self.chk_drag.toggled.connect(lambda v: self._set("drag_sfx", v))
        self.chk_walk.toggled.connect(lambda v: self._set("walk_sfx", v))
        self.chk_greeting.toggled.connect(lambda v: self._set("greeting_tts", v))
        self.chk_shutdown.toggled.connect(lambda v: self._set("shutdown_sfx", v))

        self._update_enabled()

    def _on_muted(self, checked):
        self.audio.set_muted(checked)
        self._update_enabled()
        self.on_change()

    def _set(self, key, value):
        self.config["audio"][key] = value
        self.on_change()

    def _update_enabled(self):
        enabled = not self.chk_muted.isChecked()
        for w in (self.chk_click, self.chk_drag, self.chk_walk,
                  self.chk_greeting, self.chk_shutdown):
            w.setEnabled(enabled)
```

### 5.7 config.json 更新

在第 1 步的基礎上加入以下欄位：

```json
{
  "idle_animations": [
    { "name": "站立呼吸", "path": "animations/idle/idle_standing", "enabled": true, "weight": 1 }
  ],
  "idle_switch": {
    "min_interval": 30,
    "max_interval": 180,
    "avoid_repeat": true
  },
  "audio": {
    "muted": false,
    "click_sfx": true,
    "drag_sfx": false,
    "walk_sfx": false,
    "greeting_tts": true,
    "shutdown_sfx": true
  }
}
```

---

## 六、驗收標準

完成第 3 步後，逐項檢查：

- [ ] 托盤「設置」可打開設置窗口，分頁完整。
- [ ] 改任何設定，晴兒即時反應。
- [ ] 關閉程式再開，設定保留。
- [ ] 「導入動畫資料夾」成功，新動畫出現在清單。
- [ ] 「導入多張圖片」成功，自然排序正確（1, 2, 10 而非 1, 10, 2）。
- [ ] 導入後 `文檔/animations/idle/<動畫名>/` 下是 `frame_000.png` 起。
- [ ] 導入後無需重啟，晴兒待機隨機調度即包含新動畫。
- [ ] 同名動畫再導入時，彈出覆蓋/重命名/取消選項。
- [ ] 中途取消導入，目標目錄被清理，config 未寫入。
- [ ] 待機動畫隨機切換，間隔在設定範圍內。
- [ ] 不連續揀同一個動畫。
- [ ] 不同動畫切換有交叉淡化，相同動畫不淡化。
- [ ] 只有一個啟用動畫時不切換。
- [ ] 全局靜音生效，點擊/拖拽/問候/關機提示全部無聲。
- [ ] 取消靜音後，原本分類選擇仍生效。
- [ ] 全局靜音時，分類開關變灰但保留狀態。
- [ ] 托盤「靜音」與設置窗口同步。
- [ ] 多螢幕不跑丟，高 DPI 正常。
- [ ] `config.json` 正確寫入所有設定。

---

## 七、常見問題與提醒

1. **導入後動畫不生效**：確認導入完成後呼叫了 `on_finished()`，並通知 `IdleScheduler` 重新讀取 config。
2. **中文路徑問題**：用 `Path` 拼接，不要寫死反斜杠；確保系統編碼為 UTF-8。
3. **導入大圖卡頓**：導入時統一縮放到最長邊 1024 px，避免記憶體爆。
4. **自然排序失效**：確認用 `natural_key`，不要用 `sorted()` 直接排。
5. **交叉淡化出黑底**：確認兩個 `QLabel` 都設定了 `WA_TranslucentBackground`。
6. **相同動畫仍然淡化**：確認切換前比較 `new_path == current_path`，相同就 return。
7. **托盤與設置不同步**：兩邊改動都要即時更新對方，用信號雙向綁定。
8. **QSoundEffect 被回收**：用 dict 快取，不要每次播放都新建物件。
9. **全局靜音沒清空分類**：`set_muted` 只改 `muted`，不要動其他分類開關。
10. **不要提前做擴展功能**：定時關機、粵語問候、動態壁紙留到第 4 步。

---

## 八、完成後

第 3 步完成後，執行：
```bash
git add .
git commit -m "step3: 設置窗口 + 待機動畫管理 + 聲音"
```

至此第 1~3 步完成，晴兒已具備核心桌面寵物能力。

後續第 4 步（服務框架 + 三個擴展）與第 5 步（優化打包）可另拆文件。

---

**文件版本**：v1.0  
**對應需求**：桌面伴侶需求文檔 v2.1  
**最後更新**：2026-09-10