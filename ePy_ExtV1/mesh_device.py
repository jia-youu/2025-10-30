# MicroPython MeshDevice 物件，封裝 UART 初始化與狀態管理
# 註解皆為中文，遵守 PEP8
from machine import UART
import utime


class MeshDevice:
    def __init__(self, uart_id=0, baudrate=115200, tx=None, rx=None, debug=False):
        """
        初始化 MeshDevice 物件，設定 UART 連線
        uart_id: UART 埠號 (ePy BLE Mesh 預設為 1)
        baudrate: 傳輸速率 (預設 115200)
        tx, rx: 可選，指定 TX/RX 腳位
        debug: 是否啟用除錯輸出 (預設 False)
        """
        if tx is not None and rx is not None:
            self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx)
        else:
            self.uart = UART(uart_id, baudrate=baudrate)
        self.is_bound = False  # 綁定狀態
        self.last_status = None  # 儲存最近一次狀態訊息
        self.uid = None  # 儲存設備 UID
        self.debug = debug  # 除錯輸出開關
        # 清空 UART buffer
        self.uart.read(self.uart.any())

    def _debug_print(self, *args, **kwargs):
        """
        條件性除錯輸出，只有在 debug=True 時才輸出
        """
        if self.debug:
            print(*args, **kwargs)

    def _parse_provision_status(self, line):
        """
        解析綁定狀態訊息並更新內部狀態
        line: 接收到的 UART 訊息 (bytes)
        回傳: True 表示訊息已處理，False 表示非狀態訊息
        """
        if b'SYS-MSG DEVICE PROV-ED' in line or b'PROV-MSG SUCCESS' in line:
            # 取得 UID
            parts = line.strip().split(b' ')
            if len(parts) >= 1:
                self.uid = self.bytes_to_str(parts[-1])
            self.is_bound = True
            self.last_status = 'PROV-ED'
            return True
        elif b'SYS-MSG DEVICE UNPROV' in line:
            self.is_bound = False
            self.last_status = 'UNPROV'
            self.uid = None
            return True
        return False

    def reboot(self, timeout=2000):
        """
        送出 AT+REBOOT 指令，並解析回應判斷是否已綁定
        timeout: 等待回應的毫秒數
        """
        self.uart.write(b'AT+REBOOT\r\n')
        start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start) < timeout:
            if self.uart.any():
                line = self.uart.readline()
                if not line:
                    continue
                self._debug_print("REBOOT 回應:", line.strip())
                # 使用統一方法解析綁定狀態
                if self._parse_provision_status(line):
                    break
                # 其他回應如 REBOOT-MSG SUCCESS 可略過
        return self.is_bound

    def unbind(self):
        """
        送出 AT+NR 指令，解除綁定
        """
        self.uart.write(b'AT+NR\r\n')
        # 解除綁定後，狀態設為未綁定
        self.is_bound = False

    def str_to_bytes(self, s):
        """
        將純英文數字字串轉 bytes（無 encode）
        """
        b = bytearray()
        for c in s:
            b.append(ord(c))
        return bytes(b)

    def set_data(self, data):
        """
        設定自身資料，需已綁定才可傳送
        data: bytes 或 str (自動轉 bytes)
        """
        if not self.is_bound:
            # 未綁定不可設定資料
            return False
        # 將數字先轉為字串
        if isinstance(data, (int, float)):
            data = str(data)
        # 將字串轉為 hex 字串（大寫），再轉 bytes
        if isinstance(data, str):
            hexstr = ''
            for c in data:
                hexstr += '{:02X}'.format(ord(c))
            data = self.str_to_bytes(hexstr)

        # 限制 data 長度 < 20 bytes，過長自動截斷
        if len(data) > 20:
            data = data[:20]
        # AT+MDTS=<data>\r\n
        cmd = b'AT+MDTS 0 ' + data + b'\r\n'
        self.uart.write(cmd)
        return True

    def recv_data(self, timeout=50):
        """
        接收 UART 資料，解析 MDTSG-MSG、MDTPG、綁定/解綁訊息
        timeout: 等待資料的毫秒數
        回傳 (msg_type, content) 或 None
        """
        start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start) < timeout:
            if self.uart.any():
                buffer = self.uart.readline()
                if not buffer:
                    continue
                # 綁定/解綁狀態即時判斷
                if self._parse_provision_status(buffer):
                    if self.is_bound:
                        self._debug_print("[系統] 已綁定，UID:{}".format(self.uid))
                    else:
                        self._debug_print("[系統] 已解除綁定")
                    continue
                # 嘗試解析 MDTS-MSG (設定資料訊息)
                if b'MDTS-MSG' in buffer:
                    if b'MDTS-MSG SUCCESS' in buffer:
                        # 情況 1: 自己傳送資料成功的確認訊息
                        return
                        # return ('MDTS-MSG', b'SUCCESS')
                    else:
                        # 情況 2: 從其他 provision 節點收到資料
                        # 格式: MDTS-MSG 0x0028 0 31
                        parts = buffer.strip().split(b' ')
                        if len(parts) >= 4:
                            sender = self.bytes_to_str(
                                parts[1])  # 0x0028 (發送者地址)
                            data = self.bytes_to_str(parts[3])    # 31 (資料內容)
                            return ('MDTS-MSG', {'sender': sender, 'data': data})
                # 嘗試解析 MDTSG-MSG
                idx = buffer.find(b'MDTSG-MSG:')
                if idx >= 0:
                    msg = buffer[idx+10:]
                    return ('MDTSG-MSG', msg.strip())
                idx2 = buffer.find(b'MDTPG:')
                if idx2 >= 0:
                    msg = buffer[idx2+6:]
                    return ('MDTPG', msg.strip())
                self._debug_print("其他訊息:", buffer.strip())
        return None

    def bytes_to_str(self, b):
        """
        將 bytes 逐字元轉為 str（無 decode）
        """
        chars = []
        for c in b:
            chars.append(chr(c))
        return ''.join(chars)


if __name__ == "__main__":
    # 測試 MeshDevice 物件功能，支援按鍵控制與即時狀態更新
    from machine import Pin

    print("初始化 MeshDevice 物件...")
    mesh = MeshDevice(uart_id=0, baudrate=115200, debug=True)  # 測試時啟用除錯輸出
    print("執行 reboot() 並判斷綁定狀態...")
    mesh.reboot()
    print("目前綁定狀態: {}".format(mesh.is_bound))

    # 設定按鍵（上：P24， 下：P8）
    key_up = Pin.epy.P24
    key_down = Pin.epy.P8
    key_up.init(Pin.IN, Pin.PULL_UP)
    key_down.init(Pin.IN, Pin.PULL_UP)

    send_count = 1
    print("進入主迴圈，按上鍵解除綁定，按下鍵傳送資料。隨時接收訊息...")
    while True:
        # 按鍵偵測
        if mesh.is_bound and key_up.value() == 0:
            print("[操作] 上鍵按下，執行解除綁定...")
            mesh.unbind()
            utime.sleep_ms(300)  # 去彈跳
        if mesh.is_bound and key_down.value() == 0:
            print("[操作] 下鍵按下，傳送資料: {}".format(send_count))
            mesh.set_data(str(send_count))
            send_count += 1
            utime.sleep_ms(300)
        # 不論綁定與否都持續接收訊息，並即時更新狀態
        msg = mesh.recv_data(timeout=200)
        if msg:
            msg_type, content = msg
            if msg_type == 'MDTS-MSG':
                if content == b'SUCCESS':
                    print("[接收] 資料傳送成功確認")
                elif isinstance(content, dict):
                    print("[接收] 來自 {} 的資料: {}".format(
                        content['sender'], content['data']))
            else:
                print("[接收] {} 內容: {}".format(msg_type, content))

        utime.sleep_ms(50)
