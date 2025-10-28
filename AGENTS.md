# Project Overview
這是一個基於ePy SDK的專案，包含多個模組和測試文件。主要目標是提供MicroPython設備的驅動程序和實用程序模組。ePy 是一個MCU硬體平台，支援MicroPython。MicroPython是一個針對微控制器和嵌入式系統優化的Python 3語言實現。但有些限制，使用限制與部分特製API 或模組紀錄在下

# ePy MicroPython 使用限制
- 不支援 f-string , 使用 string.format() 來格式化字串
- 沒有 time 模組, 使用 utime 模組來取代
- 沒有 threading 模組, 使用 _thread 模組來取代
- 沒有 queue 模組, 使用 uqueue 模組來取代
- 沒有 json 模組, 使用 ujson 模組來取代
- 沒有 re 模組, 使用 ure 模組來取代
- 基礎訓練用，產生 code 不使用 class , 使用 function 來取代
- 不使用中斷，使用 Polling 來取代 utime.ticks_ms() 來做時間判斷
- 不使用裝飾器 (Decorator) 
- 不使用生成器 (Generator)
- 不使用異步 (Async/Await)
- 不使用 lambda 函數
- 撰寫註解說明程式的用途(中文)，力求讓初學者看得懂
- UART read/write 使用 bytes 不要使用  string  處理
- 編寫程式遵守  PEP8 規範
- 有指定使用 module 或者 package ，直接 import 進來使用
- epy micrioPython 硬體API 與一般 Python API 不一樣，請參考 ./MicroPython_API/ 目錄下 所有相關 .md 檔案
- 不建構測試環境，直接在 ePy 開發板上測試
- 不使用模擬器 (Simulator) 或線上IDE (Online IDE)
- 沒有 reversed()
- 沒有 string.encode()
- 沒有 string.decode()

# ePy 內建硬體模組
- 參考 ./MicroPython_API/ 目錄下 所有相關 .md 檔案
- epy 包含三個LED R/Y/G, 一個按鈕 `Keya` 或使用 `Pi.epy.P24`
- IO 腳位對應參考 Pin.epy.P0-P24
- ADC 腳位對應參考 Pin.epy.AIN0-5
- BLE GATT Module 使用 UART1 , Baud Rate = 115200 , AT Command
- 一個 RGB LED 燈帶, 接口，使用 machine.LED('LED.RGB') 控制
- epy 使用的I2C/UART與通用的不一樣，使用方法請參考 ./MicroPython_API/I2C.md 與 ./MicroPython_API/UART.md

  
# epy 擴充版 V1.0 模組硬體協議
- 一個UART0接口可以接 BLE MESH 模組 , Baud Rate = 115200 , AT Command參考 ./MicroPython_API/MESH_Device_ATCMD.md
- AIN5 連接一個  可變電阻 (Potentiometer)
- 四個 Push Button , 分別接 上(Pin.epy.P24) 下(Pin.epy.P8) 左(Pin.epy.P6) 右(Pin.epy.P7)
- I2C0 接口 連接 OLED 顯示器 ，直接呼叫 ssd1306.py 模組
- I2C0 接口 連接 HTU21D 溫溼度感測器，直接呼叫 htu21d.py 模組
- microphone AIN2  
- SSD1306 OLED 顯示器 128x64，只支援英文數字字體
- Mesh Device 資料收送可以直接套用 lib/mesh_device.py 模組
- py microPython  已經內定 擴充 library 放置在 lib/ 目錄下，import 不需要加入lib路徑

