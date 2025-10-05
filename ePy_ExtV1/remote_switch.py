# 電磁鎖開關控制程式
# 使用 MeshDevice 模組發送控制指令
# 監控 Pin.epy.P24 按鈕狀態，持續按下時每 0.5 秒發送 "ON"，放開後 5 秒發送 "OFF"
# 可透過 DEBUG 變數控制除錯訊息輸出

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


def init_switch_button():
    """
    初始化按鈕腳位 Pin.epy.P24 or P19
    設定為輸入模式，並啟用上拉電阻
    回傳: Pin 物件
    """
    button = Pin.epy.P24
    button.init(Pin.IN, Pin.PULL_UP)
    debug_print("[初始化] 按鈕 Pin.epy.P24 設定完成")
    return button


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
    command: 要發送的指令字串（"ON" 或 "OFF"）
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

    # 初始化 MeshDevice 物件（使用 UART0）
    debug_print("[初始化] 建立 MeshDevice 連線...")
    mesh = MeshDevice(uart_id=0, baudrate=115200, debug=DEBUG)

    # 執行 reboot 並檢查綁定狀態
    debug_print("[初始化] 執行 reboot 檢查綁定狀態...")
    mesh.reboot()

    if mesh.is_bound:
        debug_print("[狀態] Mesh 已綁定，UID: {}".format(mesh.uid))
    else:
        debug_print("[警告] Mesh 未綁定，請先完成配對")

    # 初始化按鈕
    button = init_switch_button()

    # 狀態變數
    last_button_state = 1  # 初始狀態為放開（1）
    button_released_time = 0  # 按鈕放開的時間戳記
    last_on_send_time = 0  # 上次發送 ON 的時間戳記
    off_command_sent = True  # 是否已發送 OFF 指令（初始為 True 避免重複發送）

    debug_print("[就緒] 開始監控按鈕狀態...")
    debug_print("提示: 按下按鈕每 0.5 秒發送 ON，放開後 5 秒發送 OFF")
    debug_print("-" * 40)

    while True:
        # 檢查按鈕狀態
        current_state, state_changed = check_button_state(
            button, last_button_state)

        # 按鈕狀態改變時的處理
        if state_changed:
            if current_state == 0:
                # 按鈕被按下（Low）
                debug_print("[按鈕] 按下偵測")
                send_command(mesh, "ON")
                last_on_send_time = utime.ticks_ms()  # 記錄首次發送 ON 的時間
                off_command_sent = False  # 重置 OFF 指令標記

            else:
                # 按鈕被放開（High）
                debug_print("[按鈕] 放開偵測，5 秒後將發送 OFF")
                button_released_time = utime.ticks_ms()  # 記錄放開時間

        # 按鈕持續被按下時，每 0.5 秒發送一次 ON
        if current_state == 0:
            elapsed_since_last_on = utime.ticks_diff(
                utime.ticks_ms(), last_on_send_time)
            if elapsed_since_last_on >= 500:  # 0.5 秒 = 500 毫秒
                send_command(mesh, "ON")
                last_on_send_time = utime.ticks_ms()  # 更新發送時間

        # 檢查是否需要發送 OFF 指令（按鈕放開後 5 秒）
        if current_state == 1 and not off_command_sent and button_released_time > 0:
            elapsed_time = utime.ticks_diff(
                utime.ticks_ms(), button_released_time)
            if elapsed_time >= 5000:  # 5 秒 = 5000 毫秒
                debug_print("[計時] 5 秒已到，發送 OFF 指令")
                send_command(mesh, "OFF")
                off_command_sent = True  # 標記已發送，避免重複

        # 更新按鈕狀態
        last_button_state = current_state

        # 接收 Mesh 訊息（持續監聽）
        msg = mesh.recv_data(timeout=50)
        if msg:
            msg_type, content = msg
            if msg_type == 'MDTS-MSG':
                if content == b'SUCCESS':
                    debug_print("[Mesh] 指令發送成功確認")
                elif isinstance(content, dict):
                    debug_print("[Mesh] 收到來自 {} 的資料: {}".format(
                        content['sender'], content['data']))
            else:
                debug_print("[Mesh] {} 訊息: {}".format(msg_type, content))

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
