    # 遠端電磁鎖控制程式
# 使用 MeshDevice 模組接收 MDTPG-MSG 訊息
# 根據接收到的 "ON" 或 "OFF" 指令控制 Y LED
# 控制 relay_ctrl Pin 腳位  Pin.epy.P10

from mesh_device import MeshDevice
from machine import Pin
import utime

# 長按解除綁定所需時間（毫秒）
UNBIND_PRESS_DURATION_MS = 5000
# 未綁定時 LED 閃爍間隔（毫秒）
LED_BLINK_INTERVAL_MS = 400

# 除錯訊息開關：True=顯示所有訊息，False=關閉所有訊息
DEBUG = False


def debug_print(msg):
    """
    可控制的除錯訊息輸出函式
    當 DEBUG 為 True 時才會印出訊息
    msg: 要輸出的訊息字串
    """
    if DEBUG:
        print(msg)


def hex_to_text(hex_str):
    """
    將十六進制字串轉換為文字
    hex_str: 十六進制字串，例如 "4F4E" (ON)
    回傳: 解碼後的文字字串
    """
    chars = []
    # 每兩個字元組成一個 byte
    for i in range(0, len(hex_str), 2):
        hex_byte = hex_str[i:i+2]
        # 轉換為整數再轉為字元
        char_code = int(hex_byte, 16)
        chars.append(chr(char_code))
    return ''.join(chars)


def control_lock(command, led, relay, timeout_info):
    """
    根據指令控制電磁鎖（目前使用 LED 模擬）
    command: "ON" 或 "OFF" 字串
    led: LED 物件
    relay: 繼電器 Pin 物件
    timeout_info: 超時資訊字典，包含 'enabled' 和 'start_time'
    """
    if command == "ON":
        led.on()
        relay.value(1)
        # 點亮 LED（開啟電磁鎖）
        # 啟動 30 秒超時計時器
        timeout_info['enabled'] = True
        timeout_info['start_time'] = utime.ticks_ms()
        debug_print("[電磁鎖] 已開啟 (30秒後自動關閉)")
    elif command == "OFF":
        led.off()
        relay.value(0)
        # 關閉超時計時器
        timeout_info['enabled'] = False
        timeout_info['start_time'] = 0
        debug_print("[電磁鎖] 已關閉")
    else:
        debug_print("[電磁鎖] 未知指令: {}".format(command))


def check_timeout(timeout_info, led, relay):
    """
    檢查是否超過 30 秒，如果超時則自動關閉
    timeout_info: 超時資訊字典
    led: LED 物件
    relay: 繼電器 Pin 物件
    回傳: True 表示發生超時並自動關閉
    """
    if timeout_info['enabled']:
        elapsed_ms = utime.ticks_diff(
            utime.ticks_ms(), timeout_info['start_time'])
        # 3 秒 = 3000 毫秒
        if elapsed_ms >= 3000:
            led.off()
            relay.value(0)
            timeout_info['enabled'] = False
            timeout_info['start_time'] = 0
            debug_print("[電磁鎖] 超時 3 秒，自動關閉")
            return True
    return False


def update_status_led(status_led, is_bound, blink_info):
    """
    根據 Mesh 綁定狀態更新綠燈顯示
    status_led: LED 物件 (ledg)
    is_bound: 是否已綁定
    blink_info: 閃爍狀態字典，包含 enabled、is_on、last_toggle、interval
    """
    if is_bound:
        # 綁定時維持長亮
        if blink_info['enabled'] or not blink_info['is_on']:
            status_led.on()
            blink_info['enabled'] = False
            blink_info['is_on'] = True
    else:
        if not blink_info['enabled']:
            # 第一次進入未綁定狀態，先熄滅等待閃爍
            blink_info['enabled'] = True
            blink_info['is_on'] = False
            blink_info['last_toggle'] = utime.ticks_ms()
            status_led.off()
        else:
            elapsed = utime.ticks_diff(
                utime.ticks_ms(), blink_info['last_toggle'])
            if elapsed >= blink_info['interval']:
                if blink_info['is_on']:
                    status_led.off()
                else:
                    status_led.on()
                blink_info['is_on'] = not blink_info['is_on']
                blink_info['last_toggle'] = utime.ticks_ms()


def monitor_unbind_key(mesh_device, key_button, key_state):
    """
    監控 P24 綁定控制鍵是否長按 5 秒
    mesh_device: MeshDevice 物件
    key_button: Pin 物件 (P24)
    key_state: 狀態字典，包含 last_state、press_start、long_press_triggered
    回傳: True 代表已觸發解除綁定
    """
    if not mesh_device.is_bound:
        # 未綁定時不檢查，並重置狀態
        key_state['press_start'] = 0
        key_state['long_press_triggered'] = False
        key_state['last_state'] = 1
        return False

    current_state = key_button.value()
    triggered = False

    if current_state != key_state['last_state']:
        if current_state == 0:
            debug_print("[P24] 綁定控制鍵按下")
            key_state['press_start'] = utime.ticks_ms()
            key_state['long_press_triggered'] = False
        else:
            debug_print("[P24] 綁定控制鍵放開")
            key_state['press_start'] = 0
            key_state['long_press_triggered'] = False

    if (current_state == 0 and key_state['press_start'] > 0 and
            not key_state['long_press_triggered']):
        press_duration = utime.ticks_diff(
            utime.ticks_ms(), key_state['press_start'])
        if press_duration >= UNBIND_PRESS_DURATION_MS:
            debug_print("[P24] 長按 5 秒，執行解除綁定")
            mesh_device.unbind()
            key_state['long_press_triggered'] = True
            triggered = True

    key_state['last_state'] = current_state
    return triggered


def main(mesh_device, led, relay, status_led, control_key):
    """
    主程式：持續監聽 MDTGP-MSG 和 MDTSG-MSG 訊息
    mesh_device: MeshDevice 物件
    led: LED 物件
    relay: 繼電器 Pin 物件
    status_led: 綠色狀態 LED 物件 (ledg)
    control_key: 綁定控制按鍵 Pin 物件 (P24)
    """
    # 超時控制資訊
    timeout_info = {
        'enabled': False,    # 是否啟用超時檢查
        'start_time': 0      # 開啟時間（毫秒）
    }

    # 綁定狀態 LED 閃爍資訊
    led_blink_info = {
        'enabled': False,
        'last_toggle': utime.ticks_ms(),
        'is_on': False,
        'interval': LED_BLINK_INTERVAL_MS
    }

    # 綁定控制鍵狀態
    key_state = {
        'last_state': 1,
        'press_start': 0,
        'long_press_triggered': False
    }

    previous_bound_state = None

    # 主迴圈：持續接收並處理訊息
    while True:
        # 檢查是否超時
        check_timeout(timeout_info, led, relay)
        # 更新綁定提示燈號
        update_status_led(status_led, mesh_device.is_bound, led_blink_info)

        # 監控解除綁定長按鍵，僅在已綁定時生效
        if monitor_unbind_key(mesh_device, control_key, key_state):
            led.off()
            relay.value(0)
            timeout_info['enabled'] = False
            timeout_info['start_time'] = 0
            debug_print("[電磁鎖] 已解除綁定，鎖定狀態重設為關閉")

        # 接收 mesh device 資料
        msg = mesh_device.recv_data(timeout=100)

        if msg:
            msg_type, content = msg
            debug_print("收到訊息類型: {}, 內容: {}".format(msg_type, content))

            # 檢查是否為 MDTGP-MSG 或 MDTSG-MSG 訊息（裝置間推播或來自配置主機）
            if msg_type in ['MDTGP-MSG', 'MDTSG-MSG', 'MDTS-MSG']:
                # 處理 MDTGP-MSG 和 MDTSG-MSG（資料訊息）
                if msg_type in ['MDTGP-MSG', 'MDTSG-MSG']:
                    debug_print("[接收] {} 訊息".format(msg_type))

                    # content 可能是 bytes 或 dict
                    if isinstance(content, dict):
                        sender = content.get('sender', '未知')
                        data = content.get('data', b'')
                        debug_print("  來源: {}".format(sender))
                        debug_print("  原始資料: {}".format(data))

                        # 將 bytes 轉為十六進制字串
                        hex_str = ''.join(['{:02X}'.format(byte)
                                          for byte in data])

                        # 將十六進制轉為文字
                        text = hex_to_text(hex_str)
                        debug_print("  解碼內容: {}".format(text))

                        # 執行控制
                        control_lock(text, led, relay, timeout_info)
                    elif isinstance(content, bytes):
                        # 直接是 bytes 格式，將 bytes 轉為字串
                        text = ''.join([chr(byte) for byte in content])
                        debug_print("  內容: {}".format(text))
                        control_lock(text, led, relay, timeout_info)

                # 處理 MDTS-MSG（資料傳送確認訊息）
                elif msg_type == 'MDTS-MSG':
                    if content == b'SUCCESS':
                        debug_print("[系統] 資料傳送成功")

        # 綁定狀態改變時輸出提示訊息
        if mesh_device.is_bound != previous_bound_state:
            if mesh_device.is_bound:
                debug_print("[狀態] Mesh 已綁定，綠燈長亮")
            else:
                debug_print("[狀態] Mesh 未綁定，綠燈閃爍提示")
                led_blink_info['enabled'] = False
                led_blink_info['is_on'] = False
                led_blink_info['last_toggle'] = utime.ticks_ms()
            previous_bound_state = mesh_device.is_bound

        # 短暫延遲，避免 CPU 滿載
        utime.sleep_ms(50)


# 程式進入點
if __name__ == "__main__":
    from machine import LED, Pin

    debug_print("=== 遠端電磁鎖控制系統 ===")

    # 初始化硬體（先初始化硬體再初始化通訊）
    debug_print("初始化硬體...")
    relay_ctrl = Pin(Pin.epy.P10, Pin.OUT)
    relay_ctrl.value(0)  # 預設關閉電磁鎖
    y_led = LED('ledy')
    y_led.off()
    g_led = LED('ledg')
    g_led.off()
    control_key = Pin.epy.P24
    control_key.init(Pin.IN, Pin.PULL_UP)
    debug_print("綠燈與綁定控制鍵已初始化")
    debug_print("Y LED 和繼電器已初始化")

    # 初始化 MeshDevice (使用 UART0，連接 BLE MESH 模組)
    debug_print("初始化 MeshDevice...")
    mesh = MeshDevice(uart_id=1, baudrate=115200, debug=True)

    # 執行 reboot 並檢查綁定狀態
    debug_print("重啟 Mesh 模組...")
    mesh.reboot(timeout=200)
    debug_print("綁定狀態: {}".format("已綁定" if mesh.is_bound else "未綁定"))
    debug_print("開始監聽 MDTGP-MSG 和 MDTSG-MSG 訊息...")
    debug_print("等待遠端控制指令 (ON/OFF)...\n")

    try:
        main(mesh, y_led, relay_ctrl, g_led, control_key)
    except KeyboardInterrupt:
        debug_print("\n程式已停止")
    except Exception as e:
        debug_print("錯誤: {}".format(e))
