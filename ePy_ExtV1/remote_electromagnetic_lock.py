# 遠端電磁鎖控制程式
# 使用 MeshDevice 模組接收 MDTPG-MSG 訊息
# 根據接收到的 "ON" 或 "OFF" 指令控制 Y LED
# 控制 relay_ctrl Pin 腳位  Pin.epy.P10

from lib.mesh_device import MeshDevice
from machine import Pin
import utime

# 除錯訊息開關：True=顯示所有訊息，False=關閉所有訊息
DEBUG = True


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
        # 30 秒 = 30000 毫秒
        if elapsed_ms >= 30000:
            led.off()
            relay.value(0)
            timeout_info['enabled'] = False
            timeout_info['start_time'] = 0
            debug_print("[電磁鎖] 超時 30 秒，自動關閉")
            return True
    return False


def main(mesh_device, led, relay):
    """
    主程式：持續監聽 MDTGP-MSG 和 MDTSG-MSG 訊息
    mesh_device: MeshDevice 物件
    led: LED 物件
    relay: 繼電器 Pin 物件
    """
    # 超時控制資訊
    timeout_info = {
        'enabled': False,    # 是否啟用超時檢查
        'start_time': 0      # 開啟時間（毫秒）
    }

    # 主迴圈：持續接收並處理訊息
    while True:
        # 檢查是否超時
        check_timeout(timeout_info, led, relay)
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

        # 短暫延遲，避免 CPU 滿載
        utime.sleep_ms(50)


# 程式進入點
if __name__ == "__main__":
    from machine import LED, Pin

    debug_print("=== 遠端電磁鎖控制系統 ===")

    # 初始化硬體（先初始化硬體再初始化通訊）
    debug_print("初始化硬體...")
    relay_ctrl = Pin(Pin.epy.P10, Pin.OUT)
    y_led = LED('ledy')
    y_led.off()
    debug_print("Y LED 和繼電器已初始化")

    # 初始化 MeshDevice (使用 UART0，連接 BLE MESH 模組)
    debug_print("初始化 MeshDevice...")
    mesh = MeshDevice(uart_id=0, baudrate=115200, debug=True)

    # 執行 reboot 並檢查綁定狀態
    debug_print("重啟 Mesh 模組...")
    mesh.reboot(timeout=200)
    debug_print("綁定狀態: {}".format("已綁定" if mesh.is_bound else "未綁定"))
    debug_print("開始監聽 MDTGP-MSG 和 MDTSG-MSG 訊息...")
    debug_print("等待遠端控制指令 (ON/OFF)...\n")

    try:
        main(mesh, y_led, relay_ctrl)
    except KeyboardInterrupt:
        debug_print("\n程式已停止")
    except Exception as e:
        debug_print("錯誤: {}".format(e))
