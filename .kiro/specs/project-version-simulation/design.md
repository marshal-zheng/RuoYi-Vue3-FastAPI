# 设计文档

## 概述

项目版本仿真系统是一个综合性的总线通信仿真平台，用于对项目版本中的设备拓扑和协议配置进行数字化仿真验证。系统采用前后端分离架构，前端使用Vue 3 + TypeScript + ZxChart实现实时数据可视化，后端使用FastAPI + Python实现仿真引擎和数据处理。

### 核心功能

1. **仿真引擎**: 基于数据规格和协议配置驱动的报文传输模拟
2. **实时监控**: 使用ZxChart组件展示带宽利用率、负载率等实时曲线
3. **告警系统**: 自动检测并报告通信设计问题和风险
4. **事件触发**: 支持基于条件的自动化操作
5. **数据分析**: 报文记录、过滤、导出和异常检测

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                         │
├─────────────────────────────────────────────────────────────┤
│  仿真控制面板  │  拓扑可视化  │  实时图表  │  告警面板       │
│  (SimControl)  │  (TopoView)  │ (ZxChart)  │ (AlarmPanel)   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      后端层 (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  仿真控制器  │  仿真引擎  │  告警引擎  │  数据处理器        │
│ (Controller) │  (Engine)  │  (Alarm)   │  (Processor)       │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      数据层 (MySQL/Redis)                     │
├─────────────────────────────────────────────────────────────┤
│  项目版本  │  拓扑数据  │  协议配置  │  仿真记录  │  告警日志│
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

**前端**:
- Vue 3 Composition API
- TypeScript
- ZxChart (基于ECharts) - 实时图表展示
- Element Plus - UI组件库
- Pinia - 状态管理
- WebSocket - 实时通信

**后端**:
- FastAPI - Web框架
- Python 3.9+ - 编程语言
- SQLAlchemy - ORM
- Redis - 缓存和实时数据
- APScheduler - 定时任务
- WebSocket - 实时推送

## 组件和接口

### 前端组件

#### 1. 仿真控制面板 (SimulationControlPanel.vue)

**职责**: 提供仿真会话的启动、暂停、停止、配置等控制功能

**主要功能**:
- 仿真会话管理（开始/暂停/停止/重置）
- 数据注入策略选择（自动生成/手动注入）
- 事件触发器配置
- 仿真参数设置（速度倍率、时间范围等）

**接口**:
```typescript
interface SimulationControlPanel {
  // Props
  projectId: number
  versionId: number
  
  // Methods
  startSimulation(): Promise<void>
  pauseSimulation(): Promise<void>
  stopSimulation(): Promise<void>
  resetSimulation(): Promise<void>
  
  // Events
  onSimulationStart: (sessionId: string) => void
  onSimulationStop: () => void
  onError: (error: Error) => void
}
```

#### 2. 拓扑可视化组件 (SimulationTopologyView.vue)

**职责**: 展示设备拓扑图并实时显示报文流动

**主要功能**:
- 渲染设备节点和连接线
- 实时显示报文传输动画
- 高亮显示活动节点和链路
- 显示节点状态（正常/告警/异常）

**接口**:
```typescript
interface SimulationTopologyView {
  // Props
  topologyData: TopologyData
  messageFlow: MessageFlowData[]
  
  // Methods
  highlightNode(nodeId: string): void
  highlightLink(linkId: string): void
  showMessageAnimation(from: string, to: string): void
  
  // Events
  onNodeClick: (node: DeviceNode) => void
  onLinkClick: (link: DeviceLink) => void
}
```

#### 3. 实时图表组件 (SimulationChartPanel.vue)

**职责**: 使用ZxChart展示带宽、负载率等实时曲线

**主要功能**:
- 多端口带宽曲线实时展示
- 负载率曲线展示
- 时间窗口滑动（支持600秒+）
- 图表缩放和数据点查看

**接口**:
```typescript
interface SimulationChartPanel {
  // Props
  nodeId: string
  portId: string
  timeWindow: number // 秒
  
  // Methods
  updateBandwidthData(data: BandwidthDataPoint): void
  clearChart(): void
  exportChartImage(): Promise<Blob>
  
  // ZxChart配置
  chartOptions: EChartsOption
}
```

#### 4. 告警面板 (SimulationAlarmPanel.vue)

**职责**: 展示仿真过程中的告警信息

**主要功能**:
- 实时告警列表展示
- 告警分类和过滤
- 告警详情查看
- 告警统计图表

**接口**:
```typescript
interface SimulationAlarmPanel {
  // Props
  alarms: Alarm[]
  
  // Methods
  filterAlarms(type: AlarmType): void
  clearAlarms(): void
  exportAlarms(): Promise<void>
  
  // Events
  onAlarmClick: (alarm: Alarm) => void
}
```

#### 5. 报文记录组件 (MessageLogPanel.vue)

**职责**: 展示和管理仿真报文记录

**主要功能**:
- 报文列表展示（发送方、接收方、时间戳、内容）
- 关键字过滤
- 报文详情查看
- 数据导出

**接口**:
```typescript
interface MessageLogPanel {
  // Props
  messages: MessageFrame[]
  
  // Methods
  filterMessages(criteria: FilterCriteria): void
  exportMessages(format: 'json' | 'csv' | 'excel'): Promise<void>
  clearMessages(): void
  
  // Events
  onMessageClick: (message: MessageFrame) => void
}
```

### 后端组件

#### 1. 仿真控制器 (simulation_controller.py)

**职责**: 处理仿真相关的HTTP请求和WebSocket连接

**API端点**:
```python
# 创建仿真会话
POST /api/simulation/sessions
Request: {
  "projectId": int,
  "versionId": int,
  "config": SimulationConfig
}
Response: {
  "sessionId": str,
  "status": str
}

# 启动仿真
POST /api/simulation/sessions/{sessionId}/start

# 暂停仿真
POST /api/simulation/sessions/{sessionId}/pause

# 停止仿真
POST /api/simulation/sessions/{sessionId}/stop

# 获取仿真状态
GET /api/simulation/sessions/{sessionId}/status

# WebSocket连接（实时数据推送）
WS /api/simulation/sessions/{sessionId}/ws
```

#### 2. 仿真引擎 (simulation_engine.py)

**职责**: 核心仿真逻辑，处理报文传输和时序控制

**主要类**:
```python
class SimulationEngine:
    """仿真引擎核心类"""
    
    def __init__(self, session_id: str, topology: TopologyData, 
                 protocols: List[ProtocolConfig]):
        """初始化仿真引擎"""
        
    async def start(self) -> None:
        """启动仿真"""
        
    async def pause(self) -> None:
        """暂停仿真"""
        
    async def stop(self) -> None:
        """停止仿真"""
        
    async def process_tick(self, current_time: float) -> None:
        """处理一个时间片"""
        
    def calculate_bandwidth(self, node_id: str, port_id: str) -> float:
        """计算端口带宽"""
        
    def generate_message(self, spec: MessageSpec) -> MessageFrame:
        """生成报文"""
```

#### 3. 报文生成器 (message_generator.py)

**职责**: 根据协议配置生成模拟报文数据

**主要类**:
```python
class MessageGenerator:
    """报文生成器"""
    
    def generate_lan_message(self, config: LANConfig) -> bytes:
        """生成LAN报文"""
        
    def generate_rs422_message(self, config: RS422Config) -> bytes:
        """生成RS422报文"""
        
    def generate_can_message(self, config: CANConfig) -> bytes:
        """生成CAN报文"""
        
    def generate_1553b_message(self, config: Protocol1553BConfig) -> bytes:
        """生成1553B报文"""
        
    def auto_fill_missing_fields(self, message: dict, 
                                  protocol_type: str) -> dict:
        """自动填充缺失字段"""
```

#### 4. 带宽计算器 (bandwidth_calculator.py)

**职责**: 根据协议类型计算带宽利用率

**主要类**:
```python
class BandwidthCalculator:
    """带宽计算器"""
    
    @staticmethod
    def calculate_lan_bandwidth(frequency_ms: float, 
                                 byte_count: int) -> float:
        """
        计算LAN带宽
        公式: (频率 × 字节数 / 1024 × 8) Mbps
        """
        
    @staticmethod
    def calculate_rs422_bandwidth(baud_rate: int) -> float:
        """
        计算RS422/RS485带宽
        公式: (波特率 / 10 / 1024) Mbps
        """
        
    @staticmethod
    def calculate_can_bandwidth(baud_rate: int, 
                                 frame_size: int = 8) -> float:
        """
        计算CAN带宽
        公式: (波特率 × 64 / 113 / 1024) Mbps (8字节标准帧)
        """
        
    def calculate_load_rate(self, actual_bandwidth: float, 
                           max_bandwidth: float) -> float:
        """计算负载率"""
```

#### 5. 告警引擎 (alarm_engine.py)

**职责**: 检测和生成仿真告警

**主要类**:
```python
class AlarmEngine:
    """告警引擎"""
    
    def check_loopback(self, message: MessageFrame) -> Optional[Alarm]:
        """检查回环告警"""
        
    def check_multi_connection(self, topology: TopologyData) -> List[Alarm]:
        """检查多连接告警"""
        
    def check_message_count_mismatch(self, 
                                     send_count: int, 
                                     receive_count: int) -> Optional[Alarm]:
        """检查报文数量不匹配"""
        
    def check_congestion(self, bandwidth_usage: float, 
                        threshold: float) -> Optional[Alarm]:
        """检查拥塞"""
        
    def check_collision(self, messages: List[MessageFrame]) -> Optional[Alarm]:
        """检查冲突"""
        
    def check_packet_loss(self, sent_messages: List[MessageFrame], 
                         received_messages: List[MessageFrame]) -> List[Alarm]:
        """检查丢包"""
```

#### 6. 事件触发器管理器 (event_trigger_manager.py)

**职责**: 管理和执行事件触发器

**主要类**:
```python
class EventTriggerManager:
    """事件触发器管理器"""
    
    def register_trigger(self, trigger: EventTrigger) -> None:
        """注册触发器"""
        
    def check_triggers(self, context: SimulationContext) -> List[EventTrigger]:
        """检查触发条件"""
        
    async def execute_trigger(self, trigger: EventTrigger) -> None:
        """执行触发器动作"""
        
    def remove_trigger(self, trigger_id: str) -> None:
        """移除触发器"""
```

## 数据模型

### 仿真会话 (SimulationSession)

```python
class SimulationSession:
    """仿真会话数据模型"""
    session_id: str              # 会话ID
    project_id: int              # 项目ID
    version_id: int              # 版本ID
    status: str                  # 状态: created/running/paused/stopped/error
    config: SimulationConfig     # 仿真配置
    start_time: datetime         # 开始时间
    end_time: Optional[datetime] # 结束时间
    created_by: str              # 创建人
    created_at: datetime         # 创建时间
```

### 仿真配置 (SimulationConfig)

```python
class SimulationConfig:
    """仿真配置"""
    speed_multiplier: float = 1.0      # 速度倍率
    data_injection_mode: str = "auto"  # 数据注入模式: auto/manual
    enable_alarms: bool = True         # 启用告警
    enable_bandwidth_monitor: bool = True  # 启用带宽监控
    time_window: int = 600             # 时间窗口（秒）
    event_triggers: List[EventTrigger] # 事件触发器列表
```

### 报文帧 (MessageFrame)

```python
class MessageFrame:
    """报文帧数据模型"""
    message_id: str              # 报文ID
    session_id: str              # 会话ID
    sender_node_id: str          # 发送节点ID
    sender_port_id: str          # 发送端口ID
    receiver_node_id: str        # 接收节点ID
    receiver_port_id: str        # 接收端口ID
    protocol_type: str           # 协议类型
    payload: bytes               # 报文内容
    size_bytes: int              # 报文大小（字节）
    send_timestamp: float        # 发送时间戳
    receive_timestamp: Optional[float]  # 接收时间戳
    status: str                  # 状态: sent/received/lost/error
    is_anomalous: bool = False   # 是否异常
```

### 告警 (Alarm)

```python
class Alarm:
    """告警数据模型"""
    alarm_id: str                # 告警ID
    session_id: str              # 会话ID
    alarm_type: str              # 告警类型: loopback/multi_connection/
                                 # message_mismatch/congestion/collision/packet_loss
    severity: str                # 严重程度: info/warning/error/critical
    affected_nodes: List[str]    # 受影响节点
    message: str                 # 告警消息
    details: dict                # 详细信息
    timestamp: float             # 时间戳
    acknowledged: bool = False   # 是否已确认
```

### 带宽数据点 (BandwidthDataPoint)

```python
class BandwidthDataPoint:
    """带宽数据点"""
    session_id: str              # 会话ID
    node_id: str                 # 节点ID
    port_id: str                 # 端口ID
    timestamp: float             # 时间戳
    bandwidth_mbps: float        # 带宽（Mbps）
    load_rate: float             # 负载率（0-1）
    message_count: int           # 报文数量
```

### 事件触发器 (EventTrigger)

```python
class EventTrigger:
    """事件触发器"""
    trigger_id: str              # 触发器ID
    trigger_type: str            # 触发类型: bandwidth_threshold/send/stop/
                                 # end_simulation/terminal
    condition: dict              # 触发条件
    action: dict                 # 触发动作
    enabled: bool = True         # 是否启用
    priority: int = 0            # 优先级
```

### 拓扑数据 (TopologyData)

```python
class TopologyData:
    """拓扑数据（从现有sys_project_topology扩展）"""
    topology_id: int             # 拓扑ID
    project_id: int              # 项目ID
    version_id: int              # 版本ID
    nodes: List[DeviceNode]      # 设备节点列表
    links: List[DeviceLink]      # 连接链路列表
    topology_data: dict          # 原始拓扑JSON数据
```

### 设备节点 (DeviceNode)

```python
class DeviceNode:
    """设备节点"""
    node_id: str                 # 节点ID
    device_id: int               # 设备ID
    device_name: str             # 设备名称
    device_type: str             # 设备类型
    ports: List[DevicePort]      # 端口列表
    position: dict               # 位置信息
```

### 设备端口 (DevicePort)

```python
class DevicePort:
    """设备端口"""
    port_id: str                 # 端口ID
    interface_id: int            # 接口ID
    port_name: str               # 端口名称
    protocol_type: str           # 协议类型
    protocol_config: dict        # 协议配置
    message_specs: List[MessageSpec]  # 报文规格列表
```

### 报文规格 (MessageSpec)

```python
class MessageSpec:
    """报文规格"""
    spec_id: str                 # 规格ID
    frequency_ms: float          # 发送频率（毫秒）
    byte_count: int              # 字节数
    sender_port_id: str          # 发送端口ID
    receiver_port_ids: List[str] # 接收端口ID列表
    message_template: dict       # 报文模板
```


## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 设备识别和连接建立

*对于任何*数据规格和通信报文，当仿真引擎接收它们时，系统应该自动识别所有设备并建立正确的连接关系
**验证需求: 1.1**

### 属性 2: 报文传输频率遵守

*对于任何*报文规格，当仿真引擎传输报文时，实际传输间隔应该与数据规格中指定的发送频率一致（在合理误差范围内）
**验证需求: 1.4**

### 属性 3: 报文信息完整性

*对于任何*传输的报文帧，系统显示的信息应该包含发送方节点、发送方端口、接收方节点和接收方端口
**验证需求: 1.3**

### 属性 4: 时间戳记录完整性

*对于任何*发送的报文帧，系统应该记录发送时间戳；对于任何接收的报文帧，系统应该记录接收时间戳
**验证需求: 2.2, 2.3**

### 属性 5: 时延计算正确性

*对于任何*已接收的报文帧，系统计算的时延应该等于接收时间戳减去发送时间戳
**验证需求: 2.4**

### 属性 6: 协议配置自动生成数据

*对于任何*定义了报文格式的协议配置，系统应该能够自动生成符合该格式的模拟数据
**验证需求: 3.1, 3.4**

### 属性 7: 缺失字段自动填充

*对于任何*存在缺失字段的协议配置，系统应该使用有效的默认值自动填充，且填充后的值应该符合协议约束
**验证需求: 3.2, 3.5**

### 属性 8: 回环告警检测

*对于任何*报文帧，如果发送方节点和接收方节点相同，系统应该生成回环警告告警
**验证需求: 4.1**

### 属性 9: 多连接告警检测

*对于任何*拓扑结构，如果一个端口连接到多个端口，系统应该生成多连接警告告警
**验证需求: 4.2**

### 属性 10: 报文数量不匹配告警

*对于任何*通信节点对，如果发送报文数量与接收报文数量不一致，系统应该生成报文数量不匹配告警
**验证需求: 4.3**

### 属性 11: 丢包检测

*对于任何*发送的报文帧，如果在合理时间内未被接收，系统应该生成丢包告警
**验证需求: 4.6**

### 属性 12: 告警信息完整性

*对于任何*生成的告警，系统应该显示告警类型、受影响的通信节点列表和时间戳
**验证需求: 4.7**

### 属性 13: 带宽超限触发器执行

*对于任何*配置了带宽阈值的事件触发器，当带宽利用率超过阈值时，系统应该执行关联的触发器动作
**验证需求: 5.2**

### 属性 14: 触发器动作执行正确性

*对于任何*激活的事件触发器，系统应该根据触发器类型执行相应的动作（发送、停止、结束仿真、终端记录）
**验证需求: 5.3, 5.4, 5.5, 5.6**

### 属性 15: 报文记录完整性

*对于任何*仿真引擎处理的报文帧，系统应该记录该报文并包含发送方、接收方、报文内容和时间戳
**验证需求: 6.1, 6.2**

### 属性 16: 异常数据帧告警

*对于任何*检测到的异常数据帧或协议违规，系统应该生成告警并将报文帧标记为异常
**验证需求: 6.3, 6.4**

### 属性 17: 报文时间顺序

*对于任何*报文记录列表，报文应该按照时间戳的时间顺序排列
**验证需求: 6.5**

### 属性 18: LAN带宽计算正确性

*对于任何*LAN协议的端口，系统计算的带宽应该等于 (频率_毫秒 × 字节数 / 1024 × 8) Mbps
**验证需求: 7.2**

### 属性 19: RS422/RS485带宽计算正确性

*对于任何*RS422或RS485协议的端口，系统计算的带宽应该等于 (波特率 / 10 / 1024) Mbps
**验证需求: 7.3**

### 属性 20: CAN带宽计算正确性

*对于任何*CAN协议的端口（8字节标准帧），系统计算的带宽应该等于 (波特率 × 64 / 113 / 1024) Mbps
**验证需求: 7.4**

### 属性 21: 负载率计算正确性

*对于任何*端口，系统计算的负载率应该等于实际带宽除以最大可用带宽
**验证需求: 7.7**

### 属性 22: 报文过滤正确性

*对于任何*过滤条件，系统显示的报文帧应该只包含匹配该过滤条件的报文
**验证需求: 8.1, 8.2**

### 属性 23: 过滤数据属性保持

*对于任何*过滤后的报文帧，其所有原始属性（发送方、接收方、内容、时间戳等）应该保持不变
**验证需求: 8.3**

### 属性 24: 数据导出往返一致性

*对于任何*导出的仿真数据，重新导入后应该保留所有时间戳、报文内容和元数据
**验证需求: 8.4, 8.5**

## 错误处理

### 仿真引擎错误

1. **拓扑数据无效**
   - 错误类型: `InvalidTopologyError`
   - 处理: 返回详细的验证错误信息，拒绝启动仿真
   - 用户反馈: 显示具体的拓扑问题（缺失节点、无效连接等）

2. **协议配置错误**
   - 错误类型: `InvalidProtocolConfigError`
   - 处理: 标记有问题的协议配置，允许用户修正
   - 用户反馈: 高亮显示错误的配置项

3. **报文生成失败**
   - 错误类型: `MessageGenerationError`
   - 处理: 记录错误日志，跳过该报文，继续仿真
   - 用户反馈: 在告警面板显示生成失败的报文规格

4. **仿真引擎崩溃**
   - 错误类型: `SimulationEngineError`
   - 处理: 保存当前仿真状态，安全停止仿真
   - 用户反馈: 显示错误信息和恢复选项

### 数据处理错误

1. **带宽计算溢出**
   - 错误类型: `BandwidthCalculationError`
   - 处理: 使用最大值限制，记录警告
   - 用户反馈: 在图表上标记异常数据点

2. **时间戳异常**
   - 错误类型: `TimestampError`
   - 处理: 使用系统时间修正，标记为异常
   - 用户反馈: 在报文记录中标记时间戳异常

3. **数据存储失败**
   - 错误类型: `StorageError`
   - 处理: 重试3次，失败后缓存到内存
   - 用户反馈: 显示存储状态和重试进度

### 网络通信错误

1. **WebSocket连接断开**
   - 错误类型: `WebSocketDisconnectedError`
   - 处理: 自动重连（最多5次），保持仿真状态
   - 用户反馈: 显示连接状态和重连进度

2. **数据推送失败**
   - 错误类型: `DataPushError`
   - 处理: 缓存数据，连接恢复后批量推送
   - 用户反馈: 显示数据同步状态

### 用户输入错误

1. **无效的过滤条件**
   - 错误类型: `InvalidFilterError`
   - 处理: 显示错误提示，保持之前的过滤状态
   - 用户反馈: 高亮显示错误的输入字段

2. **无效的触发器配置**
   - 错误类型: `InvalidTriggerError`
   - 处理: 拒绝保存，显示验证错误
   - 用户反馈: 在配置表单中显示具体错误

## 测试策略

### 单元测试

**后端单元测试** (使用pytest):

1. **带宽计算器测试**
   - 测试LAN、RS422/RS485、CAN带宽计算公式
   - 测试边界值（零、最大值）
   - 测试负载率计算

2. **报文生成器测试**
   - 测试各协议类型的报文生成
   - 测试自动填充功能
   - 测试协议约束验证

3. **告警引擎测试**
   - 测试各类告警检测逻辑
   - 测试告警优先级和去重
   - 测试告警持久化

4. **事件触发器测试**
   - 测试触发条件判断
   - 测试触发动作执行
   - 测试触发器优先级

**前端单元测试** (使用Vitest):

1. **组件渲染测试**
   - 测试各组件的基本渲染
   - 测试props传递
   - 测试事件触发

2. **状态管理测试**
   - 测试Pinia store的状态变更
   - 测试actions和getters

3. **工具函数测试**
   - 测试数据格式化函数
   - 测试过滤和排序函数

### 属性测试

**属性测试框架**: Hypothesis (Python后端)

1. **属性 18-20: 带宽计算正确性**
   ```python
   @given(
       frequency_ms=st.floats(min_value=1, max_value=10000),
       byte_count=st.integers(min_value=1, max_value=65535)
   )
   def test_lan_bandwidth_calculation(frequency_ms, byte_count):
       """
       Feature: project-version-simulation, Property 18: LAN带宽计算正确性
       """
       calculator = BandwidthCalculator()
       result = calculator.calculate_lan_bandwidth(frequency_ms, byte_count)
       expected = (frequency_ms * byte_count / 1024 * 8)
       assert abs(result - expected) < 0.001
   ```

2. **属性 5: 时延计算正确性**
   ```python
   @given(
       send_time=st.floats(min_value=0, max_value=1000000),
       receive_time=st.floats(min_value=0, max_value=1000000)
   )
   def test_time_delay_calculation(send_time, receive_time):
       """
       Feature: project-version-simulation, Property 5: 时延计算正确性
       """
       assume(receive_time >= send_time)
       delay = receive_time - send_time
       calculated_delay = calculate_delay(send_time, receive_time)
       assert abs(calculated_delay - delay) < 0.001
   ```

3. **属性 8: 回环告警检测**
   ```python
   @given(
       node_id=st.text(min_size=1, max_size=50)
   )
   def test_loopback_alarm_detection(node_id):
       """
       Feature: project-version-simulation, Property 8: 回环告警检测
       """
       message = MessageFrame(
           sender_node_id=node_id,
           receiver_node_id=node_id
       )
       alarm_engine = AlarmEngine()
       alarm = alarm_engine.check_loopback(message)
       assert alarm is not None
       assert alarm.alarm_type == "loopback"
   ```

4. **属性 7: 缺失字段自动填充**
   ```python
   @given(
       protocol_config=st.dictionaries(
           keys=st.text(min_size=1),
           values=st.one_of(st.integers(), st.text(), st.none())
       )
   )
   def test_auto_fill_missing_fields(protocol_config):
       """
       Feature: project-version-simulation, Property 7: 缺失字段自动填充
       """
       generator = MessageGenerator()
       filled_config = generator.auto_fill_missing_fields(
           protocol_config, "LAN"
       )
       # 验证所有必需字段都已填充
       assert all(v is not None for v in filled_config.values())
       # 验证填充的值符合协议约束
       assert generator.validate_protocol_constraints(filled_config, "LAN")
   ```

5. **属性 22: 报文过滤正确性**
   ```python
   @given(
       messages=st.lists(
           st.builds(MessageFrame),
           min_size=0,
           max_size=100
       ),
       filter_keyword=st.text(min_size=1, max_size=20)
   )
   def test_message_filtering(messages, filter_keyword):
       """
       Feature: project-version-simulation, Property 22: 报文过滤正确性
       """
       filtered = filter_messages(messages, filter_keyword)
       # 所有过滤后的报文都应该包含关键字
       for msg in filtered:
           assert (
               filter_keyword in msg.sender_node_id or
               filter_keyword in msg.receiver_node_id or
               filter_keyword in str(msg.payload)
           )
   ```

6. **属性 24: 数据导出往返一致性**
   ```python
   @given(
       simulation_data=st.builds(SimulationData)
   )
   def test_export_import_roundtrip(simulation_data):
       """
       Feature: project-version-simulation, Property 24: 数据导出往返一致性
       """
       # 导出数据
       exported = export_simulation_data(simulation_data)
       # 重新导入
       imported = import_simulation_data(exported)
       # 验证数据一致性
       assert imported.messages == simulation_data.messages
       assert imported.alarms == simulation_data.alarms
       assert all(
           abs(t1 - t2) < 0.001
           for t1, t2 in zip(
               imported.timestamps,
               simulation_data.timestamps
           )
       )
   ```

### 集成测试

1. **端到端仿真流程测试**
   - 创建仿真会话 → 启动仿真 → 验证报文传输 → 停止仿真
   - 验证WebSocket实时数据推送
   - 验证前后端数据同步

2. **告警系统集成测试**
   - 触发各类告警条件
   - 验证告警生成和显示
   - 验证告警持久化

3. **实时图表集成测试**
   - 验证ZxChart组件正确渲染
   - 验证数据实时更新
   - 验证600秒+数据显示

4. **事件触发器集成测试**
   - 配置触发器 → 触发条件 → 验证动作执行
   - 验证多个触发器的协同工作

### 性能测试

1. **20节点仿真性能**
   - 创建20个通信节点
   - 验证仿真引擎处理性能
   - 验证UI渲染性能

2. **600秒长时间运行**
   - 运行600秒以上的仿真
   - 验证内存使用稳定
   - 验证数据存储性能

3. **高频报文传输**
   - 测试高频率报文传输（1ms间隔）
   - 验证系统吞吐量
   - 验证数据丢失率

### 兼容性测试

1. **Windows 7兼容性**
   - 在Windows 7 SP1上安装和运行
   - 验证所有功能正常工作
   - 验证UI显示正常

2. **浏览器兼容性**
   - 测试Chrome、Edge、Firefox
   - 验证ZxChart图表显示
   - 验证WebSocket连接

### 测试配置

**属性测试配置**:
- 每个属性测试至少运行100次迭代
- 使用随机种子确保可重现性
- 记录失败的测试用例用于回归测试

**测试覆盖率目标**:
- 后端代码覆盖率: ≥ 80%
- 前端代码覆盖率: ≥ 70%
- 核心仿真引擎覆盖率: ≥ 90%

## 实现注意事项

### 性能优化

1. **仿真引擎优化**
   - 使用异步处理提高并发性能
   - 批量处理报文减少数据库操作
   - 使用Redis缓存实时数据

2. **前端渲染优化**
   - 虚拟滚动处理大量报文记录
   - 防抖和节流优化实时更新
   - Web Worker处理数据计算

3. **WebSocket优化**
   - 数据压缩减少传输量
   - 批量推送减少消息数量
   - 心跳机制保持连接

### 安全考虑

1. **输入验证**
   - 验证所有用户输入
   - 防止SQL注入和XSS攻击
   - 限制文件上传大小和类型

2. **权限控制**
   - 验证用户对项目版本的访问权限
   - 限制仿真会话的并发数量
   - 审计仿真操作日志

3. **数据保护**
   - 加密敏感配置数据
   - 定期清理过期仿真数据
   - 备份重要仿真记录

### 可扩展性

1. **协议扩展**
   - 插件化协议支持
   - 自定义协议配置模板
   - 协议转换器接口

2. **告警扩展**
   - 自定义告警规则
   - 告警插件系统
   - 第三方告警集成

3. **数据导出扩展**
   - 支持多种导出格式
   - 自定义导出模板
   - 第三方工具集成

### 监控和日志

1. **仿真监控**
   - 实时监控仿真引擎状态
   - 监控系统资源使用
   - 监控WebSocket连接状态

2. **日志记录**
   - 结构化日志记录
   - 日志级别分类
   - 日志轮转和归档

3. **性能指标**
   - 报文处理速率
   - 平均响应时间
   - 错误率统计
