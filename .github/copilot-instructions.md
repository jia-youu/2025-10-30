## 快速說明 — ePy_Basic 專案 (給自動化程式碼助理)

以下為在此專案中立刻能夠產生安全、可運行程式碼所必須知道的重點；請只依據專案中可被發現的約定與範例編寫或修改程式碼。

- 此專案目標：提供基於 ePy（MicroPython） 的硬體驅動範例與教學範例（參考 `led_demo.py`, `ePy_ExtV1/oled_demo.py` 等）。
- 重要目錄：`lib/`（驅動與工具庫）、`MicroPython_API/`（硬體 API 與 AT 指令規範說明）、範例檔在專案根目錄與 `ePy_ExtV1/`。

### 關鍵語言 / 執行環境限制（必讀）
- 目標執行環境是 ePy 的 MicroPython：有多項標準 Python 模組不可用或替代品不同（來源：`AGENTS.md`）。
- 不支援 f-string：請使用 string.format()。不要使用 `string.encode()` / `string.decode()`。
- 沒有 `time`、`json`、`re`、`queue`、`threading` 等標準模組：分別使用 `utime`, `ujson`, `ure`, `uqueue`, `_thread`。
- 不使用 class、decorator、generator、async/await 或 lambda；用「函式」和明確的 polling（utime.ticks_ms）來處理時序。
- UART 與 I2C 實作與桌面 Python 不同：UART read/write 請以 bytes 處理（例：參考 `MicroPython_API/UART.md` 與 `lib/mesh_device.py`）。

### 專案程式風格與注記慣例
- 程式需遵守 PEP8（排版風格），但語法需符合 MicroPython 限制。
- 註解請以中文撰寫，目標為初學者可讀（AGENTS.md 要求）。
- Import 第三方或內建專用驅動請直接 `import`（`lib/` 已在 sys.path 中，可直接 import，如 `import htu21d`、`import ssd1306`）。

### 常見檔案與範例（參考）
- 範例燈號：`led_demo.py`（根目錄） — 查看如何控制板上 LED。
- OLED 與感測器：`lib/ssd1306.py`, `lib/htu21d.py`、`ePy_ExtV1/oled_demo.py`。
- Mesh / BLE：`lib/mesh_device.py` 與 `MicroPython_API/MESH_Device_ATCMD.md`（UART0/UART1 的使用注意波特率 115200）。

### 編輯 / 測試 / 驗證流程（專案特有）
- 不建立模擬測試：所有功能在實體 ePy 開發板上測試（不要引入模擬器、線上 IDE 或桌面特有 API）。
- 測試步驟建議（可放入 PR 描述）：1) 編寫/修改 `.py`，2) 透過使用者慣用工具（如 ampy / rshell /板端同步工具）上傳到開發板，3) 在板上觀察輸出或顯示器/感測器行為。

### 產生/修改程式碼時的具體範例指引
- 若需等待：使用 `utime.ticks_ms()` 與差值比較做 polling，而非中斷或 sleep 長時間。
- UART 讀寫：始終以 bytes 處理資料；範例回傳請使用 `b"..."`。
- 字串格式化：`"Temperature: {} C".format(temp)`。

### 不要做的事（常見錯誤）
- 不要使用 f-strings、async/await、裝飾器、生成器或 lambda。
- 不要假設標準 Python 的完整標準庫（請先查 `MicroPython_API/` 對應說明）。

### 如果需要更多上下文
- 先打開 `AGENTS.md`（專案已放置板固有限制與硬體對應清單）與 `MicroPython_API/*.md`（I2C/UART/MESH 指令）來確認 API 行為。

---
若有任何專案內部慣例或硬體細節看起來不完整，請回報給 repo 擁有者並附上你依據的檔案與行數；我可以依照回饋進行迭代更新。
