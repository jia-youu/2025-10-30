# ePy Final Demo - 溫濕度監測與 Mesh 網路傳輸應用
# 功能：讀取 HTU21D 溫濕度感測器、AIN5 類比輸入，顯示於 OLED，並透過 Mesh 網路傳送
# 註解皆為中文，遵守 PEP8 規範

from lib.mesh_device import MeshDevice
from ssd1306 import SSD1306_I2C
from htu21d import HTU21D
from machine import I2C, Pin, ADC
import utime


def celsius_to_fahrenheit(celsius):
    """
    將攝氏溫度轉換為華氏溫度
    celsius: 攝氏溫度值
    回傳: 華氏溫度值
    """
    return celsius * 9.0 / 5.0 + 32.0


def main():
    """
    主程式：整合溫濕度感測、OLED 顯示、Mesh 網路傳輸
    """
    print("=== ePy Final Demo 啟動 ===")

    # 初始化 I2C0 (OLED 與 HTU21D 共用)
    print("初始化 I2C0...")
    i2c0 = I2C(0, I2C.MASTER, baudrate=100000)

    # 初始化 OLED 顯示器 (128x64)
    print("初始化 OLED 顯示器...")
    oled = SSD1306_I2C(128, 64, i2c0)
    oled.fill(0)
    oled.text('ePy Demo', 0, 0)
    oled.text('Starting...', 0, 16)
    oled.show()
    utime.sleep_ms(1000)

    # 初始化 HTU21D 溫濕度感測器
    print("初始化 HTU21D 感測器...")
    sensor = HTU21D(i2c0)

    # 初始化 AIN5 類比輸入 (可變電阻)
    print("初始化 AIN5...")
    ain5 = ADC(Pin.epy.AIN5)

    # 初始化 Mesh Device (UART0, 除錯模式關閉以節省資源)
    print("初始化 Mesh Device...")
    mesh = MeshDevice(uart_id=0, baudrate=115200, debug=False)
    mesh.reboot()
    print("Mesh 綁定狀態: {}".format(mesh.is_bound))

    # 初始化按鍵 (上鍵：P24)
    print("初始化按鍵...")
    key_up = Pin.epy.P24
    key_up.init(Pin.IN, Pin.PULL_UP)

    # 狀態變數
    use_celsius = True  # True: 攝氏, False: 華氏
    last_key_state = 1  # 按鍵去彈跳用
    last_read_time = 0  # 上次讀取時間
    last_send_time = 0  # 上次傳送時間
    send_interval = 5000  # Mesh 傳送間隔 (毫秒)

    print("進入主迴圈...")
    oled.fill(0)
    oled.text('Ready!', 0, 0)
    oled.show()
    utime.sleep_ms(500)

    while True:
        current_time = utime.ticks_ms()

        # 每 1 秒讀取一次感測器
        if utime.ticks_diff(current_time, last_read_time) >= 1000:
            last_read_time = current_time

            # 讀取溫濕度
            temperature_c = sensor.readTemperatureData()
            humidity = sensor.readHumidityData()

            # 讀取 AIN5 (0-4095 對應 0-3.3V)
            ain5_value = ain5.read()
            ain5_voltage = ain5_value * 3.3 / 4095.0

            # 判斷溫度顯示單位
            if use_celsius:
                temp_display = temperature_c
                temp_unit = 'C'
            else:
                temp_display = celsius_to_fahrenheit(temperature_c)
                temp_unit = 'F'

            # 清空 OLED 並顯示資料
            oled.fill(0)

            # 第一行：溫度 (小數第一位)
            temp_str = 'T:{:.1f} {}'.format(temp_display, temp_unit)
            oled.text(temp_str, 0, 0)

            # 第二行：濕度 (小數第一位 + %)
            humid_str = 'H:{:.1f} %'.format(humidity)
            oled.text(humid_str, 0, 16)

            # 第三行：AIN5 電壓值 (小數第一位，無單位)
            ain5_str = 'AIN5:{:.1f}'.format(ain5_voltage)
            oled.text(ain5_str, 0, 32)

            # 第四行：Mesh 狀態
            if mesh.is_bound:
                oled.text('Mesh:OK', 0, 48)
            else:
                oled.text('Mesh:--', 0, 48)

            oled.show()

            # 每 5 秒透過 Mesh 傳送資料 (如果已綁定)
            if mesh.is_bound and utime.ticks_diff(current_time, last_send_time) >= send_interval:
                last_send_time = current_time

                # 傳送溫度 (使用攝氏)
                temp_msg = 'T:{:.1f}'.format(temperature_c)
                mesh.set_data(temp_msg)
                print("Mesh 傳送: {}".format(temp_msg))
                utime.sleep_ms(100)  # 短暫延遲避免訊息衝突

                # 傳送濕度
                humid_msg = 'H:{:.1f}'.format(humidity)
                mesh.set_data(humid_msg)
                print("Mesh 傳送: {}".format(humid_msg))
                utime.sleep_ms(100)

                # 傳送 AIN5
                ain5_msg = 'A:{:.1f}'.format(ain5_voltage)
                mesh.set_data(ain5_msg)
                print("Mesh 傳送: {}".format(ain5_msg))

        # 按鍵偵測 (上鍵切換溫度單位)
        key_state = key_up.value()
        if last_key_state == 1 and key_state == 0:
            # 按鍵按下 (去彈跳)
            utime.sleep_ms(50)
            if key_up.value() == 0:
                # 切換溫度單位
                use_celsius = not use_celsius
                unit_name = '攝氏' if use_celsius else '華氏'
                print("溫度單位切換為: {}".format(unit_name))

                # 短暫顯示提示
                oled.fill(0)
                oled.text('Unit Change', 0, 0)
                oled.text(unit_name, 0, 16)
                oled.show()
                utime.sleep_ms(500)
        last_key_state = key_state

        # 接收 Mesh 訊息 (非阻塞)
        msg = mesh.recv_data(timeout=50)
        if msg:
            msg_type, content = msg
            if msg_type == 'MDTS-MSG':
                if content == b'SUCCESS':
                    print("[Mesh] 資料傳送成功")
                elif isinstance(content, dict):
                    print("[Mesh] 來自 {} 的資料: {}".format(
                        content['sender'], content['data']))
            else:
                print("[Mesh] {} : {}".format(msg_type, content))

        # 短暫延遲，避免 CPU 過載
        utime.sleep_ms(50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程式已中斷")
    except Exception as e:
        print("發生錯誤: {}".format(e))
