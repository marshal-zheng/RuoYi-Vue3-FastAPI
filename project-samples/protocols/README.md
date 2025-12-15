# 协议JSON导入格式说明

## 正确的JSON格式

### 基本结构

```json
{
  "protocolType": "LAN",
  "header": {
    "sender": "发送方名称",
    "receiver": "接收方名称",
    "frequency": "100",
    "speed": "100M",
    "method": "udp_unicast",
    "port": "8001",
    "frameLength": 256,
    "errorHandle": "timeout_retry"
  },
  "fields": [
    {
      "id": "field_0_unique_id",
      "fieldName": "字段名称",
      "byteCount": 2,
      "byteSequence": "0-1",
      "valueRange": "0xAA55",
      "unit": "",
      "dataType": "UINT16",
      "scale": "1",
      "remark": "备注说明"
    }
  ]
}
```

## 重要说明

### 1. 协议类型 (protocolType)
支持的值：
- `"LAN"` - 以太网协议
- `"RS422"` - RS422协议
- `"RS485"` - RS485协议
- `"CAN"` - CAN协议
- `"1553B"` - 1553B协议

### 2. 头部配置字段 (header)

#### 通用字段
- `sender` (string): 发送方名称
- `receiver` (string): 接收方名称
- `frequency` (string): 传输频率，必须使用字典值
- `errorHandle` (string): 错误处理方式，必须使用字典值

#### LAN协议特有字段
- `speed` (string): 传输速率，必须使用字典值
- `method` (string): 传输方式，必须使用字典值
- `port` (string): 端口号
- `frameLength` (number): 帧长度（字节）

#### RS422/RS485协议特有字段
- `speed` (string): 传输速率，必须使用字典值
- `method` (string): 传输方式，必须使用字典值
- `sendDuration` (number): 发送时长（毫秒）
- `frameLength` (number): 帧长度（字节）

#### CAN协议特有字段
- `speed` (string): 传输速率，必须使用字典值
- `method` (string): 传输方式，必须使用字典值
- `canId` (string): CAN ID
- `frameLength` (number): 帧长度（字节）

#### 1553B协议特有字段
- `speed` (string): 传输速率，必须使用字典值
- `method` (string): 传输方式，必须使用字典值
- `subAddress` (string): 子地址
- `frameLength` (number): 帧长度（字）

### 3. 字典值对照表

#### 传输频率 (frequency)
| 字典值 | 显示名称 |
|--------|---------|
| `"once"` | 单次 |
| `"10"` | 10ms |
| `"20"` | 20ms |
| `"50"` | 50ms |
| `"100"` | 100ms |
| `"160"` | 160ms |
| `"200"` | 200ms |
| `"500"` | 500ms |
| `"1000"` | 1000ms |

#### LAN传输速率 (speed)
| 字典值 | 显示名称 |
|--------|---------|
| `"10M"` | 10M |
| `"100M"` | 100M |
| `"1000M"` | 1000M |

#### LAN传输方式 (method)
| 字典值 | 显示名称 |
|--------|---------|
| `"udp_unicast"` | UDP单播 |
| `"udp_multicast"` | UDP组播 |
| `"udp_broadcast"` | UDP广播 |
| `"tcp"` | TCP |

#### RS422/RS485传输速率 (speed)
| 字典值 | 显示名称 |
|--------|---------|
| `"9.6K"` | 9.6K |
| `"19.2K"` | 19.2K |
| `"38.4K"` | 38.4K |
| `"57.6K"` | 57.6K |
| `"115.2K"` | 115.2K |
| `"230.4K"` | 230.4K |
| `"460.8K"` | 460.8K |
| `"921.6K"` | 921.6K |

#### CAN传输速率 (speed)
| 字典值 | 显示名称 |
|--------|---------|
| `"125K"` | 125K |
| `"250K"` | 250K |
| `"500K"` | 500K |
| `"1000K"` | 1000K |

#### CAN传输方式 (method)
| 字典值 | 显示名称 |
|--------|---------|
| `"can_standard"` | CAN标准帧 |
| `"can_extended"` | CAN扩展帧 |

#### 1553B传输速率 (speed)
| 字典值 | 显示名称 |
|--------|---------|
| `"1M"` | 1M |

#### 1553B传输方式 (method)
| 字典值 | 显示名称 |
|--------|---------|
| `"bc_to_rt"` | BC-RT |
| `"rt_to_bc"` | RT-BC |
| `"rt_to_rt"` | RT-RT |

#### 错误处理 (errorHandle)
| 字典值 | 显示名称 |
|--------|---------|
| `"none"` | 不判断 |
| `"timeout_retry"` | 超时重传 |
| `"crc_check"` | CRC校验 |
| `"parity_check"` | 奇偶校验 |
| `"timeout_retry_3_100ms"` | 超时重传 3 次, 100ms |
| `"default"` | - |

### 4. 字段列表 (fields)

每个字段对象包含以下属性：

- `id` (string, 必填): 字段唯一标识符，建议格式 `field_序号_随机字符串`
- `fieldName` (string, 必填): 字段名称
- `byteCount` (number, 必填): 字节数
- `byteSequence` (string, 必填): 字节序号，如 "0-1" 或 "2"
- `valueRange` (string, 可选): 值域及含义
- `unit` (string, 可选): 量纲/单位
- `dataType` (string, 必填): 数据类型
- `scale` (string, 必填): 比例尺
- `remark` (string, 可选): 备注
- `parentId` (string, 可选): 父级字段ID（用于嵌套字段）

#### 支持的数据类型 (dataType)
- `"UINT8"` - 无符号8位整数
- `"UINT16"` - 无符号16位整数
- `"UINT32"` - 无符号32位整数
- `"INT8"` - 有符号8位整数
- `"INT16"` - 有符号16位整数
- `"INT32"` - 有符号32位整数
- `"FLOAT"` - 单精度浮点数
- `"DOUBLE"` - 双精度浮点数
- `"STRING"` - 字符串
- `"BOOL"` - 布尔值

## 常见错误

### ❌ 错误示例 1：使用显示名称而非字典值
```json
{
  "speed": "100Mbps",  // 错误：应该使用 "100M"
  "method": "UDP",     // 错误：应该使用 "udp_unicast"
  "errorHandle": "重传" // 错误：应该使用 "timeout_retry"
}
```

### ❌ 错误示例 2：数字字段使用字符串
```json
{
  "frameLength": "256"  // 错误：应该使用数字 256
}
```

### ❌ 错误示例 3：嵌套过深的结构
```json
{
  "protocolConfig": {
    "header": { ... },
    "fields": [ ... ]
  }
}
```
应该使用扁平结构：
```json
{
  "header": { ... },
  "fields": [ ... ]
}
```

### ❌ 错误示例 4：包含Label字段
```json
{
  "frequency": "100",
  "frequencyLabel": "100Hz"  // 不需要，前端会自动生成
}
```

## ✅ 完整正确示例

参见 `lan-protocol-1.json` 文件。

## 导入流程

1. 准备符合格式的JSON文件
2. 确保所有枚举字段使用正确的字典值（value），而不是显示名称（label）
3. 确保数字字段使用数字类型，而不是字符串
4. 在系统中选择"导入协议"功能
5. 上传JSON文件
6. 系统会自动解析并创建协议

## 注意事项

1. **必须使用字典值**：所有枚举类型的字段（frequency、speed、method、errorHandle）必须使用数据库字典中定义的value值，不能使用label值
2. **数据类型正确**：frameLength、byteCount等数字字段必须使用数字类型，不能用字符串
3. **字段ID唯一**：每个字段的id必须唯一，建议使用 `field_序号_随机字符串` 格式
4. **不要包含Label字段**：不要在JSON中包含 `*Label` 后缀的字段，前端会根据字典自动生成
5. **结构扁平化**：使用 `header` 和 `fields` 作为顶层字段，不要嵌套在 `protocolConfig` 中
