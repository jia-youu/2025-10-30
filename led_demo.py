"""
led_demo.py

範例：控制 ePy 開發板上的紅色 LED（ledr），每 3 秒週期中亮 1 秒。

注意：依 ePy/MicroPython 專案慣例，不使用 class、f-string 等限制，
使用 utime.ticks_ms() 做 polling 判斷時間。
"""

from machine import LED
import utime


def main():
    """主程式：紅色 LED 每 3 秒亮 1 秒（on:1s, off:2s）。"""
    # 建立紅燈物件（名稱參考 MicroPython_API/micropython_internal.md）
    try:
        ledr = LED('ledr')
    except Exception:
        # 如果機板或模組不支援，嘗試用 LED(LED.R) 之類的替代（保險處理）
        # 這裡不使用 f-string，使用簡單的輸出字串
        print('無法建立 LED("ledr") 物件，請確認硬體或 API 名稱')
        return

    cycle_ms = 3000  # 週期 3000 ms
    on_ms = 1000     # 點亮時間 1000 ms

    start = utime.ticks_ms()

    while True:
        # 計算目前相對於 start 的週期位置（0..cycle_ms-1）
        now = utime.ticks_ms()
        elapsed = utime.ticks_diff(now, start)  # 可以為負，但差值用在 modulo 前無須擔心

        # 將 elapsed 標準化到正數範圍，並取模得到週期內位置
        # 由於 MicroPython 可能沒有內建的 % 對負數處理保證，先用條件處理
        if elapsed < 0:
            elapsed = -elapsed

        phase = elapsed % cycle_ms

        if phase < on_ms:
            ledr.on()
        else:
            ledr.off()

        # 小延遲，避免 busy-loop 導致高 CPU 使用；50 ms 對 LED 週期足夠精細
        utime.sleep_ms(50)


if __name__ == '__main__':
    main()
