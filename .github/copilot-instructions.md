## ePy_Basic — Copilot 指示（專案摘要與本地慣例）

下面為讓 AI 立刻在本專案中有生產力所需的關鍵知識、範例與可遵循規則。內容均來自專案中可發現的檔案（`AGENTS.md`, `README.md`, 以及 `MicroPython_API/` 與 `lib/` 目錄）。請只採用可驗證的模式與約定。

### 1) 大局架構與目的
- 本專案為 ePy MicroPython 範例集合與驅動程式（device drivers / utilities），目的是在實體 ePy MCU 上示範硬體互動（OLED、HTU21D、RGB LED、Mesh/BLE via UART 等）。
- 重要目錄：
  - `lib/`：擴充套件 library（例如 `ssd1306.py`, `htu21d.py`, `mesh_device.py`）。程式直接 import，不需變更 sys.path。
  - `MicroPython_API/`：描述 I2C/UART/TIMER 等硬體 API 與限制的文件（首要參考來源）。
  - 範例檔案分散在根目錄與 `ePy_ExtV1/`, `backup/` 等。

### 2) 關鍵約定（必須遵守）
- 語言/環境：MicroPython（ePy 平台），非完整 CPython；許多標準模組缺失或替代（見 `AGENTS.md`）。
- 禁止/替代列表（務必遵守）：
  - 不使用 f-string；改用 `string.format()`。
  - 沒有 `time`、`json`、`re`... 使用替代模組 `utime`, `ujson`, `ure`。
  - 不使用 class（專案以 function 為主）、decorator、generator、async/await、lambda。
  - 不使用中斷；使用 polling（utime.ticks_ms()）進行時間判斷。
  - UART 讀寫必須使用 bytes（不要用 str 處理串列輸入/輸出）。
  - 遵守 PEP8（命名/縮排）與中文註解說明程式用途（專案目標為教學）。

### 3) 常見整合點與範例
- OLED（I2C0）：參考 `lib/ssd1306.py`，範例檔 `ePy_ExtV1/oled_demo.py` 與 `backup/oled.py`。顯示大小為 128x64。
- 溫濕度感測：`lib/htu21d.py`，接在 I2C0。
- Mesh / BLE：透過 UART（UART0、UART1），AT command 文件在 `MicroPython_API/MESH_Device_ATCMD.md`，範例與 helper在 `lib/mesh_device.py`。
- RGB LED：可用 `machine.LED('LED.RGB')` 控制（見 `AGENTS.md`）。

### 4) 編寫/修改程式時要點（AI 指令化建議）
- 產生程式碼時，優先參考 `MicroPython_API/*.md` 與 `lib/*.py` 的使用方式與參數範例。
- 生成範例時以 function 為單位，避免引入 classes 或複雜語法特性。
- 字串處理：避免使用 `.format()` 以外的字串插值；若產生序列化程式碼，使用 `ujson`。
- UART 範例：輸入/輸出都以 bytes 處理（例：b"AT+...\r\n"），不要使用 `.encode()` / `.decode()`。

### 5) 測試與開發工作流程（可觀察到的慣例）
- 本專案以實機測試為主，**不使用模擬器或線上 IDE**；測試須在 ePy 開發板上進行（見 `AGENTS.md`）。
- 檔案部署/Flashing 並非專案內定義的步驟（repo 未包含上傳腳本）；若需新增上傳說明，請在 PR 中明確標註工具（例如 ampy / rshell / Thonny）與範例命令。

### 6) 範例片段（風格指引）
- 使用 utime 輪詢代替中斷（概念）:

  - 以 `utime.ticks_ms()` 做時間差計算，而非 sleep-blocking 的長延遲。

### 7) 編輯/提交建議
- 保持註解為中文，清楚說明 hardware pin、I2C 地址與初始化參數（方便初學者閱讀）。
- 若修改 `lib/` 中的驅動，請在檔案頂端保留簡短使用說明與相容資訊（例：支援哪個 I2C bus、預設位址）。

---
如果這份指示檔中有遺漏的專案慣例（例如特定上傳工具或常用硬體腳位表），請告訴我，我會把實際檔案或使用流程整合進來並更新此檔案。感謝回饋！
