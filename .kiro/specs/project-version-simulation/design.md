# 设计文档（简化版）

## 概述

项目版本仿真系统是一个轻量级的总线通信仿真工具，用于验证项目版本中的设备拓扑和通信配置。系统采用前后端分离架构，提供基础的仿真控制、报文模拟、实时带宽监控和告警功能。

### 核心功能

1. **仿真控制**: 启动/停止仿真会话
2. **报文模拟**: 根据协议配置模拟报文传输
3. **实时监控**: 使用ZxChart展示带宽曲线
4. **基本告警**: 检测配置错误

## 架构

### 系统架构图

```
┌──────────────────────────────────────────┐
│          前端 (Vue 3)                     │
├──────────────────────────────────────────┤
│  仿真页面  │  拓扑视图  │  图表  │  告警  │
└──────────────────────────────────────────┘
                    ↕ HTTP/WebSocket
┌──────────────────────────────────────────┐
│          后端 (FastAPI)                   │
├──────────────────────────────────────────┤
│  仿真控制器  │  仿真引擎  │  带宽计算器  │
└──────────────────────────────────────────┘
                    ↕
┌──────────────────────────────────────────┐
│          数据层 (MySQL/Redis)             │
└──────────────────────────────────────────┘
```

## 组件和接口

### 前端组件

#### 1. 仿真页面 (SimulationPage.vue)

**路径**: `ruoyi-fastapi-frontend/src/views/project/simulation/index.vue`

**功能**:
- 仿真控制按钮（开始/停止）
- 拓扑图显示
- 带宽图表面板
- 报文列表
- 告警面板

**接口**:
```typescript
interface SimulationPage {
  projectId: number
  versionId: number
  
  startSimulation(): Promise<void>
  stopSimulation(): Promise<void>
}
```

#### 2. 带宽图表组件 (BandwidthChart.vue)

**功能**:
- 使用ZxChart显示实时带宽曲线
- 支持多端口数据展示
- 滑动时间窗口

**接口**:
```typescript
interface BandwidthChart {
  chartData: BandwidthDataPoint[]
  
  updateData(data: BandwidthDataPoint): void
  clearChart(): void
}
```

### 后端组件

#### 1. 仿真控制器 (simulation_controller.py)

**路径**: `ruoyi-fastapi-backend/module_admin/controller/simulation_controller.py`

**API端点**:
```python
# 创建仿真会话
POST /api/simulation/sessions
Request: {
  "projectId": int,
  "versionId": int
}
Response: {
  "sessionId": str,
  "status": str
}

# 启动仿真
POST /api/simulation/sessions/{sessionId}/start

# 停止仿真
POST /api/simulation/sessions/{sessionId}/stop

# WebSocket连接
WS /api/simulation/sessions/{sessionId}/ws
```

#### 2. 仿真引擎 (simulation_engine.py)

**路径**: `ruoyi-fastapi-backend/module_admin/service/simulation_engine.py`

**主要类**:
```python
class SimulationEngine:
    """简化的仿真引擎"""
    
    def __init__(self, session_id: str, topology_data: dict):
        """初始化"""
        
    async def start(self) -> None:
        """启动仿真"""
        
    async def stop(self) -> None:
        """停止仿真"""
        
    async def tick(self) -> None:
        """处理一个时间片（100ms）"""
        
    def generate_messages(self) -> List[Message]:
        """生成当前时间片的报文"""
```

#### 3. 带宽计算器 (bandwidth_calculator.py)

**路径**: `ruoyi-fastapi-backend/module_admin/service/bandwidth_calculator.py`

**主要类**:
```python
class BandwidthCalculator:
    """带宽计算器"""
    
    @staticmethod
    def calculate_lan(frequency_ms: float, byte_count: int) -> float:
        """LAN: (频率 × 字节数 / 1024 × 8) Mbps"""
        return (frequency_ms * byte_count / 1024 * 8)
        
    @staticmethod
    def calculate_rs422(baud_rate: int) -> float:
        """RS422/RS485: (波特率 / 10 / 1024) Mbps"""
        return (baud_rate / 10 / 1024)
        
    @staticmethod
    def calculate_can(baud_rate: int) -> float:
        """CAN: (波特率 × 64 / 113 / 1024) Mbps"""
        return (baud_rate * 64 / 113 / 1024)
```

## 数据模型

### 仿真会话 (SimulationSession)

```python
class SimulationSessionDO(Base):
    """仿真会话表"""
    __tablename__ = 'sys_simulation_session'
    
    session_id = Column(String(64), primary_key=True)
    project_id = Column(Integer, nullable=False)
    version_id = Column(Integer, nullable=False)
    status = Column(String(20))  # created/running/stopped
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    create_by = Column(String(64))
    create_time = Column(DateTime)
```

### 报文记录 (MessageLog)

```python
class SimulationMessageDO(Base):
    """仿真报文记录表"""
    __tablename__ = 'sys_simulation_message'
    
    message_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=False)
    sender_node_id = Column(String(64))
    sender_port_id = Column(String(64))
    receiver_node_id = Column(String(64))
    receiver_port_id = Column(String(64))
    protocol_type = Column(String(20))
    size_bytes = Column(Integer)
    send_timestamp = Column(Float)
    receive_timestamp = Column(Float)
    create_time = Column(DateTime)
```

### 带宽数据 (BandwidthData)

```python
class SimulationBandwidthDO(Base):
    """仿真带宽数据表"""
    __tablename__ = 'sys_simulation_bandwidth'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    node_id = Column(String(64))
    port_id = Column(String(64))
    timestamp = Column(Float)
    bandwidth_mbps = Column(Float)
    message_count = Column(Integer)
    create_time = Column(DateTime)
```

### 告警记录 (AlarmLog)

```python
class SimulationAlarmDO(Base):
    """仿真告警记录表"""
    __tablename__ = 'sys_simulation_alarm'
    
    alarm_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=False)
    alarm_type = Column(String(50))  # loopback/multi_connection
    severity = Column(String(20))  # warning/error
    affected_nodes = Column(JSON)
    message = Column(String(500))
    timestamp = Column(Float)
    create_time = Column(DateTime)
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 仿真会话状态转换

*对于任何*仿真会话，状态转换必须遵循：created → running → stopped 的顺序
**验证需求: 1.2, 1.3**

### 属性 2: 报文时间戳单调性

*对于任何*仿真会话中的报文序列，发送时间戳必须单调递增
**验证需求: 2.2**

### 属性 3: 带宽计算公式正确性

*对于任何*协议类型和参数，带宽计算结果必须符合指定公式
**验证需求: 3.2, 3.3, 3.4**

### 属性 4: 告警检测完整性

*对于任何*拓扑配置，所有回环和多连接情况必须被检测并生成告警
**验证需求: 4.1, 4.2**

### 属性 5: 数据导出完整性

*对于任何*报文记录集合，导出后重新导入应得到相同的数据
**验证需求: 5.3**

## 错误处理

### 错误类型

1. **配置错误**: 拓扑数据缺失、协议配置无效
2. **运行时错误**: 仿真引擎异常、WebSocket断开
3. **数据错误**: 数据库操作失败、数据格式错误

### 错误处理策略

- 配置错误：启动前验证，显示错误信息，阻止启动
- 运行时错误：记录日志，停止仿真，通知用户
- 数据错误：重试机制，失败后回滚

## 测试策略

### 单元测试

- 带宽计算器：测试各协议类型的计算公式
- 告警检测：测试回环和多连接检测逻辑
- 数据导出：测试JSON/CSV导出功能

### 集成测试

- 仿真流程：测试完整的启动-运行-停止流程
- WebSocket通信：测试实时数据推送
- 数据持久化：测试报文和带宽数据存储

### 性能测试

- 20节点仿真：验证系统支持20个节点同时运行
- 600秒数据：验证系统能够记录和显示600秒的带宽数据

## 实施注意事项

### 简化策略

1. **不实现复杂的事件触发器** - 仅提供基本的启动/停止控制
2. **简化报文生成** - 使用固定大小的模拟数据，不实现复杂的协议解析
3. **基础告警** - 仅检测回环和多连接，不实现拥塞、冲突检测
4. **内存存储** - 仿真数据优先存储在Redis，定期批量写入MySQL

### 技术选型

- **前端图表**: ZxChart (基于ECharts)
- **实时通信**: WebSocket
- **定时任务**: Python asyncio
- **数据缓存**: Redis

### 开发优先级

1. **P0**: 仿真控制、报文模拟、带宽计算
2. **P1**: 实时图表、基本告警
3. **P2**: 数据导出、过滤功能
