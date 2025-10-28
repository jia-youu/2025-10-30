# ePy LED 範例
# 說明：
# - 紅燈 (ledr) 每 3 秒週期，亮 1 秒
# - 綠燈 (ledg) 每 2 秒週期，亮 1 秒
# - 黃燈 (ledy) 每 4 秒週期，亮 1 秒
# 實作說明：使用 utime.ticks_ms() 進行非阻塞輪詢，避免長時間阻塞。
# 遵循專案慣例：使用 function 而非 class，並以中文註解說明。

import utime
from machine import LED

# 建立 LED 物件（依照 MicroPython ePy 約定）
led_r = LED('ledr')
led_g = LED('ledg')
led_y = LED('ledy')

# 設定週期與亮度時間（毫秒）
PERIOD_R = 3000  # 紅燈 3 秒
ON_R = 1000      # 亮 1 秒
PERIOD_G = 2000  # 綠燈 2 秒
ON_G = 1000      # 亮 1 秒
PERIOD_Y = 4000  # 黃燈 4 秒
ON_Y = 1000      # 亮 1 秒


def _led_set(led_obj, should_on):
    """將 LED 物件設定為開或關（封裝以利閱讀）"""
    if should_on:
        led_obj.on()
    else:
        led_obj.off()


def main():
    """主程式：非阻塞輪詢，根據時間週期切換 LED 狀態"""
    # 記錄起始時間
    start = utime.ticks_ms()

    # 主迴圈
    while True:
        now = utime.ticks_ms()
        # 使用 ticks 的差值，對各自週期取模判斷是否在亮燈期間
        elapsed = now - start  # 在大多數情況下這樣足夠且簡潔

        # 計算是否該亮（如果 elapsed 為負數—極罕見的 wrap 情況—仍可透過 modulo 處理）
        r_on = (elapsed % PERIOD_R) < ON_R
        g_on = (elapsed % PERIOD_G) < ON_G
        y_on = (elapsed % PERIOD_Y) < ON_Y

        _led_set(led_r, r_on)
        _led_set(led_g, g_on)
        _led_set(led_y, y_on)

        # 短暫暫停以降低 CPU 使用率（不會影響時間判斷精準度）
        utime.sleep_ms(50)


# 若直接執行此檔，則啟動範例
if __name__ == '__main__':
    main()
