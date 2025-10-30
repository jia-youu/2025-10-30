"""
traffic_light.py

範例：使用板上三顆 LED (ledg, ledy, ledr) 做成紅綠燈循環。

行為：
  - 綠燈亮 6 秒
  - 黃燈亮 2 秒
  - 紅燈亮 6 秒

注意：使用 utime.ticks_ms() 做 polling，比較適合 MicroPython/ePy 環境。
補充說明：綠+黃+紅的時間合計為 14 秒，因此週期為 14,000 ms（注意使用者原始要求提到 12 秒，但顏色時長總和為 14 秒，本檔案以顏色時長為準實作；如需強制週期 12 秒，請回覆我會調整）。
"""

from machine import LED
import utime


def main():
    """主程式：持續執行紅綠燈循環。"""
    try:
        led_g = LED('ledg')
        led_y = LED('ledy')
        led_r = LED('ledr')
    except Exception:
        print('無法建立 LED 物件，請確認硬體或 API 名稱（應為 "ledg","ledy","ledr"）')
        return

    # 時間以毫秒為單位
    green_ms = 6000
    yellow_ms = 2000
    red_ms = 6000

    cycle_ms = green_ms + yellow_ms + red_ms  # 14000 ms

    start = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()
        elapsed = utime.ticks_diff(now, start)

        # 保證為正數以方便取模
        if elapsed < 0:
            elapsed = -elapsed

        phase = elapsed % cycle_ms

        # 根據 phase 決定哪顆燈亮（其餘關閉）
        if phase < green_ms:
            # 綠燈
            led_g.on()
            led_y.off()
            led_r.off()
        elif phase < (green_ms + yellow_ms):
            # 黃燈
            led_g.off()
            led_y.on()
            led_r.off()
        else:
            # 紅燈
            led_g.off()
            led_y.off()
            led_r.on()

        # 小延遲，避免 busy-loop；100 ms 對於 LED 變化足夠
        utime.sleep_ms(100)


if __name__ == '__main__':
    main()
