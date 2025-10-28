Short guidance for AI coding agents working on the ePy_Basic repository.
Focus: MicroPython drivers and examples for the ePy platform.
Keep this file concise (20–50 lines) and actionable.

# Copilot / AI agent instructions for ePy_Basic



  - `htu21d.py`：HTU21D I2C 範例（使用 `i2c.mem_read()`、CRC 檢查）
  - `ssd1306.py`：SSD1306 顯示驅動（framebuf、I2C buffer 第一位為 control byte）
  - `ePy_ExtV1/oled.py`：擴充板上 UI helper（教學風格、示範如何初始化與畫選單）

  - 不使用 f-string；以 string.format()。
  - 儘量以 function 為主（教學導向）；避免新增 class、decorator、generator、async/await、lambda（現有檔案例外）。
  - 使用 MicroPython 替代庫名：`utime`/`ujson`/`ure`/`uqueue`/_thread 等。
  - UART I/O 必須用 bytes，勿以 str 處理。
  - 註解需為中文，並遵守 PEP8（行長與縮排）。

  - I2C 讀 register：使用 `i2c.mem_read(length, addr, cmd)`（見 `lib/htu21d.py`）。
  - OLED 更新：準備整個 framebuffer buffer（第一 byte 為控制位），一次用 `i2c.send(buffer, addr)` 傳送（見 `lib/ssd1306.py`）。
  - 驅動 API：建構時傳入已初始化的 `i2c` 或 `spi` 物件，提供同步讀寫函式（如 readTemperatureData()）。

  - 優先在真機測試；repo 無通用模擬器。示例初始化：
    - from machine import I2C
    - import ssd1306,htu21d 
    - i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
    - oled = ssd1306.SSD1306_I2C(128, 64, i2c0)
  - 測試感測器：
    - sensor = htu21d.HTU21D(i2c0)
    - temp = sensor.readTemperatureData()

  - 檔案沒記載 I2C 地址、引腳或接線圖時必須詢問。
  - 若建議改變整體程式風格（例如改用 class）或引入需同步更新多個範例的改動時，先徵詢。

  - 此專案以教學範例為主，請勿一次性大幅重構導致教學風格失真。
  - 任何新增檔案應附簡短 demo() 範例並在註解中說明硬體前提。

請回饋是否需要加入更多硬體接線範例、測試腳本或 CI 指南（如要我可以再補）。
