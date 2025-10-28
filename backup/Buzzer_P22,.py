# -*- coding: utf-8 -*-
"""
利用 Timer0 切換 P22 腳位驅動蜂鳴器的範例。
外部硬體：P22 經由電晶體放大後接到被動蜂鳴器。
"""

from machine import Pin, Timer
import utime


class Buzzer(object):
    """簡易蜂鳴器控制類別，支援設定頻率與播放時間。"""

    def __init__(self, pin_id=Pin.epy.P22, timer_id=0):
        # 初始化輸出腳位並預設為低電位，確保蜂鳴器靜音
        self._pin = Pin(pin_id, Pin.OUT)
        self._pin.value(0)

        # 預設使用 Timer0，由於 ePy 僅有少量 Timer，建議單一實例使用
        self._timer_id = timer_id
        self._timer = None
        self._timer_active = False

        # 播放狀態管理
        self._active = False
        self._duration_ms = None
        self._start_tick = 0
        self._pin_state = 0

    def _timer_handler(self, timer_obj):
        # Timer 中斷回呼會連續被觸發，用來產生方波
        if not self._active:
            return

        if self._duration_ms is not None:
            now_tick = utime.ticks_ms()
            if utime.ticks_diff(now_tick, self._start_tick) >= self._duration_ms:
                # 時間到後立即停止，以免多餘的觸發
                self.stop()
                return

        # 交替輸出高低電位形成聲波
        if self._pin_state:
            self._pin_state = 0
        else:
            self._pin_state = 1
        self._pin.value(self._pin_state)

    def start(self, frequency_hz, duration_ms=None):
        """以指定頻率開始發聲，duration_ms 為 None 表示持續發聲。"""
        if frequency_hz <= 0:
            raise ValueError("frequency_hz 必須大於 0")

        # 重新初始化時先確認靜音狀態
        self.stop()

        self._active = True
        self._duration_ms = duration_ms
        self._start_tick = utime.ticks_ms()
        self._pin_state = 0
        self._pin.value(0)

        # 為了切換高低電位，Timer 頻率需為欲輸出頻率的 2 倍
        toggle_freq = frequency_hz * 2
        self._timer = Timer(self._timer_id, freq=toggle_freq)
        self._timer.callback(self._timer_handler)
        self._timer_active = True

    def play_tone(self, frequency_hz, duration_ms, tail_ms=60):
        """同步播放一段聲音並等待結束後自動靜音。"""
        self.start(frequency_hz, duration_ms)
        # 留一點緩衝時間，確保 Timer 回呼完成最後一次 stop()
        wait_time = duration_ms + tail_ms
        if wait_time < 0:
            wait_time = 0
        utime.sleep_ms(wait_time)
        self.stop()

    def stop(self):
        """停止發聲並將輸出腳位拉低。"""
        self._active = False
        self._duration_ms = None
        self._pin_state = 0

        if self._timer_active and self._timer is not None:
            # 關閉 Timer 中斷並釋放資源
            self._timer.callback(None)
            self._timer.deinit()
            self._timer_active = False
            self._timer = None

        self._pin.value(0)

    def is_playing(self):
        """回傳目前是否正在播放聲音。"""
        return self._active


if __name__ == "__main__":
    # 此檔案直接在 ePy 開發板執行時進行示範
    buzzer = Buzzer()
    pattern = (
        (523, 200),  # C5
        (659, 200),  # E5
        (784, 300),  # G5
    )

    for freq, duration in pattern:
        buzzer.start(freq, duration)
        # 播放期間阻塞等待，避免與下一個音重疊
        utime.sleep_ms(duration + 80)

    # 休息一段時間後示範長音
    utime.sleep_ms(200)
    buzzer.start(440, 500)
    utime.sleep_ms(560)
    buzzer.play_tone(660, 300)
    buzzer.play_tone(880, 300)
    buzzer.play_tone(988, 400)

    # 確保最終靜音
    buzzer.stop()
