## **1\. 仿真系统设计哲学与架构总览**

在着手编写代码之前，必须明确仿真系统的设计哲学。客户的不满通常源于“黑盒效应”——他们配置了复杂的参数，点击运行后却只能看到日志文件的生成，缺乏过程感。因此，本方案的核心设计理念是\*\*“可观测性”（Observability）**与**“即时反馈”（Immediate Feedback）\*\*。

### **1.1 核心架构选型论证**

为了满足最大算力利用与方案落地的双重需求，经过对英文高质量资源社区的详尽调研，我们确立了以下技术栈。

#### **1.1.1 后端仿真内核：离散事件仿真（DES）的必然选择**

对于涉及 MIL-STD-1553B、CAN、RS485 等多协议混合的仿真场景，传统的“时间步进”（Time-Slicing）循环（即每隔1ms轮询一次所有设备）极其低效且难以精确模拟总线仲裁。

**选型结论**：采用 **SimPy** 作为仿真内核。

* **调研依据**：根据 INFORMS Simulation Society 及多篇学术论文对比，SimPy 是 Python 生态中最成熟的基于进程（Process-based）的离散事件仿真框架 1。相比于 Salabim，SimPy 的 API 更贴近 Python 原生生成器模式，学习曲线平滑且社区支持更广 3。  
* **技术优势**：SimPy 允许我们为每个设备（Device）创建一个独立的进程，为每条线缆（Link）创建一个资源（Resource）。例如，当 1553B 总线被 BC（总线控制器）占用时，RT（远程终端）的发送请求会自动进入等待队列（Yield Request），这完美模拟了物理层的“载波监听”或“时分复用”机制。  
* **实时同步**：SimPy 的 RealtimeEnvironment 模块能够将仿真时钟与现实世界的墙钟时间（Wall-clock time）严格同步 4，这是实现前端“实时动画”的基石。

#### **1.1.3 前后端通信：全双工实时管道**

仿真状态的推送必须是毫秒级的。轮询（Polling）和 SSE（Server-Sent Events）在双向交互（如暂停仿真、注入故障）场景下显得力不从心 10。

**选型结论**：**FastAPI WebSockets**。

* **技术优势**：FastAPI 基于 Starlette，天生支持异步 WebSocket 处理。这允许我们在后端 SimPy 引擎产生事件的瞬间（Event Trigger），直接通过异步队列（asyncio.Queue）推送到前端，延迟可控制在 10ms 以内 12。

### **1.2 系统逻辑架构图**

我们将系统划分为三层：**表现层（Presentation Layer）**、**控制层（Control Layer）** 和 **仿真层（Simulation Layer）**。

| 层次 | 模块 | 职责描述 | 关键技术 |
| :---- | :---- | :---- | :---- |
| **表现层** | **拓扑画布** | 展示设备连接，渲染数据包传输动画 | antv x6 |
|  | **虚拟仪表盘** | 实时显示总线负载、错误率、波特率 | zxchart |
|  | **日志控制台** | 滚动显示协议帧解码信息（类似 Wireshark） | element plus Virtualized Table |
| **控制层** | **仿真管理器** | 负责加载工程、实例化对象、控制时钟 | Python, Factory Pattern |
|  | **实时网关** | WebSocket 广播，指令下发（暂停/注入） | FastAPI, asyncio |
| **仿真层** | **时序内核** | 维护全局仿真时钟，调度事件队列 | SimPy RealtimeEnvironment |
|  | **协议模型库** | 具体的 1553B/CAN/RS485 行为逻辑 | python-can, pyserial, Custom Classes |
|  | **虚拟总线** | 模拟物理介质的竞争与传输延迟 | SimPy Resources, Containers |

## ---

**2\. 后端仿真引擎深度实施方案**

后端的任务不是“跑通代码”，而是构建一个“虚拟世界”。我们需要在内存中重构出现实世界的时间流逝和物理约束。

### **2.1 仿真内核设计：SimPy 的深度应用**

在您的项目中，核心难点在于如何让 SimPy 跑在 Web 服务（FastAPI）中。SimPy 默认是阻塞运行的（env.run()），而 Web 服务需要响应 HTTP 请求。

#### **2.1.1 异步与同步的桥梁：多线程仿真容器**

我们需要设计一个 SimulationRunner 类，它继承自 threading.Thread，在独立线程中运行 SimPy 的 RealtimeEnvironment。

**关键实现逻辑**：

1. **环境隔离**：Web 服务线程负责接收用户指令（Start, Stop, Pause），通过 thread-safe queue 将指令传递给仿真线程。  
2. **步进控制**：不直接调用 env.run()（这会一直运行到结束），而是使用“步进循环”模式。  
   * 利用 env.step() 或在 env.run(until=current\_time \+ step\_size) 中逐步推进时间。  
   * 这种模式允许我们在每一步仿真之间插入“暂停检查”逻辑，实现客户要求的“暂停/继续”功能 14。

Python

\# 概念代码架构：仿真运行器  
import simpy  
import threading  
import time

class SimulationRunner(threading.Thread):  
    def \_\_init\_\_(self, topology\_data, message\_callback):  
        super().\_\_init\_\_()  
        self.env \= simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)  
        self.topology \= topology\_data  
        self.callback \= message\_callback  \# 用于向 WebSocket 发送数据的回调  
        self.paused \= threading.Event()  
        self.stopped \= threading.Event()  
        self.paused.set() \# 初始为运行状态

    def run(self):  
        self.\_setup\_world() \# 解析拓扑，创建 SimPy 进程  
          
        while not self.stopped.is\_set():  
            self.paused.wait() \# 等待暂停信号解除  
              
            try:  
                \# 向前推进 100ms  
                self.env.run(until=self.env.now \+ 0.1)  
                self.\_collect\_and\_emit\_metrics() \# 收集这100ms内的数据  
            except Exception as e:  
                \# 错误处理与日志  
                break

### **2.2 协议仿真模型详解**

针对您列出的四种协议，我们需要建立不同的仿真模型（Model）。这是体现专业性的关键——不能用简单的 print 代替协议行为。

#### **2.2.1 MIL-STD-1553B：时分指令/响应架构**

1553B 是一种严格的主从式协议，总线控制器（BC）主导一切。

* **仿真难点**：调度表（Schedule）的执行与微秒级响应。  
* **模型设计**：  
  * **BC 进程**：维护一个“指令帧列表”（Major/Minor Frames）16。它会周期性地醒来（yield env.timeout(frame\_time)），向总线资源（Resource）申请独占锁，发送指令。  
  * **RT 进程**：处于监听状态。当总线上传输了匹配其 RT Address 的指令时，RT 进程被激活（利用 simpy.Store 或 Event 触发）。  
  * **状态字模拟**：RT 接收指令后，必须在规定的响应时间（通常 12μs \- 32μs）内发回状态字。我们在 SimPy 中使用 yield env.timeout(response\_time\_gap) 来精确模拟这段静默期 17。  
* **数据结构**：使用 Python 的 dataclass 定义 1553B Word（Command Word, Data Word, Status Word），确保日志输出时能解析出具体的位含义（如 T/R 位，子地址等）19。

#### **2.2.2 CAN Bus：事件驱动与仲裁**

CAN 是基于优先级的广播协议。

* **仿真难点**：非破坏性位仲裁（Arbitration）。  
* **模型设计**：  
  * **利用 python-can 的虚拟总线**：python-can 库提供了 virtual 接口，可以在操作系统内存中创建一个虚拟 CAN 通道 20。  
  * **SimPy 集成**：不要自己写 CAN 协议栈。在 SimPy 的设备进程中，调用 bus.send(msg) 将消息注入 virtual 接口。  
  * **监听器（Listener）**：创建一个独立的监听线程，使用 can.Notifier 监听虚拟通道。当捕获到消息时，将其转换成 SimPy 事件或直接推送到前端日志队列。  
  * **错误注入**：为了增加仿真的真实感，可以随机生成“错误帧”（Error Frame），利用 python-can 的错误注入功能，并在前端用红色高亮显示，这会让客户觉得仿真非常“硬核” 22。

#### **2.2.3 RS422 / RS485：流式传输**

RS485 是半双工的，容易发生冲突。

* **模型设计**：  
  * **资源锁**：在 SimPy 中使用 Resource(capacity=1) 来代表 RS485 总线。  
  * **冲突模拟**：当设备 A 想要发送数据时，首先检查 resource.count。如果 count \> 0，说明总线忙。此时可以选择“等待”（阻塞）或者“冲突”（记录一个 Collision Event 并推送到前端）。  
  * **字节流模拟**：RS485 传输的是字节流。可以简单根据波特率计算传输耗时：duration \= (bits\_per\_byte \* bytes\_count) / baud\_rate。SimPy 休眠该时长，表示传输过程 23。

#### **2.2.4 LAN (Ethernet)：交换式网络**

* **模型设计**：  
  * LAN 不同于上述总线，它是交换式的。我们需要在 SimPy 中模拟一个“交换机”（Switch）对象。  
  * **Store 模型**：使用 simpy.Store 作为交换机的缓冲区。每个连接到交换机的设备都有一个独立的输入/输出管道。  
  * **延迟模拟**：主要模拟排队延迟和处理延迟，而非物理传输延迟。

### **2.3 “仿真”**

鉴于时间紧迫，我建议您采用\*\*“数据驱动”\*\*的迭代路径：

1. **（深度功能）：“生成模式”（Generative Mode）**  
   * **逻辑**：加入随机发生器和调度逻辑，实现真正的动态交互。  
   * **实现**：逐步替换掉“回放进程”，接入上述的 1553B BC 调度器和 CAN 事件触发器。

## ---

**3\. 前端界面设计与用户体验（UX）方案**

客户对界面“不知道做成什么样子”感到迷茫，这是我们建立专家权威的良机。我们需要提供一套“航空暗黑系”\*\*（Avionics Dark Mode）的设计规范。

### **3.1 总体布局设计 (Layout)**

放弃传统的“管理后台”风格（白色背景、大量表格），转向“态势感知”风格（深色背景、高亮线条）。建议采用以下布局：

* **顶部（Header）**：仿真控制条。居中放置巨大的播放/暂停/停止按钮（仿照 IDE 的 Debug 工具栏）。右侧显示全局仿真时间（00:00:00.000），毫秒级跳动。  
* **中间（Main Canvas）**：**交互式拓扑图**。这是核心视觉区域 宽度占满内容区。  
* **右侧（Dashboard）**：**实时遥测仪表盘**。上下两部分：  
  * 上部：总线负载率（Gauge Chart）、错误计数（Line Chart）。  
  * 下部：设备属性详情（点击拓扑节点后显示）。  
* **底部（Bottom Panel）**：**协议分析器日志**。类似 Wireshark 的界面，全宽显示，支持虚拟滚动。

### **3.2 拓扑图与动画设计 (v-network-graph)**

这是让客户“哇塞”的关键点。静态的线是不够的，必须有光在跑。

* **节点设计**：使用 SVG 图标代替简单的圆圈。为“服务器”、“传感器”、“控制器”设计不同的 SVG 图标。  
* **链路动画**：  
  * 利用antv x6 的 paths 和 layers 功能 28。  
  * 当后端推送“数据传输”事件时，前端动态创建一条 path，覆盖在连接线上。  
  * **视觉编码**：  
    * **1553B**：使用**橙色**虚线光点，模拟指令交互的严谨感。  
    * **CAN**：使用**蓝色**快速光点，模拟高频事件。  
    * **RS485**：使用**绿色**慢速光流。  
    * **错误/故障**：如果发生冲突或错误帧，链路瞬间闪烁**红色**，并在节点旁弹出“\!”警告图标。

### **3.3 实时日志与性能优化**

仿真产生的日志量极大（1553B 和 CAN 满载时每秒可能有数千帧）。

* **性能陷阱**：直接使用 v-for 渲染数组会瞬间卡死浏览器。  
* **解决方案**：必须使用 **vue-virtual-scroll-list** 29。它只渲染视口内可见的几十条数据，无论底层数据有几十万条，滚动都丝般顺滑。  
* **自动滚动**：实现“Auto-Scroll”功能，当有新日志时自动吸底，但当用户向上滚动查看历史时，自动暂停吸底（这是专业工具的标准交互）。

## ---

**4\. 前后端集成与通信协议设计**

### **4.1 WebSocket 消息协议定义**

为了规范前后端通信，我们需要定义一套简洁的 JSON 消息协议。

**1\. 仿真控制指令 (Client \-\> Server)**

JSON

{  
  "action": "start", // 或 "pause", "stop", "step"  
  "speed\_factor": 2.0, // 2倍速仿真  
  "scenario\_id": "project\_123"  
}

2\. 实时状态推送 (Server \-\> Client)  
为了减少带宽，不要推送整个拓扑状态，只推送变化量（Delta）。

JSON

// 事件类型 A: 链路流量动画  
{  
  "type": "traffic",  
  "protocol": "1553B",  
  "src\_node": "BC\_01",  
  "dst\_node": "RT\_04",  
  "timestamp": 1678900.123  
}

// 事件类型 B: 日志帧 (用于底部列表)  
{  
  "type": "log",  
  "id": 1024,  
  "time": "10:00:01.553",  
  "proto": "CAN",  
  "info": "ID: 0x123 Data: \[00 FF...\]"  
}

// 事件类型 C: 统计指标 (用于右侧仪表盘，低频推送，如1秒1次)  
{  
  "type": "stats",  
  "bus\_load": {  
    "can\_bus\_1": 45.2,  
    "1553\_bus\_main": 12.8  
  }  
}

### **4.2 应对高频数据的“背压”策略**

即便使用了 WebSocket，如果每秒推送 5000 条 CAN 消息，前端解析 JSON 也会崩溃。

**优化策略**：

1. **后端缓冲合并（Buffering）**：在 SimPy 线程和 WebSocket 发送之间增加一个缓冲层。每隔 50ms（或积攒 100 条消息）打包发送一次。前端收到一个数组，批量处理。  
2. **前端节流（Throttling）**：动画不需要每帧都画。对于极其高频的 CAN 消息，可以在前端限制动画触发频率（例如同一链路上 100ms 内只触发一次动画），但日志数据必须全量记录。

## ---

**5\. 迭代交付路线图 (Roadmap to Acceptance)**

鉴于您“时间没有那么多”，我们需要制定精确的作战计划。

### **阶段一：视觉 MVP (Week 1\) —— 解决“极不满意”**

* **目标**：界面能动，看起来像真的在跑，无需真实物理逻辑。  
* **后端**：  
  * 搭建 FastAPI \+ WebSocket 框架。  
  * 编写一个“伪仿真器”，随机生成流量数据（Random Traffic Generator），不涉及 SimPy 复杂调度。  
* **前端**：  
  * 完成暗色系布局。  
  * 集成 v-network-graph，实现 WebSocket 驱动的随机连线动画。  
  * 集成 vue-virtual-scroll-list，展示滚动的伪造日志。  
* **验收话术**：“这是仿真平台的 UI 框架演示，展示了实时数据流的可视化能力。”

### **阶段二：全功能仿真 (Week 3+) —— 协议深度模拟**

* **目标**：实现 1553B 调度和 CAN 交互。  
* **后端**：  
  * 实现 1553B BC 调度表逻辑。  
  * 实现 CAN 虚拟总线仲裁。  
  * 加入“故障注入”接口。  
* **前端**：  
  * 右键菜单支持“断开连接”、“注入错误”。  
* **验收话术**：“这是完整的闭环仿真系统，支持复杂的协议交互和故障模拟。”

## ---

**大列表的救星。**

* **设计灵感**: Dribbble 搜索 "SCADA Dashboard", "Cyber Security Dashboard" \- 获取配色和布局灵感。