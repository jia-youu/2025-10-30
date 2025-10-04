# OLED 選單 Demo for ePy 擴充版
# 使用 SSD1306 OLED 顯示器實現兩層選單，每層四個選項
# 使用上下鍵移動選項，左鍵選取，反白顯示當前選項
# 選單狀態使用字典記錄

import utime
from machine import I2C, Pin
import lib.ssd1306

# 選單數據：兩層，每層四個選項
menu_data = [
    {
        'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4']
    },
    {
        'options': ['Sub A', 'Sub B', 'Sub C', 'Sub D']
    }
]

# 選單狀態字典
menu_state = {
    'current_layer': 0,  # 當前層 (0 或 1)
    'current_selection': 0,  # 當前選項索引 (0-3)
    'selected_option': None  # 最終選取的選項 (layer, index)
}

# 初始化 OLED 和按鈕


def init_hardware():
    # 初始化 I2C 和 OLED
    i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
    oled = lib.ssd1306.SSD1306_I2C(128, 64, i2c0)
    # 初始化按鈕 (上、下、左、右)
    btn_up = Pin(Pin.epy.P24, Pin.IN, Pin.PULL_UP)
    btn_down = Pin(Pin.epy.P8, Pin.IN, Pin.PULL_UP)
    btn_left = Pin(Pin.epy.P6, Pin.IN, Pin.PULL_UP)
    btn_right = Pin(Pin.epy.P7, Pin.IN, Pin.PULL_UP)
    return oled, btn_up, btn_down, btn_left, btn_right

# 顯示選單


def display_menu(oled, menu_state):
    oled.fill(0)  # 清空螢幕
    layer = menu_state['current_layer']
    selection = menu_state['current_selection']
    options = menu_data[layer]['options']

    for i in range(4):
        y = i * 16  # 每行 16 像素
        if i == selection:
            # 反白當前選項：填充矩形
            oled.fill_rect(0, y, 128, 16, 1)
            oled.text(options[i], 0, y, 0)  # 黑色文字
        else:
            oled.text(options[i], 0, y, 1)  # 白色文字

    oled.show()

# 讀取按鈕輸入


def read_buttons(btn_up, btn_down, btn_left, btn_right):
    up_pressed = btn_up.value() == 0
    down_pressed = btn_down.value() == 0
    left_pressed = btn_left.value() == 0
    right_pressed = btn_right.value() == 0
    return up_pressed, down_pressed, left_pressed, right_pressed

# 打印選單狀態


def print_menu_state():
    """
    打印所有選單的狀態信息
    """
    print("=== 選單狀態 ===")
    print("當前層: {}".format(menu_state['current_layer']))
    print("當前選項索引: {}".format(menu_state['current_selection']))
    if menu_state['selected_option'] is not None:
        layer, index = menu_state['selected_option']
        option_text = menu_data[layer]['options'][index]
        print("最終選取: 層={}, 索引={}, 文字='{}'".format(layer, index, option_text))
    else:
        print("最終選取: 尚未選取")
    print("================")

# 更新選單狀態


def update_menu_state(menu_state, up_pressed, down_pressed, left_pressed, right_pressed):
    if up_pressed:
        menu_state['current_selection'] = (
            menu_state['current_selection'] - 1) % 4
        utime.sleep_ms(200)  # 防抖
    elif down_pressed:
        menu_state['current_selection'] = (
            menu_state['current_selection'] + 1) % 4
        utime.sleep_ms(200)  # 防抖
    elif left_pressed:
        # 選取：如果在第一層，進入第二層；如果在第二層，記錄選取結果並返回第一層
        if menu_state['current_layer'] == 0:
            menu_state['current_layer'] = 1
            menu_state['current_selection'] = 0  # 重置選項
            print_menu_state()  # 打印狀態
        else:
            # 在第二層選取，記錄結果
            menu_state['selected_option'] = (
                menu_state['current_layer'], menu_state['current_selection'])
            menu_state['current_layer'] = 0
            menu_state['current_selection'] = 0
            print_menu_state()  # 打印狀態
        print("------------------")
        utime.sleep_ms(200)  # 防抖
    elif right_pressed:
        # 右鍵：跳回上一層
        if menu_state['current_layer'] > 0:
            menu_state['current_layer'] -= 1
            menu_state['current_selection'] = 0  # 重置選項
        utime.sleep_ms(200)  # 防抖

# 主函數


def menu_demo():
    oled, btn_up, btn_down, btn_left, btn_right = init_hardware()

    while True:
        display_menu(oled, menu_state)
        up, down, left, right = read_buttons(
            btn_up, btn_down, btn_left, btn_right)
        update_menu_state(menu_state, up, down, left, right)
        utime.sleep_ms(50)  # 小延遲以節省 CPU

# 獲取選取的選項結果


def get_selected_option():
    """
    返回最終選取的選項
    返回格式: (layer, index, option_text) 或 None 如果未選取
    """
    if menu_state['selected_option'] is not None:
        layer, index = menu_state['selected_option']
        option_text = menu_data[layer]['options'][index]
        return (layer, index, option_text)
    return None

# 示範函數


def demo():
    # 初始化示例
    from machine import I2C
    i2c0 = I2C(0, I2C.MASTER, baudrate=100000)
    oled = lib.ssd1306.SSD1306_I2C(128, 64, i2c0)
    menu_demo()


if __name__ == "__main__":
    demo()
