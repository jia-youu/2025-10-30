"""
traffic_light_oled.py

將板上三顆 LED (ledg, ledy, ledr) 與 OLED 顯示結合，
在 OLED 上畫三個圓（左=綠、中=黃、右=紅），
依照以下週期更新：綠 6s、黃 2s、紅 6s（總 14s）。

圓形顯示行為：
  - 初始皆為空心圓
  - 當某顏色啟用時，該圓變為實心，其他兩個為空心

注意：使用 MicroPython/ePy 範例 API（不使用 class、f-string 等），
使用簡單的繪圖演算法（畫圓與填滿）來支援 SSD1306。
"""

from machine import LED, I2C, Pin
from lib.ssd1306 import SSD1306_I2C
import utime


def draw_hollow_circle(oled, x0, y0, r, col=1):
    """用 Midpoint 演算法在 oled 上畫一個空心圓（像素級）。"""
    x = r
    y = 0
    err = 0

    while x >= y:
        oled.pixel(x0 + x, y0 + y, col)
        oled.pixel(x0 + y, y0 + x, col)
        oled.pixel(x0 - y, y0 + x, col)
        oled.pixel(x0 - x, y0 + y, col)
        oled.pixel(x0 - x, y0 - y, col)
        oled.pixel(x0 - y, y0 - x, col)
        oled.pixel(x0 + y, y0 - x, col)
        oled.pixel(x0 + x, y0 - y, col)

        y += 1
        if err <= 0:
            err += 2 * y + 1
        if err > 0:
            x -= 1
            err -= 2 * x + 1


def draw_filled_circle(oled, x0, y0, r, col=1):
    """填滿圓：對每一個 y 繪製水平線段。"""
    y = -r
    while y <= r:
        # 計算該 y 的水平半寬
        xspan = 0
        yy = y
        # 找到最大的 xspan 使 (xspan)^2 + (y)^2 <= r^2
        # 線性搜尋因 r 小（10~20）效能可接受
        while (xspan + 1) * (xspan + 1) + yy * yy <= r * r:
            xspan += 1

        x1 = x0 - xspan
        x2 = x0 + xspan
        # 畫水平線
        oled.fill_rect(x1, y0 + y, x2 - x1 + 1, 1, col)
        y += 1


def update_oled(oled, state):
    """根據 state ('green','yellow','red') 更新 OLED：對應圓為實心，其餘空心。"""
    oled.fill(0)

    # 參數：圓心位置與半徑
    r = 10
    y0 = 32
    x_left = 24
    x_mid = 64
    x_right = 104

    if state == 'green':
        draw_filled_circle(oled, x_left, y0, r, 1)
        draw_hollow_circle(oled, x_mid, y0, r, 1)
        draw_hollow_circle(oled, x_right, y0, r, 1)
    elif state == 'yellow':
        draw_hollow_circle(oled, x_left, y0, r, 1)
        draw_filled_circle(oled, x_mid, y0, r, 1)
        draw_hollow_circle(oled, x_right, y0, r, 1)
    elif state == 'red':
        draw_hollow_circle(oled, x_left, y0, r, 1)
        draw_hollow_circle(oled, x_mid, y0, r, 1)
        draw_filled_circle(oled, x_right, y0, r, 1)
    else:
        # 預設皆空心
        draw_hollow_circle(oled, x_left, y0, r, 1)
        draw_hollow_circle(oled, x_mid, y0, r, 1)
        draw_hollow_circle(oled, x_right, y0, r, 1)

    oled.show()


def main():
    """主程式：初始化 I2C 與 OLED，並與 LED 同步顯示交通號誌（綠6s,黃2s,紅6s）。"""
    # 初始化 LED
    try:
        led_g = LED('ledg')
        led_y = LED('ledy')
        led_r = LED('ledr')
    except Exception:
        print('無法建立 LED 物件，請確認硬體或 API 名稱（"ledg","ledy","ledr"）')
        return

    # 初始化按鍵 (上:P24, 下:P8, 左:P6, 右:P7)
    try:
        btn_up = Pin.epy.P24
        btn_down = Pin.epy.P8
        btn_left = Pin.epy.P6
        btn_right = Pin.epy.P7
        btn_up.init(Pin.IN, Pin.PULL_UP)
        btn_down.init(Pin.IN, Pin.PULL_UP)
        btn_left.init(Pin.IN, Pin.PULL_UP)
        btn_right.init(Pin.IN, Pin.PULL_UP)
    except Exception:
        # 若 Pin API 不可用，繼續但無按鍵功能
        btn_up = None
        btn_down = None
        btn_left = None
        btn_right = None

    # 初始化 I2C 與 OLED
    try:
        i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
        oled = SSD1306_I2C(128, 64, i2c0)
    except Exception:
        print('無法初始化 I2C 或 OLED，請確認接線與驅動')
        return

    # 長模式（原本）：綠6s 黃2s 紅6s
    long_green_ms = 6000
    long_yellow_ms = 2000
    long_red_ms = 6000

    # 短模式（按下下鍵）：綠2s 黃2s 紅2s
    short_green_ms = 2000
    short_yellow_ms = 2000
    short_red_ms = 2000

    # 閃黃模式：黃燈 1s on / 1s off
    blink_period_ms = 2000
    blink_on_ms = 1000

    # 初始模式：長模式（綠6s 黃2s 紅6s）
    mode = 'normal_long'

    # 若要保留長模式也可用 'normal_long'
    # start 用來計算相對時間
    start = utime.ticks_ms()

    # 按鍵去彈跳用
    last_up = 1
    last_down = 1
    last_left = 1
    last_right = 1

    # 初始顯示
    update_oled(oled, None)

    while True:
        now = utime.ticks_ms()
        elapsed = utime.ticks_diff(now, start)
        if elapsed < 0:
            elapsed = -elapsed

        # 按鍵偵測（若有按鍵物件）
        if btn_up is not None:
            up_state = btn_up.value()
            if last_up == 1 and up_state == 0:
                # 按下上鍵 -> 切換到閃黃模式
                utime.sleep_ms(50)
                if btn_up.value() == 0:
                    mode = 'blink_yellow'
                    # 重新計時，讓閃爍從 on 開始
                    start = utime.ticks_ms()
            last_up = up_state

            down_state = btn_down.value()
            if last_down == 1 and down_state == 0:
                # 按下下鍵 -> 切換到短模式（綠2s 黃2s 紅2s）
                utime.sleep_ms(50)
                if btn_down.value() == 0:
                    mode = 'normal_short'
                    start = utime.ticks_ms()
            last_down = down_state

            # left/right 暫不指定功能，可監聽或擴充
            last_left = btn_left.value()
            last_right = btn_right.value()

        # 根據模式更新 LED 與 OLED
        if mode == 'blink_yellow':
            phase = elapsed % blink_period_ms
            if phase < blink_on_ms:
                # 黃燈 on
                led_g.off()
                led_y.on()
                led_r.off()
                update_oled(oled, 'yellow')
            else:
                # all off (OLED 顯示空心)
                led_g.off()
                led_y.off()
                led_r.off()
                update_oled(oled, None)

        elif mode == 'normal_short':
            cycle_ms = short_green_ms + short_yellow_ms + short_red_ms
            phase = elapsed % cycle_ms
            if phase < short_green_ms:
                led_g.on(); led_y.off(); led_r.off()
                update_oled(oled, 'green')
            elif phase < (short_green_ms + short_yellow_ms):
                led_g.off(); led_y.on(); led_r.off()
                update_oled(oled, 'yellow')
            else:
                led_g.off(); led_y.off(); led_r.on()
                update_oled(oled, 'red')

        else:
            # fallback to long mode
            cycle_ms = long_green_ms + long_yellow_ms + long_red_ms
            phase = elapsed % cycle_ms
            if phase < long_green_ms:
                led_g.on(); led_y.off(); led_r.off()
                update_oled(oled, 'green')
            elif phase < (long_green_ms + long_yellow_ms):
                led_g.off(); led_y.on(); led_r.off()
                update_oled(oled, 'yellow')
            else:
                led_g.off(); led_y.off(); led_r.on()
                update_oled(oled, 'red')

        # 每 80 ms 更新一次，兼顧反應與 CPU 使用
        utime.sleep_ms(80)


if __name__ == '__main__':
    main()
