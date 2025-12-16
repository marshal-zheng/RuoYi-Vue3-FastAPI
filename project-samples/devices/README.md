# 设备JSON导入格式说明

## 设备数据结构

```json
{
  "deviceName": "设备名称",
  "deviceType": "设备类型",
  "manufacturer": "制造商",
  "model": "型号",
  "version": "版本",
  "busType": "总线类型",
  "remark": "备注",
  "interfaces": [
    {
      "interfaceName": "接口名称",
      "interfaceType": "接口类型",
      "position": "端口位置",
      "description": "接口描述"
    }
  ]
}
```

## 字段说明

### 设备基本信息
- `deviceName` (string, 必填): 设备名称
- `deviceType` (string): 设备类型
- `manufacturer` (string): 制造商
- `model` (string): 型号
- `version` (string): 版本
- `busType` (string): 主要总线类型
- `remark` (string): 备注说明

### 接口信息 (interfaces)
- `interfaceName` (string, 必填): 接口名称
- `interfaceType` (string, 必填): 接口类型（RS422/RS485/CAN/LAN/1553B）
- `position` (string): 端口位置（left/right/top/bottom），默认right
- `description` (string): 接口描述

## 设备与协议绑定关系

导入设备后，需要在工程中手动绑定协议。以下是推荐的绑定关系：

### 飞控计算机 (flight-controller.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| LAN-飞控数据 | LAN | right | lan-protocol-1 (飞控数据传输) |
| 1553B-BC | 1553B | right | 1553b-protocol-1 (飞控指令下发) |
| RS485-舵机控制 | RS485 | bottom | rs485-protocol-1 (舵机控制指令) |
| CAN-起落架 | CAN | bottom | can-protocol-1 (起落架控制) |

### 惯性导航系统 (ins-system.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| RS422-惯导输出 | RS422 | right | rs422-protocol-1 (惯导数据输出) |
| 1553B-RT | 1553B | left | 1553b-protocol-2 (导航数据上报) |

### GPS接收机 (gps-receiver.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| RS422-GPS输出 | RS422 | right | rs422-protocol-2 (GPS定位数据) |

### 导航计算机 (navigation-computer.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| RS422-惯导输入 | RS422 | left | rs422-protocol-1 (接收惯导数据) |
| RS422-GPS输入 | RS422 | left | rs422-protocol-2 (接收GPS数据) |
| 1553B-RT | 1553B | right | 1553b-protocol-2 (导航数据上报) |

### 舵机控制器 (servo-controller.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| RS485-指令接收 | RS485 | left | rs485-protocol-1 (舵机控制指令) |
| RS485-状态反馈 | RS485 | right | rs485-protocol-2 (舵机状态反馈) |

### 起落架控制器 (landing-gear-controller.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| CAN-指令接收 | CAN | left | can-protocol-1 (起落架控制) |
| CAN-状态反馈 | CAN | right | can-protocol-2 (起落架状态反馈) |

### 燃油管理系统 (fuel-management.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| CAN-燃油数据 | CAN | right | can-protocol-3 (燃油系统监控) |

### 火控计算机 (fire-control-computer.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| 1553B-RT | 1553B | left | 1553b-protocol-3 (武器火控数据) |
| LAN-火控数据 | LAN | right | lan-protocol-2 (火控数据传输) |

### 任务计算机 (mission-computer.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| 1553B-RT | 1553B | left | 1553b-protocol-3 (武器火控数据) |
| LAN-任务数据 | LAN | right | lan-protocol-3 (任务数据传输) |

### 综合传感器 (sensor-hub.json)
| 接口名称 | 接口类型 | 位置 | 推荐绑定协议 |
|---------|---------|------|-------------|
| CAN-传感器数据 | CAN | left | can-protocol-3 (接收燃油数据) |
| LAN-传感器汇聚 | LAN | right | lan-protocol-2 (传感器数据采集) |

## 典型工程拓扑示例

```
                    ┌─────────────────┐
                    │   飞控计算机     │
                    │ (flight-controller)│
                    └─────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  导航计算机    │  │  舵机控制器    │  │ 起落架控制器  │
│(navigation)   │  │(servo)        │  │(landing-gear) │
└───────────────┘  └───────────────┘  └───────────────┘
        │
        ├──────────────────┐
        ▼                  ▼
┌───────────────┐  ┌───────────────┐
│  惯性导航系统  │  │  GPS接收机    │
│(ins-system)   │  │(gps-receiver) │
└───────────────┘  └───────────────┘
```

## 注意事项

1. **接口位置**: left表示输入端，right表示输出端，便于拓扑图连线
2. **协议绑定**: 设备导入后不带协议，需要在工程中手动绑定
3. **双向通信**: 某些设备有指令接收和状态反馈两个接口，分别绑定不同协议
4. **总线类型**: 设备的busType字段表示主要通信总线，实际可能支持多种总线
