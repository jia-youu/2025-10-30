# RL62M02 藍牙 Mesh AT 指令程式設計指南

## 簡介
本文件提供 RL62M02 藍牙 Mesh 裝置模組的 AT 指令集，用於配置和控制藍牙 Mesh 網絡。
文件中使用以下符號表示：
- `<<` 表示發送到模組的指令
- `>>` 表示從模組接收的回應
- at 指令和回應均以字串形式傳輸，請注意區分大小寫。並且以 `\r\n` 結尾。


## 基本指令

### 查詢韌體版本

**指令格式：**
```
AT+VER
```

**返回值格式：**
```
VER-MSG {SUCCESS/ERROR} <version>
```

**範例：**
```
<< AT+VER
>> VER-MSG SUCCESS 1.0.0
```

### 設置藍芽名稱

**指令格式：**
```
AT+NAME [param]
```

**參數說明：**
- `[param]`：要設定的藍牙裝置名稱

**返回值格式：**
```
NAME-MSG {SUCCESS/ERROR}
```

**範例：**
```
<< AT+NAME BLE_TEST
>> NAME-MSG SUCCESS
```

### 重啟藍芽模組

**指令格式：**
```
AT+REBOOT
```

**返回值格式：**
```
REBOOT-MSG {SUCCESS/ERROR}
```

**範例：**
```
<< AT+REBOOT
>> REBOOT-MSG SUCCESS
>> SYS-MSG PROVISIONER READY
```

### 查詢藍芽 Mesh 模組角色

**指令格式：**
```
AT+MRG
```

**返回值格式：**
```
MRG-MSG {SUCCESS/ERROR} {PROVISIONER/DEVICE}
```

**範例：**
```
<< AT+MRG
>> MRG-MSG SUCCESS DEVICE
```

## 網絡配置指令

### 清除 Mesh 網路配置
- 解除裝置自己與 Mesh 網路的關聯
- 清除之後，裝置自行會重啟

**指令格式：**
```
AT+NR
```

**返回值格式：**
```
NR-MSG {SUCCESS/ERROR} <unicast_addr>
```

**範例：**
```
<< AT+NR
>> NR-MSG SUCCESS
```

## 設置節點設備 UUID
AT+DUS <16Bytes UUID>
DUS-MSG {SUCCESS/ERROR}
```
<< AT+DUS 123E4567E89B12D3A456655600000144\r\n
>> DUS-MSG SUCCESS\r\n
```
## 查詢節點設備 UUID
AT+DUG
DUG-MSG {SUCCESS/ERROR} <UUID>

```
<< AT+DUG\r\n
>> DUG-MSG SUCCESS 123E4567E89B12D3A456655600000152 \r\n
```
## 設置 SIG Model - Generic on off Model 的狀態
AT+GOOS [element_index] [on/off]
GOOS-MSG {SUCCESS/ERROR}
```
<< AT+GOOS 0 1\r\n
>> GOOS-MSG SUCCESS\r\n
```

## 查詢 SIG Model - Generic on off Model 的狀態
AT+GOOG [element_index]
GOOG-MSG <unicast_addr> <element_idx> <on/off>
```
<< AT+GOOG 0\r\n
>> GOOG-MSG 0x0100 0 0\r\n
```

## 資料傳輸指令 (改變自身狀態-資料傳輸)

### 設置 Vendor Model - Datatrans Model 的狀態

**指令格式：**
```
AT+MDTS [element_index] [data(1~20bytes)]
```

**參數說明：**
- `[element_index]`：元素索引
- `[data]`：要傳送的數據，1-20 字節 Hex文字 格式 (例如: 0x112233)

**備註：**
當目標節點 Datatrans model 有被綁定之後，即可透過此指令發送且設定目標節點的 datatrans model 狀態。

**返回值格式：**
```
MDTS-MSG {SUCCESS/ERROR}
```

**範例：**
```
<< AT+MDTS 0 0x1122335566778899
>> MDTS-MSG SUCCESS
```
## 查詢 Vendor Model - Datatrans Model 的狀態
AT+MDTG [element_index] [get_data_len]
MDTS-MSG <unicast_addr> <element_idx> <data>
```
<< AT+MDTG 0 5\r\n
>> MDTG-MSG 0x0100 0 1122334455\r\n
```

## GATT 透傳服務發送數據
AT+GDTS [Data(1~20Bytes)]
GDTS-MSG {SUCCESS/ERROR}
```
<< AT+GDTS 0x112233445566\r\n
>> GDTS-MSG SUCCESS\r\n
```

### 接收 Vendor Model - Datatrans Model 的狀態 (UART AT Command)

當裝置被綁定之後隨時會收到其他節點發送來的 Datatrans model 狀態。會有兩種情況：
- 配置主機 傳送 : 會接收到 `MDTSG-MSG` 訊息
- 裝置間 傳送 訂閱(推播) : 會接收到 `MDTPG-MSG` 訊息


**返回值格式：**
```
MDTS-MSG <unicast_addr> <element_idx> <read_data>
MDTG-MSG <unicast_addr> <element_idx> <read_data>
```

**範例：**
```
>> MDTSG-MSG 0x100 0 122233
>> MDTPG-MSG 0x100 0 122233
```