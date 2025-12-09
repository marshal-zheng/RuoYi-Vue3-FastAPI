# Requirements Document

## Introduction

本文档定义了多总线混合设计仿真管理系统的仿真功能重构需求。基于用户反馈和迭代方案，本次重构旨在解决以下核心问题：

1. **可观测性不足**：用户配置参数后缺乏过程感，"黑盒效应"严重
2. **告警功能缺失**：缺少拥塞、冲突、丢包等通信风险预警
3. **数据过滤监视缺失**：无法对关键数据进行过滤、监视及存储
4. **故障注入缺失**：无法进行故障注入和异常数据帧告警
5. **性能问题**：仿真时间超过200秒后界面卡顿严重
6. **关键事件触发缺失**：无法自定义关键事件触发

本方案基于现有项目实现，优先复用已封装的zxflow组件（XflowDAG、ZxContentWrap、ZxFloatingPanel等），在现有拓扑基础上丰富仿真功能。

## Glossary

- **Simulation_System**: 仿真系统，负责模拟多总线通信行为的核心模块
- **Topology_Canvas**: 拓扑画布，基于XflowDAG组件的设备连接可视化区域
- **Message_Monitor**: 报文监视器，实时显示和过滤通信报文的组件
- **Bandwidth_Dashboard**: 带宽仪表盘，显示总线负载率和流量统计的组件
- **Alarm_Panel**: 告警面板，显示通信风险和异常告警的组件
- **Fault_Injector**: 故障注入器，用于模拟通信故障的功能模块
- **Event_Trigger**: 事件触发器，用于定义和触发关键事件的功能模块
- **Protocol_Analyzer**: 协议分析器，解析和显示协议帧详情的组件
- **Data_Filter**: 数据过滤器，用于筛选关键数据的功能模块
- **WebSocket_Gateway**: WebSocket网关，负责实时数据推送的通信层

## Requirements

### Requirement 1: 仿真界面布局重构

**User Story:** As a 系统用户, I want 一个专业的"态势感知"风格仿真界面, so that 我能直观地观察仿真过程和系统状态。

#### Acceptance Criteria

1. WHEN 用户进入仿真页面 THEN Simulation_System SHALL 显示深色主题的专业仿真界面，包含顶部控制条、中央拓扑画布、右侧仪表盘和底部协议分析器四个区域
2. WHEN 仿真运行时 THEN Simulation_System SHALL 在顶部控制条居中显示播放/暂停/停止按钮，右侧显示毫秒级跳动的全局仿真时间（格式：HH:MM:SS.mmm）
3. WHEN 用户点击拓扑节点 THEN Simulation_System SHALL 在右侧仪表盘下部显示该设备的属性详情
4. WHEN 仿真产生日志 THEN Simulation_System SHALL 在底部协议分析器区域以虚拟滚动列表形式显示协议帧解码信息

### Requirement 2: 拓扑动画增强

**User Story:** As a 系统用户, I want 在拓扑图上看到数据传输的动态效果, so that 我能直观理解数据流向和通信状态。

#### Acceptance Criteria

1. WHEN 报文在链路上传输时 THEN Topology_Canvas SHALL 在对应连接线上显示移动的光点动画，动画颜色根据协议类型区分（1553B橙色、CAN蓝色、RS422/RS485绿色、LAN白色）
2. WHEN 链路发生通信错误或冲突时 THEN Topology_Canvas SHALL 使该链路瞬间闪烁红色，并在相关节点旁显示警告图标
3. WHEN 用户悬停在链路上时 THEN Topology_Canvas SHALL 显示该链路的实时带宽、报文数量和协议类型信息
4. WHEN 节点处于活跃通信状态时 THEN Topology_Canvas SHALL 为该节点添加呼吸灯效果以示区分

### Requirement 3: 实时报文监视与过滤

**User Story:** As a 系统用户, I want 对通信报文进行实时监视和过滤, so that 我能快速定位关键数据和异常情况。

#### Acceptance Criteria

1. WHEN 仿真运行时 THEN Message_Monitor SHALL 以虚拟滚动列表形式实时显示报文，支持显示时间戳、源节点、目标节点、协议类型、报文大小和数据内容
2. WHEN 用户设置过滤条件（协议类型、源/目标节点、关键字）THEN Message_Monitor SHALL 仅显示符合条件的报文，过滤操作响应时间小于100毫秒
3. WHEN 用户启用自动滚动 THEN Message_Monitor SHALL 自动滚动到最新报文；WHEN 用户手动向上滚动查看历史 THEN Message_Monitor SHALL 暂停自动滚动
4. WHEN 用户选中某条报文 THEN Message_Monitor SHALL 在详情区域显示该报文的完整十六进制内容和字段解析结果
5. WHEN 用户点击导出按钮 THEN Message_Monitor SHALL 将当前过滤结果导出为CSV或JSON格式文件

### Requirement 4: 带宽监控仪表盘

**User Story:** As a 系统用户, I want 实时查看各总线的带宽使用情况, so that 我能评估通信设计的合理性。

#### Acceptance Criteria

1. WHEN 仿真运行时 THEN Bandwidth_Dashboard SHALL 以仪表盘图形式显示各总线的实时负载率（百分比），刷新频率不低于每秒1次
2. WHEN 仿真运行时 THEN Bandwidth_Dashboard SHALL 以折线图形式显示各总线带宽的历史趋势，保留最近10分钟的数据
3. WHEN 总线负载率超过80% THEN Bandwidth_Dashboard SHALL 将对应仪表盘显示为黄色警告状态
4. WHEN 总线负载率超过95% THEN Bandwidth_Dashboard SHALL 将对应仪表盘显示为红色危险状态，并触发拥塞告警
5. WHEN 用户点击某个总线仪表盘 THEN Bandwidth_Dashboard SHALL 展开显示该总线下所有端口的详细带宽数据

### Requirement 5: 告警与风险预警

**User Story:** As a 系统用户, I want 系统能够自动检测并告警通信风险, so that 我能及时发现设计问题。

#### Acceptance Criteria

1. WHEN 检测到总线拥塞（负载率超过95%）THEN Alarm_Panel SHALL 生成拥塞告警，显示告警时间、总线名称、当前负载率和建议措施
2. WHEN 检测到报文冲突（同一时刻多个设备竞争总线）THEN Alarm_Panel SHALL 生成冲突告警，显示冲突设备、冲突时间和冲突次数
3. WHEN 检测到丢包（报文发送后未收到确认）THEN Alarm_Panel SHALL 生成丢包告警，显示丢包率、丢包报文详情和可能原因
4. WHEN 检测到带宽超限（配置的数据率超过总线物理带宽）THEN Alarm_Panel SHALL 生成带宽超限告警，显示超限端口、配置带宽和物理带宽上限
5. WHEN 检测到数值范围溢出（报文字段值超出定义范围）THEN Alarm_Panel SHALL 生成溢出告警，显示字段名称、当前值和有效范围
6. WHEN 用户在报文配置界面输入超出字节范围的数值 THEN Simulation_System SHALL 阻止输入并在界面上显示醒目的红色告警提示
7. WHEN 告警产生时 THEN Alarm_Panel SHALL 按严重程度（错误/警告/信息）分类显示，支持按类型和时间过滤

### Requirement 6: 故障注入功能

**User Story:** As a 系统用户, I want 能够人为注入通信故障, so that 我能测试系统的容错能力。

#### Acceptance Criteria

1. WHEN 用户右键点击链路并选择"断开连接" THEN Fault_Injector SHALL 模拟该链路断开，停止该链路上的所有报文传输
2. WHEN 用户右键点击链路并选择"注入错误帧" THEN Fault_Injector SHALL 在该链路上生成指定数量的错误帧，并在协议分析器中以红色高亮显示
3. WHEN 用户右键点击节点并选择"模拟设备故障" THEN Fault_Injector SHALL 使该节点停止响应，模拟设备离线状态
4. WHEN 用户设置丢包率参数 THEN Fault_Injector SHALL 按设定概率随机丢弃报文，并记录丢包统计
5. WHEN 用户设置延迟参数 THEN Fault_Injector SHALL 为报文传输添加指定的额外延迟时间
6. WHEN 故障注入生效时 THEN Topology_Canvas SHALL 在受影响的链路或节点上显示故障标识

### Requirement 7: 关键事件触发

**User Story:** As a 系统用户, I want 能够自定义关键事件并在特定条件下触发, so that 我能测试系统对特殊场景的响应。

#### Acceptance Criteria

1. WHEN 用户打开事件配置面板 THEN Event_Trigger SHALL 显示事件列表，支持新增、编辑和删除自定义事件
2. WHEN 用户创建事件时 THEN Event_Trigger SHALL 允许设置触发条件（时间点、报文数量、带宽阈值、特定报文内容）
3. WHEN 用户创建事件时 THEN Event_Trigger SHALL 允许设置触发动作（发送特定报文、注入故障、暂停仿真、记录日志）
4. WHEN 仿真运行中满足事件触发条件 THEN Event_Trigger SHALL 自动执行配置的触发动作，并在界面上显示事件触发通知
5. WHEN 用户点击手动触发按钮 THEN Event_Trigger SHALL 立即执行选中事件的触发动作

### Requirement 8: 数据存储与导出

**User Story:** As a 系统用户, I want 能够存储和导出仿真数据, so that 我能进行离线分析和报告生成。

#### Acceptance Criteria

1. WHEN 仿真运行时 THEN Simulation_System SHALL 将报文数据、带宽数据和告警数据实时存储到数据库
2. WHEN 用户点击导出报文按钮 THEN Simulation_System SHALL 支持导出为CSV、JSON和PCAP格式
3. WHEN 用户点击导出带宽数据按钮 THEN Simulation_System SHALL 导出带宽历史数据为CSV格式，包含时间戳、端口、带宽值
4. WHEN 用户点击生成报告按钮 THEN Simulation_System SHALL 生成包含仿真摘要、带宽统计、告警汇总的PDF报告
5. WHEN 用户查询历史仿真记录 THEN Simulation_System SHALL 显示历史会话列表，支持按时间和项目筛选

### Requirement 9: 仿真控制增强

**User Story:** As a 系统用户, I want 更精细地控制仿真过程, so that 我能灵活地进行各种测试场景。

#### Acceptance Criteria

1. WHEN 用户点击暂停按钮 THEN Simulation_System SHALL 暂停仿真时钟，保持当前状态，所有动画停止
2. WHEN 用户点击继续按钮 THEN Simulation_System SHALL 从暂停点继续仿真，恢复所有动画
3. WHEN 用户调整仿真速度滑块 THEN Simulation_System SHALL 支持0.5x到4x的仿真速度调节，实时生效
4. WHEN 用户点击单步执行按钮 THEN Simulation_System SHALL 执行一个时间片（100ms）的仿真后自动暂停
5. WHEN 用户设置仿真时长 THEN Simulation_System SHALL 在达到设定时长后自动停止仿真

### Requirement 10: 性能优化

**User Story:** As a 系统用户, I want 仿真系统在长时间运行时保持流畅, so that 我能进行完整的仿真测试。

#### Acceptance Criteria

1. WHEN 仿真运行超过200秒 THEN Simulation_System SHALL 保持界面响应时间小于100毫秒，无明显卡顿
2. WHEN 报文列表超过10000条 THEN Message_Monitor SHALL 使用虚拟滚动技术，仅渲染可视区域内的数据
3. WHEN WebSocket推送数据时 THEN Simulation_System SHALL 采用增量推送策略，每次仅推送新增数据
4. WHEN 带宽数据超过600个采样点 THEN Bandwidth_Dashboard SHALL 自动清理旧数据，保持内存占用稳定
5. WHEN 前端接收高频数据时 THEN Simulation_System SHALL 采用节流策略，动画触发频率限制在每100毫秒一次

### Requirement 11: 协议帧解析显示

**User Story:** As a 系统用户, I want 查看协议帧的详细解析结果, so that 我能理解通信内容。

#### Acceptance Criteria

1. WHEN 显示1553B协议帧 THEN Protocol_Analyzer SHALL 解析并显示命令字（RT地址、子地址、T/R位、字计数）、状态字和数据字
2. WHEN 显示CAN协议帧 THEN Protocol_Analyzer SHALL 解析并显示帧ID、DLC、数据内容和CRC
3. WHEN 显示RS422/RS485协议帧 THEN Protocol_Analyzer SHALL 解析并显示帧头、数据长度、数据内容和校验和
4. WHEN 显示以太网协议帧 THEN Protocol_Analyzer SHALL 解析并显示MAC地址、IP地址、端口号和负载数据
5. WHEN 协议帧包含错误 THEN Protocol_Analyzer SHALL 以红色高亮显示错误字段，并提示错误类型

### Requirement 12: 仿真前置条件检查

**User Story:** As a 系统用户, I want 系统在仿真前自动检查配置完整性, so that 我能避免因配置问题导致仿真失败。

#### Acceptance Criteria

1. WHEN 用户点击执行仿真按钮 THEN Simulation_System SHALL 检查拓扑中是否存在至少两个设备节点和一条连接
2. WHEN 检测到未配置协议的端口 THEN Simulation_System SHALL 显示警告，列出未配置的端口并建议配置
3. WHEN 检测到不兼容的协议连接（如1553B端口连接CAN端口）THEN Simulation_System SHALL 显示错误，阻止仿真启动
4. WHEN 健康自检完成 THEN Simulation_System SHALL 显示检查报告，包含通过项、警告项和错误项的详细列表
