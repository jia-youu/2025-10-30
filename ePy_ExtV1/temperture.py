# ePy 溫濕度顯示 demo
# 每秒讀取 HTU21D 溫濕度，顯示於 OLED，支援攝氏/華氏切換（上鍵 P24）
# 遵守 ePy_Basic 教學規範：function 為主、無 f-string、中文註解

import utime
from machine import I2C, Pin
import lib.htu21d
import lib.ssd1306

# 初始化硬體


def init_hardware():
    # 初始化 I2C
    i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
    # 初始化 OLED
    oled = lib.ssd1306.SSD1306_I2C(128, 64, i2c0)
    # 初始化 HTU21D 感測器
    sensor = lib.htu21d.HTU21D(i2c0)
    # 初始化上鍵（P24）
    btn_up = Pin(Pin.epy.P24, Pin.IN, Pin.PULL_UP)
    return oled, sensor, btn_up

# 主示範函式


def demo():
    """
    每秒讀取一次溫濕度，顯示於 OLED。
    溫度單位可用上鍵切換（攝氏/華氏）。
    """
    oled, sensor, btn_up = init_hardware()
    temp_unit = 'C'  # 預設攝氏
    last_btn = 1     # 上鍵前一狀態
    last_tick = utime.ticks_ms()

    while True:
        # 讀取溫濕度
        temp_c = sensor.readTemperatureData()
        humi = sensor.readHumidityData()

        # 處理單位切換
        btn_now = btn_up.value()
        if last_btn == 1 and btn_now == 0:
            # 按下時切換單位
            if temp_unit == 'C':
                temp_unit = 'F'
            else:
                temp_unit = 'C'
            utime.sleep_ms(200)  # 防抖
        last_btn = btn_now

        # 準備顯示字串
        if temp_unit == 'C':
            temp_show = '{0:.1f} C'.format(temp_c)
        else:
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            temp_show = '{0:.1f} F'.format(temp_f)
        humi_show = '{0:.1f} %'.format(humi)

        # 顯示於 OLED
        oled.fill(0)
        oled.text('Temp: ' + temp_show, 0, 0, 1)
        oled.text('Humi: ' + humi_show, 0, 16, 1)
        oled.show()

        # 每秒更新一次
        while utime.ticks_diff(utime.ticks_ms(), last_tick) < 1000:
            # 期間仍需偵測按鍵切換單位
            btn_now = btn_up.value()
            if last_btn == 1 and btn_now == 0:
                if temp_unit == 'C':
                    temp_unit = 'F'
                else:
                    temp_unit = 'C'
                utime.sleep_ms(200)
            last_btn = btn_now
            utime.sleep_ms(10)
        last_tick = utime.ticks_ms()


# 若直接執行本檔案則自動示範
if __name__ == "__main__":
    demo()
