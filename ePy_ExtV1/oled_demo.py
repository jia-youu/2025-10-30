# SSD1306 OLED 二層選單 Demo (ePy 擴充板)
# 本範例示範如何在 ePy 擴充板上使用 SSD1306 OLED 顯示二層選單，
# 並以上下左右按鍵操作選單。選單狀態以 dict 記錄。
# 只顯示英文，程式以 function 為主，註解皆為中文。
# 
# 硬體前提：
# - OLED 連接 I2C0 (預設地址 0x3c)
# - 按鍵分別接 上(P24) 下(P8) 左(P6) 右(P7)
#
# 初始化方式：
# from machine import I2C, Pin
# import ssd1306
# i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
# oled = ssd1306.SSD1306_I2C(128, 64, i2c0)

import utime
from machine import I2C, Pin
import ssd1306

# 選單結構 (二層，每層四選項)
MENU = {
    'main': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
    'sub': {
        0: ['A1', 'A2', 'A3', 'A4'],
        1: ['B1', 'B2', 'B3', 'B4'],
        2: ['C1', 'C2', 'C3', 'C4'],
        3: ['D1', 'D2', 'D3', 'D4']
    }
}

# 選單狀態 (用 dict 記錄)
menu_state = {
    'layer': 0,      # 0:主選單, 1:子選單
    'main_idx': 0,  # 主選單選項
    'sub_idx': 0    # 子選單選項
}

# 按鍵初始化 (上/下/左/右)
KEY_UP = Pin(24, Pin.IN, Pin.PULL_UP)
KEY_DOWN = Pin(8, Pin.IN, Pin.PULL_UP)
KEY_LEFT = Pin(6, Pin.IN, Pin.PULL_UP)
KEY_RIGHT = Pin(7, Pin.IN, Pin.PULL_UP)

# OLED 初始化
I2C0 = I2C(0, I2C.MASTER, baudrate=100000)
oled = ssd1306.SSD1306_I2C(128, 64, I2C0)

# 顯示選單 (反白表示選到的選項)
def show_menu():
    oled.fill(0)
    if menu_state['layer'] == 0:
        # 主選單
        for i, item in enumerate(MENU['main']):
            y = 8 + i * 14
            if i == menu_state['main_idx']:
                # 反白
                oled.fill_rect(0, y, 128, 12, 1)
                oled.text(item, 4, y+2, 0)
            else:
                oled.text(item, 4, y+2, 1)
    else:
        # 子選單
        sub_items = MENU['sub'][menu_state['main_idx']]
        for i, item in enumerate(sub_items):
            y = 8 + i * 14
            if i == menu_state['sub_idx']:
                oled.fill_rect(0, y, 128, 12, 1)
                oled.text(item, 4, y+2, 0)
            else:
                oled.text(item, 4, y+2, 1)
    oled.show()

# 按鍵掃描 (回傳按下的鍵名)
def scan_key():
    if KEY_UP.value() == 0:
        return 'UP'
    if KEY_DOWN.value() == 0:
        return 'DOWN'
    if KEY_LEFT.value() == 0:
        return 'LEFT'
    if KEY_RIGHT.value() == 0:
        return 'RIGHT'
    return None

# 主迴圈 demo
# 按鍵說明：UP/DOWN 移動選項，LEFT 選定進入下一層，RIGHT 返回上一層
def demo():
    show_menu()
    while True:
        key = scan_key()
        if key:
            if menu_state['layer'] == 0:
                if key == 'UP':
                    menu_state['main_idx'] = (menu_state['main_idx'] - 1) % 4
                elif key == 'DOWN':
                    menu_state['main_idx'] = (menu_state['main_idx'] + 1) % 4
                elif key == 'LEFT':
                    menu_state['layer'] = 1
                    menu_state['sub_idx'] = 0
                # 主選單不處理 RIGHT
            else:
                if key == 'UP':
                    menu_state['sub_idx'] = (menu_state['sub_idx'] - 1) % 4
                elif key == 'DOWN':
                    menu_state['sub_idx'] = (menu_state['sub_idx'] + 1) % 4
                elif key == 'RIGHT':
                    menu_state['layer'] = 0
                # 子選單不處理 LEFT
            show_menu()
            # 防止重複觸發
            utime.sleep_ms(200)

# 若直接執行本檔案則啟動 demo
if __name__ == '__main__':
    demo()
