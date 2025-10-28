# 電磁鎖開關控制程式
# 使用 MeshDevice 模組發送控制指令
# 使用 Pin.epy.P19 控制 Mesh ON/OFF，持續按下時每 0.5 秒發送 "ON"，放開後 5 秒發送 "OFF"
# 使用 Pin.epy.P24 控制 Mesh 綁定狀態，長按 5 秒解除綁定
# ledg 綠燈顯示綁定狀態（綁定長亮、未綁定閃爍），可透過 DEBUG 變數控制除錯訊息輸出

from mesh_device import MeshDevice
from machine import Pin, LED
import utime

# 除錯訊息開關：True=顯示所有訊息，False=關閉所有訊息
DEBUG = False

# 長按解除 Mesh 綁定所需時間（毫秒）
UNBIND_PRESS_DURATION_MS = 5000

# 未綁定時 LED 閃爍間隔（毫秒）
LED_BLINK_INTERVAL_MS = 400

# Mesh 指令常數（UART 傳輸需使用 bytes）
COMMAND_ON = b"ON"
COMMAND_OFF = b"OFF"

# 持續按下時重送 ON 指令的間隔（毫秒）
COMMAND_REPEAT_INTERVAL_MS = 500

# 放開按鈕後發送 OFF 指令的延遲（毫秒）
COMMAND_RELEASE_DELAY_MS = 5000

# Mesh UART 設定
MESH_UART_ID = 1
MESH_BAUDRATE = 115200

# Mesh 接收等待時間（毫秒）
MESH_RECV_TIMEOUT_MS = 50


def debug_print(msg):
    """
    可控制的除錯訊息輸出函式
    當 DEBUG 為 True 時才會印出訊息
    msg: 要輸出的訊息字串
    """
    if DEBUG:
        print(msg)


def init_command_button():
    """
    初始化控制 ON/OFF 的按鈕腳位 Pin.epy.P19
    設定為輸入模式，並啟用上拉電阻
    回傳: Pin 物件
    """
    button = Pin.epy.P19
    button.init(Pin.IN, Pin.PULL_UP)
    debug_print("[初始化] 指令按鈕 Pin.epy.P19 設定完成")
    return button


def init_control_button():
    """
    初始化綁定控制按鈕腳位 Pin.epy.P24
    設定為輸入模式，並啟用上拉電阻
    回傳: Pin 物件
    """
    button = Pin.epy.P24
    button.init(Pin.IN, Pin.PULL_UP)
    debug_print("[初始化] 綁定按鈕 Pin.epy.P24 設定完成")
    return button


def init_status_led():
    """
    初始化綠色狀態 LED (ledg)
    預設熄滅以表示未綁定狀態
    回傳: LED 物件
    """
    led = LED('ledg')
    led.off()
    debug_print("[初始化] LED ledg 設定完成")
    return led


def init_command_state():
    """
    建立指令按鈕狀態紀錄字典
    回傳: 包含 last_state、released_time、last_on_send、off_sent 的字典
    """
    return {
        'last_state': 1,
        'released_time': 0,
        'last_on_send': 0,
        'off_sent': True
    }


def reset_command_state(state):
    """
    重設指令按鈕的狀態，常用於 Mesh 未綁定或解除綁定後
    state: 指令按鈕狀態字典
    """
    state['last_state'] = 1
    state['released_time'] = 0
    state['last_on_send'] = 0
    state['off_sent'] = True


def init_control_state():
    """
    建立綁定按鈕狀態紀錄字典
    回傳: 包含 last_state、press_start、long_press_triggered 的字典
    """
    return {
        'last_state': 1,
        'press_start': 0,
        'long_press_triggered': False
    }


def reset_control_state(state):
    """
    重設綁定按鈕的狀態，避免上一循環的按壓資訊干擾
    state: 綁定按鈕狀態字典
    """
    state['last_state'] = 1
    state['press_start'] = 0
    state['long_press_triggered'] = False


def handle_command_button(mesh, state, current_state, state_changed, current_time):
    """
    處理指令按鈕的 ON/OFF 控制邏輯
    mesh: MeshDevice 物件
    state: 指令按鈕狀態字典
    current_state: 目前按鍵狀態（0=按下, 1=放開）
    state_changed: 是否觸發狀態變化
    current_time: utime.ticks_ms() 取得的時間戳
    """
    if state_changed:
        if current_state == 0:
            debug_print("[P19] 指令按鈕按下")
            send_command(mesh, COMMAND_ON)
            state['last_on_send'] = current_time
            state['off_sent'] = False
            state['released_time'] = 0
        else:
            debug_print("[P19] 指令按鈕放開")
            if not state['off_sent']:
                wait_seconds = COMMAND_RELEASE_DELAY_MS // 1000
                debug_print("[計時] {} 秒後發送 OFF".format(wait_seconds))
                state['released_time'] = current_time
            else:
                state['released_time'] = 0

    if current_state == 0:
        if state['last_on_send'] == 0:
            state['last_on_send'] = current_time
        else:
            elapsed = utime.ticks_diff(current_time, state['last_on_send'])
            if elapsed >= COMMAND_REPEAT_INTERVAL_MS:
                send_command(mesh, COMMAND_ON)
                state['last_on_send'] = current_time
    elif not state['off_sent'] and state['released_time'] > 0:
        elapsed_release = utime.ticks_diff(
            current_time, state['released_time'])
        if elapsed_release >= COMMAND_RELEASE_DELAY_MS:
            debug_print("[計時] {} 秒已到，發送 OFF 指令".format(
                COMMAND_RELEASE_DELAY_MS // 1000))
            send_command(mesh, COMMAND_OFF)
            state['off_sent'] = True
            state['released_time'] = 0


def handle_control_button(mesh, control_state, command_state, current_state, state_changed, current_time):
    """
    處理綁定控制按鈕的長按與解除綁定邏輯
    mesh: MeshDevice 物件
    control_state: 綁定按鈕狀態字典
    command_state: 指令按鈕狀態字典（解除綁定後需同步重設）
    current_state: 目前按鍵狀態（0=按下, 1=放開）
    state_changed: 是否觸發狀態變化
    current_time: utime.ticks_ms() 取得的時間戳
    回傳: True=剛完成解除綁定，False=尚未解除
    """
    unbind_triggered = False

    if state_changed:
        if current_state == 0:
            debug_print("[P24] 綁定按鈕按下")
            control_state['press_start'] = current_time
            control_state['long_press_triggered'] = False
        else:
            debug_print("[P24] 綁定按鈕放開")
            control_state['press_start'] = 0
            control_state['long_press_triggered'] = False

    if current_state == 0 and control_state['press_start'] > 0 and not control_state['long_press_triggered']:
        press_duration = utime.ticks_diff(
            current_time, control_state['press_start'])
        if press_duration >= UNBIND_PRESS_DURATION_MS:
            wait_seconds = UNBIND_PRESS_DURATION_MS // 1000
            debug_print("[P24] 長按 {} 秒，執行 Mesh 解除綁定".format(wait_seconds))
            mesh.unbind()
            reset_command_state(command_state)
            control_state['long_press_triggered'] = True
            control_state['press_start'] = 0
            unbind_triggered = True

    return unbind_triggered


def process_mesh_message(msg):
    """
    處理 Mesh 回傳的訊息，統一進行除錯輸出
    msg: (msg_type, content) 的 tuple
    """
    msg_type, content = msg

    if msg_type == 'MDTS-MSG':
        if content == b'SUCCESS':
            debug_print("[Mesh] 指令發送成功確認")
        elif isinstance(content, dict):
            debug_print("[Mesh] 收到來自 {} 的資料: {}".format(
                content['sender'], content['data']))
        else:
            debug_print("[Mesh] 一般訊息內容: {}".format(content))
    elif msg_type == 'MDTS-ERR':
        debug_print("[Mesh] 錯誤訊息: {}".format(content))
    elif msg_type in ('MDTS-EVT', 'MDTS-STATUS'):
        debug_print("[Mesh] 狀態更新 {}: {}".format(msg_type, content))
    else:
        debug_print("[Mesh] {} 訊息: {}".format(msg_type, content))


def update_led_indicator(led, is_bound, blink_info, current_time):
    """
    根據 Mesh 綁定狀態更新 LED 顯示
    led: LED 物件
    is_bound: 是否已綁定
    blink_info: 閃爍狀態資訊字典
    current_time: 當前時間戳（utime.ticks_ms() 取得）
    """
    if is_bound:
        # 綁定時維持長亮
        if blink_info['enabled'] or not blink_info['is_on']:
            led.on()
            blink_info['enabled'] = False
            blink_info['is_on'] = True
            blink_info['last_toggle'] = None
    else:
        # 未綁定時啟用閃爍提示
        if not blink_info['enabled']:
            blink_info['enabled'] = True
            blink_info['is_on'] = False
            blink_info['last_toggle'] = current_time
            led.off()
        else:
            if blink_info['last_toggle'] is None:
                blink_info['last_toggle'] = current_time
            elapsed = utime.ticks_diff(
                current_time, blink_info['last_toggle'])
            if elapsed >= blink_info['interval']:
                if blink_info['is_on']:
                    led.off()
                else:
                    led.on()
                blink_info['is_on'] = not blink_info['is_on']
                blink_info['last_toggle'] = current_time


def check_button_state(button, last_state):
    """
    檢查按鈕狀態變化
    button: Pin 物件
    last_state: 上一次的按鈕狀態（0=按下，1=放開）
    回傳: (current_state, state_changed)
    """
    current_state = button.value()
    state_changed = (current_state != last_state)
    return current_state, state_changed


def send_command(mesh, command):
    """
    透過 Mesh 發送控制指令
    mesh: MeshDevice 物件
    command: 要發送的指令資料（b"ON" 或 b"OFF"）
    回傳: True=發送成功，False=發送失敗
    """
    if not mesh.is_bound:
        debug_print("[錯誤] Mesh 裝置未綁定，無法發送指令")
        return False

    success = mesh.set_data(command)
    if success:
        debug_print("[發送] 指令: {}".format(command))
    else:
        debug_print("[錯誤] 指令發送失敗: {}".format(command))
    return success


def main_loop():
    """
    主程式迴圈
    持續監控按鈕狀態並發送對應的 Mesh 指令
    """
    debug_print("=" * 40)
    debug_print("電磁鎖開關控制程式啟動")
    debug_print("=" * 40)

    # 初始化 MeshDevice 物件（使用 UART1）
    debug_print("[初始化] 建立 MeshDevice 連線...")
    mesh = MeshDevice(uart_id=MESH_UART_ID,
                      baudrate=MESH_BAUDRATE, debug=DEBUG)

    # 執行 reboot 並檢查綁定狀態
    debug_print("[初始化] 執行 reboot 檢查綁定狀態...")
    mesh.reboot()

    if mesh.is_bound:
        debug_print("[狀態] Mesh 已綁定，UID: {}".format(mesh.uid))
    else:
        debug_print("[警告] Mesh 未綁定，請先完成配對")

    # 初始化兩顆按鈕與狀態 LED
    command_button = init_command_button()
    control_button = init_control_button()
    status_led = init_status_led()
    led_blink_info = {
        'enabled': False,
        'last_toggle': None,
        'is_on': False,
        'interval': LED_BLINK_INTERVAL_MS
    }

    # 狀態變數
    command_state_info = init_command_state()
    control_state_info = init_control_state()
    previous_bound_state = None  # 前一次記錄的綁定狀態

    debug_print("[就緒] 開始監控按鈕狀態...")
    debug_print("提示: Mesh 綁定時可使用 P19 傳送指令、P24 長按解除綁定")
    debug_print("-" * 40)

    while True:
        loop_now = utime.ticks_ms()

        if mesh.is_bound:
            # 檢查兩顆按鈕的狀態
            command_value, command_changed = check_button_state(
                command_button, command_state_info['last_state'])
            control_value, control_changed = check_button_state(
                control_button, control_state_info['last_state'])

            handle_command_button(
                mesh, command_state_info, command_value, command_changed, loop_now)
            if handle_control_button(
                    mesh, control_state_info, command_state_info, control_value,
                    control_changed, loop_now):
                loop_now = utime.ticks_ms()

            command_state_info['last_state'] = command_value
            control_state_info['last_state'] = control_value
        else:
            # 未綁定時不處理按鈕事件，重設相關狀態
            reset_command_state(command_state_info)
            reset_control_state(control_state_info)

        # 接收 Mesh 訊息（持續監聽）
        msg = mesh.recv_data(timeout=MESH_RECV_TIMEOUT_MS)
        if msg:
            process_mesh_message(msg)

        # 綁定狀態改變時更新 LED 指示與除錯訊息
        if mesh.is_bound != previous_bound_state:
            if mesh.is_bound:
                debug_print("[LED] Mesh 已綁定，ledg 長亮")
            else:
                debug_print("[LED] Mesh 未綁定，ledg 閃爍提示")
            previous_bound_state = mesh.is_bound

        # 更新 LED 顯示狀態
        update_led_indicator(status_led, mesh.is_bound,
                             led_blink_info, loop_now)

        # 短暫延遲，避免過度佔用 CPU
        utime.sleep_ms(50)


# 程式進入點
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        debug_print("\n[結束] 程式被使用者中斷")
    except Exception as e:
        debug_print("[錯誤] 發生異常: {}".format(e))
