```markdown
# 第 2 步：動畫狀態機 + 待機行為

## 一、目標

晴兒會待機、被點擊、被拖拽，支援多個待機動畫自動掃描與隨機切換，特定動畫可附帶限定範圍內的移動。

完成後，你應該看到：
- 晴兒不再是一張靜止圖片，會有序列帧動畫或程序化呼吸。
- **動畫自動掃描**：`文檔/animations/idle/` 下所有子資料夾會被自動識別，無需手動維護 config.json，也無需重新編譯。
- **每個動畫有獨立 `anim.json`**，控制名稱、啟用、權重、是否移動等。
- **啟動後隨機選擇一個啟用動畫**（不固定 idle_standing）。
- **拖拽釋放後隨機選擇一個啟用動畫**（不固定 idle_standing）。
- **同一動畫至少持續 1 分鐘**（拖拽動畫除外）。
- **`weight` 值越小，被選中機率越高**。
- 點擊晴兒，她會有反應動畫。
- 拖拽晴兒時切換到 Drag 動畫，放開後隨機切換到新的待機動畫，且晴兒**停留在拖拽後的新位置**。
- 切換到 `move=true` 的動畫時，以當前位置為新起點來回移動。

---

## 二、對應需求

- 3.1.2 動畫狀態機
- 3.1.3 待機動畫調度
- 3.2 動畫資料夾與 anim.json
- 5.1 動畫自動掃描（AnimationLibrary）
- 5.2 待機動畫調度（IdleScheduler）
- 5.3 拖拽移動與位置保持
- 5.4 自然排序

---

## 三、要建立的檔案與結構

```text
桌面伴侶/
├─ app/
│  ├─ core/
│  │  ├─ __init__.py
│  │  ├─ animation.py
│  │  ├─ behavior.py
│  │  ├─ animation_library.py
│  │  └─ idle_scheduler.py
└─ 文檔/
   ├─ 晴兒.png
   └─ animations/
      └─ idle/
         ├─ idle_standing/
         │  ├─ anim.json
         │  ├─ frame_000.png
         │  └─ ...
         ├─ idle_walking/
         │  ├─ anim.json
         │  ├─ frame_000.png
         │  └─ ...
         └─ idle_cat/
            ├─ anim.json
            ├─ frame_000.png
            └─ ...
```

**說明**：
- 本步驟先支援兩種素材形態：
  1. **單張圖片**：用程式做呼吸縮放，模擬待機。
  2. **序列帧動畫**：`frame_000.png`、`frame_001.png`… 依序播放。
- 每個動畫資料夾可選有 `anim.json`，若無則用預設值。

---

## 四、動畫資料夾與 anim.json

### 4.1 資料夾結構

```text
文檔/animations/idle/
├─ idle_standing/
│  ├─ anim.json
│  ├─ frame_000.png
│  └─ ...
├─ idle_walking/
│  ├─ anim.json
│  ├─ frame_000.png
│  └─ ...
└─ idle_cat/
   ├─ anim.json
   ├─ frame_000.png
   └─ ...
```

### 4.2 anim.json 格式

```json
{
  "name": "站立呼吸",
  "enabled": true,
  "weight": 1,
  "move": false,
  "move_speed": 4,
  "move_range": 200
}
```

| 欄位 | 型別 | 預設 | 說明 |
| :--- | :--- | :--- | :--- |
| `name` | str | 資料夾名 | 顯示名稱 |
| `enabled` | bool | true | 是否啟用 |
| `weight` | int | 1 | 隨機選擇權重，**值越小權重越高** |
| `move` | bool | false | 是否附帶移動 |
| `move_speed` | int | 4 | 移動速度（像素/幀），僅 move=true 時有效 |
| `move_range` | int | 200 | 移動範圍（像素），僅 move=true 時有效 |

### 4.3 暫時關閉某動畫

將該動畫的 `anim.json` 中 `enabled` 設為 `false`。程式啟動後不會選中此動畫。

---

## 五、動畫狀態機設計

### 5.1 狀態定義

```text
Idle    待機（播放當前待機動畫，可能附帶移動）
Click   被點擊反應
Drag    被拖拽
```

**注意**：不再有獨立的 `Walk` 狀態。移動是待機動畫的附帶行為，不是獨立狀態。

### 5.2 狀態轉換

```text
Idle -> Click -> Idle
Idle -> Drag -> Idle（隨機選擇新的待機動畫）
Idle 內部：不同待機動畫之間隨機切換（由 IdleScheduler 控制）
```

規則：
- `Click` 是單次動畫，播完自動回 `Idle`。
- `Drag` 期間暫停自動行為與移動，放開後隨機切換到新的待機動畫。
- 拖拽釋放後，晴兒**停留在新位置**，不回到原位。
- 若新動畫 `move=true`，以當前位置為新移動起點。
- 同一動畫至少持續 1 分鐘（拖拽動畫除外）。

---

## 六、具體任務

### 6.1 建立 AnimationLibrary（動畫自動掃描）

- 掃描 `文檔/animations/idle/` 下所有子資料夾。
- 每個子資料夾必須包含至少一個 `frame_*.png`，否則跳過。
- 若有 `anim.json`，讀取並解析；缺失欄位用預設值補齊。
- 若無 `anim.json`，全部使用預設值。
- 若 JSON 解析失敗，使用預設值，不中斷掃描。
- 提供 `scan()` 回傳完整清單，`get_enabled()` 回傳啟用清單。

### 6.2 建立 AnimationStateMachine

- 管理目前狀態與當前幀索引。
- 每個狀態對應一組序列帧（`list[QPixmap]`）。
- 提供 `set_state(new_state)` 與 `next_frame()`。
- 支援單張圖片模式：若某狀態只有一張圖，用程序化動效代替。

### 6.3 建立 IdleScheduler

- 啟動時呼叫 `start()`，內部立即執行 `pick_random()`，隨機選擇一個啟用動畫。
- 拖拽釋放後呼叫 `pick_random()`，隨機選擇一個啟用動畫。
- 同一動畫至少持續 `MIN_HOLD_SECONDS = 60` 秒。
- 切換時排除當前動畫，避免連續重複。
- 權重計算：`weights = [1 / max(a.get("weight", 1), 1) for a in candidates]`。
- 候選為空時不切換，重新排程。
- 提供 `pause()`、`resume()`、`reload()`。

### 6.4 建立 BehaviorScheduler

- 用 `QTimer` 控制 30 FPS 更新動畫。
- 只負責更新動畫幀與待機移動（若當前動畫 `move=true`）。
- 拖拽時暫停，放開後恢復。

### 6.5 點擊反應

- 在 `mousePressEvent` 中區分「點擊」與「拖拽」：
  - 按下與放開位置距離小於閾值（例如 5 px），視為點擊。
  - 否則視為拖拽。
- 點擊時播放 `Click` 動畫，播完回 `Idle`。

### 6.6 拖拽狀態

- 按下左鍵並移動超過閾值時，進入 `Drag` 狀態。
- 拖拽期間：
  - 播放 `Drag` 動畫。
  - 暫停 `IdleScheduler`。
- 放開左鍵後：
  - 保存新位置到 config。
  - 呼叫 `idle_scheduler.pick_random()` 隨機選擇新待機動畫。
  - 晴兒停留在新位置。
  - 若新動畫 `move=true`，以當前位置為新移動起點。
  - 恢復 `IdleScheduler`。

### 6.7 待機移動

- 移動由當前待機動畫的 `anim.json` 決定。
- 每個待機動畫有 `move` 欄位：
  - `move=false`：原地不動。
  - `move=true`：在限定範圍內來回移動。
- 移動參數：
  - `move_speed`：像素/幀，預設 4。
  - `move_range`：移動範圍像素，預設 200。
- 移動邏輯：
  - 進入該動畫時記錄 `move_origin = self.x()`（以當前位置為起點）。
  - 每幀更新 `x`，在 `[origin, origin + move_range]` 內來回移動。
  - 超出範圍時反向。
  - `stop_idle_move()` 預設**不**回到原點。

---

## 七、關鍵代碼要點

### 7.1 AnimationLibrary

```python
import json
import re
from pathlib import Path


DEFAULT_ANIM_CONFIG = {
    "name": None,
    "enabled": True,
    "weight": 1,
    "move": False,
    "move_speed": 4,
    "move_range": 200,
}


def natural_key(path: Path):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", path.stem)]


class AnimationLibrary:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.idle_dir = base_dir / "文檔" / "animations" / "idle"

    def scan(self) -> list:
        animations = []
        if not self.idle_dir.exists():
            return animations

        for folder in sorted(self.idle_dir.iterdir()):
            if not folder.is_dir():
                continue

            frames = sorted(folder.glob("frame_*.png"), key=natural_key)
            if not frames:
                continue

            config_path = folder / "anim.json"
            anim = dict(DEFAULT_ANIM_CONFIG)
            if config_path.exists():
                try:
                    data = json.loads(config_path.read_text(encoding="utf-8"))
                    for k in DEFAULT_ANIM_CONFIG:
                        if k in data:
                            anim[k] = data[k]
                except (json.JSONDecodeError, OSError):
                    pass

            if anim["name"] is None:
                anim["name"] = folder.name

            anim["path"] = str(folder.relative_to(self.base_dir / "文檔"))
            anim["frames"] = [str(f) for f in frames]
            animations.append(anim)

        return animations

    def get_enabled(self) -> list:
        return [a for a in self.scan() if a.get("enabled", True)]
```

### 7.2 IdleScheduler

```python
import random
from PySide6.QtCore import QObject, QTimer, Signal
from app.core.animation_library import AnimationLibrary


MIN_HOLD_SECONDS = 60


class IdleScheduler(QObject):
    switch_requested = Signal(dict)

    def __init__(self, base_dir, config):
        super().__init__()
        self.base_dir = base_dir
        self.config = config
        self.library = AnimationLibrary(base_dir)
        self.current_path = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._pick_next)

    def start(self):
        self.timer.stop()
        self.current_path = None
        self.pick_random()

    def pick_random(self):
        """立即隨機選擇一個啟用動畫（不排除當前）。"""
        candidates = self.library.get_enabled()
        if not candidates:
            return
        weights = [1 / max(a.get("weight", 1), 1) for a in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        self.current_path = chosen["path"]
        self.timer.stop()
        self.switch_requested.emit(chosen)
        self._schedule_next()

    def _pick_next(self):
        candidates = [
            a for a in self.library.get_enabled()
            if a["path"] != self.current_path
        ]
        if not candidates:
            self._schedule_next()
            return
        weights = [1 / max(a.get("weight", 1), 1) for a in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        self.current_path = chosen["path"]
        self.switch_requested.emit(chosen)
        self._schedule_next()

    def _schedule_next(self):
        lo = max(MIN_HOLD_SECONDS,
                 self.config.get("idle_switch", {}).get("min_interval", 60))
        self.timer.start(lo * 1000)

    def pause(self):
        self.timer.stop()

    def resume(self):
        self._schedule_next()

    def reload(self):
        pass
```

### 7.3 待機移動

```python
def start_idle_move(self, speed=4, move_range=200):
    self._move_speed = speed
    self._move_range = move_range
    self._move_origin = self.x()  # 以當前位置為新起點
    self._move_direction = 1
    self._moving = True


def stop_idle_move(self, restore_origin=False):
    self._moving = False
    if restore_origin and hasattr(self, "_move_origin"):
        self.move(self._move_origin, self.y())


def update_idle_move(self):
    if not getattr(self, "_moving", False):
        return
    new_x = self.x() + self._move_speed * self._move_direction
    if new_x > self._move_origin + self._move_range:
        new_x = self._move_origin + self._move_range
        self._move_direction = -1
    elif new_x < self._move_origin:
        new_x = self._move_origin
        self._move_direction = 1
    self.move(new_x, self.y())
```

### 7.4 點擊與拖拽

```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self._press_pos = event.globalPosition().toPoint()
        self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
        self._dragging = False
        event.accept()


def mouseMoveEvent(self, event):
    if event.buttons() & Qt.LeftButton and hasattr(self, "_press_pos"):
        cur = event.globalPosition().toPoint()
        if not self._dragging:
            if (cur - self._press_pos).manhattanLength() > 5:
                self._dragging = True
                self.state_machine.set_state("Drag")
                if hasattr(self, "idle_scheduler"):
                    self.idle_scheduler.pause()
        if self._dragging:
            self.move(cur - self._drag_offset)
        event.accept()


def mouseReleaseEvent(self, event):
    if event.button() != Qt.LeftButton:
        return

    if getattr(self, "_dragging", False):
        # 保存新位置
        self.config["x"] = self.x()
        self.config["y"] = self.y()
        save_config(self.config)

        # 隨機選擇新的待機動畫
        if hasattr(self, "idle_scheduler") and self.idle_scheduler:
            self.idle_scheduler.pick_random()
        else:
            self.state_machine.set_state("Idle")

        self._dragging = False
    else:
        self.state_machine.set_state("Click")

    for attr in ("_press_pos", "_drag_offset"):
        if hasattr(self, attr):
            delattr(self, attr)
    event.accept()
```

### 7.5 待機動畫切換處理

```python
def on_idle_switch(self, anim: dict):
    """由 IdleScheduler 觸發，切換到新的待機動畫。"""
    if anim["path"] == self.current_idle_path:
        return

    self.stop_idle_move()
    self.load_idle_animation(anim)
    self.state_machine.set_state("Idle")
    self.state_machine.current_index = 0

    first_frame = self._get_first_frame("Idle")
    if first_frame:
        self.set_pixmap(first_frame)

    if anim.get("move", False):
        self.start_idle_move(
            speed=anim.get("move_speed", 4),
            move_range=anim.get("move_range", 200),
        )

    self.current_idle_path = anim["path"]
```

### 7.6 config.json 對應更新

```json
{
  "idle_switch": {
    "min_interval": 60,
    "avoid_repeat": true
  }
}
```

---

## 八、驗收標準

完成第 2 步後，逐項檢查：

- [ ] 程式啟動後自動掃描 `文檔/animations/idle/` 下所有子資料夾。
- [ ] 每個動畫的屬性由該資料夾內的 `anim.json` 決定。
- [ ] 新增動畫資料夾後，重啟程式即可被掃描到，無需改 config.json 或重新編譯。
- [ ] 修改 `anim.json` 後，重啟程式即生效。
- [ ] 若某個動畫缺少 `anim.json`，使用預設值（enabled=true, weight=1, move=false）。
- [ ] 若某個動畫缺少 `frame_*.png`，該動畫被跳過。
- [ ] 某動畫 `enabled=false` 時不被選中。
- [ ] 啟動後隨機顯示一個啟用動畫（不固定為 idle_standing）。
- [ ] 拖拽釋放後隨機切換到一個啟用動畫（不固定為 idle_standing）。
- [ ] 同一動畫至少持續 1 分鐘（拖拽動畫除外）。
- [ ] `weight` 值越小，被選中機率越高。
- [ ] 拖拽晴兒到新位置放開，晴兒**停留在新位置**，不回到原位。
- [ ] 若拖拽釋放後切換到 `move=true` 的動畫，晴兒從新位置開始移動，不跳回舊位置。
- [ ] 點擊晴兒有反應動畫，播完回待機。
- [ ] 拖拽期間暫停待機調度，放開後恢復。
- [ ] 空閒 CPU 佔用低（建議低於 3%）。
- [ ] 動畫播放流暢，無明顯卡頓。

---

## 九、常見問題與提醒

1. **啟動後顯示的動畫不是隨機**：確認 `IdleScheduler.start()` 有呼叫 `pick_random()`，且候選動畫來自 `AnimationLibrary.get_enabled()`。
2. **拖拽後回到原位**：確認 `stop_idle_move()` 沒有傳 `restore_origin=True`；`start_idle_move()` 以當前位置為新起點。
3. **拖拽釋放後沒有切換動畫**：確認 `mouseReleaseEvent` 中有呼叫 `idle_scheduler.pick_random()`。
4. **新增動畫無效**：確認資料夾下有 `frame_*.png`，且 `anim.json` 格式正確。
5. **weight 方向錯誤**：確認權重計算為 `1 / max(weight, 1)`，而非直接使用 weight。
6. **動畫卡頓**：確認 FPS 不超過 30，序列帧尺寸不要太大（建議最長邊 512–1024 px）。
7. **圖片閃爍**：確認 `QLabel` 設定了 `WA_TranslucentBackground`。
8. **點擊與拖拽衝突**：用移動距離閾值（5 px）區分，不要用時間。
9. **拖拽後不恢復待機**：確認 `mouseReleaseEvent` 中有恢復 `idle_scheduler`。
10. **不要提前做導入功能**：序列帧導入留到第 3 步，本步驟先用現成資料夾或單張圖。

---

## 十、完成後

第 2 步完成後，執行：
```bash
git add .
git commit -m "step2: 動畫自動掃描 + 待機隨機調度 + 拖拽停留新位置"
```

然後進入第 3 步：`docs/step3_設置與聲音.md`。

---

**文件版本**：v1.2  
**對應需求**：桌面伴侶需求文檔 v2.3  
**最後更新**：2026-09-14
```