"""
htu_oled_mesh.py

功能：
- 每秒讀取 HTU21D 溫濕度，並顯示在 SSD1306 OLED 上：
  - 第一行：溫度，顯示到小數第一位，帶單位 C 或 F
  - 第二行：濕度，顯示到小數第一位，帶 %
  - 第三行：AIN5 類比電壓，顯示到小數第一位（單位 V，顯示時無單位要求）
- 按下上鍵 (P24) 切換溫度單位（攝氏 <-> 華氏），有去彈跳處理
- 每次讀取時，若 Mesh 已綁定，分別送出溫度與濕度資料（格式 "T:xx.x" 與 "H:xx.x"），並送出 AIN5 ("A:xx.x")

使用方式：
 - 上傳後在 REPL 執行：
     import htu_oled_mesh
     htu_oled_mesh.main()

注意：依 ePy 專案慣例，記得使用 I2C(0) 與 Pin.epy.AIN5、Pin.epy.P24 等硬體對應。
"""

from machine import I2C, Pin, ADC
from lib.ssd1306 import SSD1306_I2C
from lib.htu21d import HTU21D
from lib.mesh_device import MeshDevice
import utime


def c_to_f(c):
    """攝氏轉華氏"""
    return c * 9.0 / 5.0 + 32.0


def format_one_decimal(value):
    """格式化為小數第一位的字串（使用 str.format()）"""
    return '{:.1f}'.format(value)


def main():
    # 初始化 I2C 與 OLED
    try:
        i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
        oled = SSD1306_I2C(128, 64, i2c0)
    except Exception:
        print('無法初始化 I2C 或 OLED，請確認硬體與驅動')
        return

    # 初始化 HTU21D
    try:
        sensor = HTU21D(i2c0)
    except Exception:
        print('無法初始化 HTU21D 感測器')
        return

    # 初始化 AIN5
    try:
        ain5 = ADC(Pin.epy.AIN5)
    except Exception:
        ain5 = None

    # 初始化 MeshDevice（不啟用 debug）
    try:
        mesh = MeshDevice(uart_id=0, baudrate=115200, debug=False)
        # 進行 reboot 嘗試取得綁定狀態（非必要，但通常可更新 is_bound）
        mesh.reboot(timeout=500)
    except Exception:
        mesh = None

    # 初始化上鍵 (P24) 用於切換單位
    try:
        btn_up = Pin.epy.P24
        btn_up.init(Pin.IN, Pin.PULL_UP)
    except Exception:
        btn_up = None

    # 狀態
    use_celsius = True
    last_up = 1

    # 時間控制，每 1000 ms 讀取一次
    interval_ms = 1000
    last_read = utime.ticks_ms() - interval_ms

    oled.fill(0)
    oled.text('HTU21D Starting', 0, 0)
    oled.show()
    utime.sleep_ms(500)

    while True:
        now = utime.ticks_ms()

        # 按鍵偵測 (去彈跳)
        if btn_up is not None:
            up_state = btn_up.value()
            if last_up == 1 and up_state == 0:
                utime.sleep_ms(50)
                if btn_up.value() == 0:
                    use_celsius = not use_celsius
            last_up = up_state

        # 週期性讀取
        if utime.ticks_diff(now, last_read) >= interval_ms:
            last_read = now

            # 讀溫濕度
            try:
                temp_c = sensor.readTemperatureData()
                hum = sensor.readHumidityData()
            except Exception:
                temp_c = None
                hum = None

            # 讀 AIN5
            if ain5 is not None:
                try:
                    ain_val = ain5.read()  # 0..4095
                    ain_voltage = ain_val * 3.3 / 4095.0
                except Exception:
                    ain_voltage = None
            else:
                ain_voltage = None

            # 溫度顯示與格式化
            if temp_c is None:
                temp_str = 'T: --.-'
            else:
                if use_celsius:
                    temp_display = temp_c
                    unit = 'C'
                else:
                    temp_display = c_to_f(temp_c)
                    unit = 'F'
                temp_str = 'T:{} {}'.format(format_one_decimal(temp_display), unit)

            # 濕度顯示
            if hum is None:
                hum_str = 'H: --.- %'
            else:
                hum_str = 'H:{} %'.format(format_one_decimal(hum))

            # AIN5 顯示（只顯示電壓到一位小數）
            if ain_voltage is None:
                ain_str = 'A: --.-'
            else:
                ain_str = 'A:{} V'.format(format_one_decimal(ain_voltage))

            # 更新 OLED（第一行溫度，第二行濕度，第三行 AIN5）
            oled.fill(0)
            oled.text(temp_str, 0, 0)
            oled.text(hum_str, 0, 16)
            oled.text(ain_str, 0, 32)
            oled.show()

            # 透過 Mesh 傳送資料（若有 mesh 並已綁定）
            if mesh is not None and mesh.is_bound:
                # 傳送溫度與濕度為兩次（T:xx.x 與 H:xx.x）
                try:
                    if temp_c is not None:
                        mesh.set_data('T:' + format_one_decimal(temp_display))
                        utime.sleep_ms(100)
                    if hum is not None:
                        mesh.set_data('H:' + format_one_decimal(hum))
                        utime.sleep_ms(100)
                    if ain_voltage is not None:
                        # AIN5 也用一位小數送出
                        mesh.set_data('A:' + format_one_decimal(ain_voltage))
                except Exception:
                    # 忽略傳送錯誤，避免崩潰
                    pass

        # 短暫延遲，避免 busy-loop
        utime.sleep_ms(50)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n程式已中斷')
