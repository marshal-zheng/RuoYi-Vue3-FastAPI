# Implementation Plan

## ⚠️ 重要说明：完全重构授权

**本次重构可以完全重写前后端仿真逻辑，旧的实现如果不合理可以删除。但必须遵守以下原则：**

1. **不影响其他功能**：仿真重构不能影响项目管理、设备管理、协议管理、用户权限等其他模块
2. **清理干净**：删除旧代码时必须彻底清理，不留垃圾代码（包括未使用的导入、废弃的组件、无效的API等）
3. **保持兼容**：保留现有的数据库表结构（simulation.sql），如需修改需明确标注
4. **渐进替换**：建议先创建新组件/服务，验证可用后再删除旧代码

**可删除/重构的旧文件清单（如不合理）：**
- 前端：`simulation.vue`（旧仿真页面）、`composables/useSimulationCore.js`、`composables/useSimulationAnimation.js` 等
- 后端：`simulation_engine.py`（当前基于asyncio的简单实现，将重构为SimPy架构）
- 后端：`data_injection_strategy.py`（如需重构数据注入逻辑）

---

## 第一部分：前端实现

- [x] 1. 仿真界面布局重构
  - [x] 1.1 创建仿真主页面框架
    - 重构 `src/views/project/simulation/index.vue`，采用深色主题"态势感知"风格
    - 使用 Tailwind CSS 实现深色主题（bg-slate-900、bg-slate-800等）
    - 实现四区域布局：顶部控制条、中央拓扑画布、右侧仪表盘、底部协议分析器
    - 复用 ZxContentWrap 组件作为容器
    - _Requirements: 1.1, 1.4_
  - [x] 1.2 创建顶部仿真控制条组件
    - 创建 `SimulationHeader.vue` 组件
    - 实现播放/暂停/停止/单步按钮
    - 实现毫秒级时间显示（HH:MM:SS.mmm格式）
    - 实现速度调节滑块（0.5x-4x）
    - _Requirements: 1.2, 9.1, 9.2, 9.3, 9.4_
  - [x] 1.3 编写时间格式化属性测试
    - **Property 1: 时间格式化一致性**
    - **Validates: Requirements 1.2**

- [x] 2. 拓扑动画增强
  - [x] 2.1 创建拓扑动画composable
    - 创建 `composables/useTopologyAnimation.js`
    - 实现协议类型到颜色的映射函数（1553B橙色、CAN蓝色、RS422绿色、LAN白色）
    - 实现链路光点动画效果
    - 实现节点呼吸灯效果
    - _Requirements: 2.1, 2.4_
  - [x] 2.2 编写协议颜色映射属性测试
    - **Property 2: 协议颜色映射完整性**
    - **Validates: Requirements 2.1**
  - [x] 2.3 实现链路错误闪烁效果
    - 在链路发生错误时显示红色闪烁
    - 在相关节点旁显示警告图标
    - _Requirements: 2.2_
  - [x] 2.4 实现链路悬停信息提示
    - 悬停时显示实时带宽、报文数量、协议类型
    - _Requirements: 2.3_

- [ ] 3. 报文监视器组件
  - [ ] 3.1 创建报文监视器组件
    - 创建 `components/MessageMonitor.vue`
    - 使用 vue-virtual-scroller 实现虚拟滚动
    - 显示时间戳、源节点、目标节点、协议类型、报文大小、数据内容
    - _Requirements: 3.1, 10.2_
  - [ ] 3.2 实现报文过滤功能
    - 支持按协议类型、源/目标节点、关键字过滤
    - 过滤响应时间小于100ms
    - _Requirements: 3.2_
  - [ ] 3.3 编写报文过滤属性测试
    - **Property 3: 报文过滤正确性**
    - **Validates: Requirements 3.2**
  - [ ] 3.4 实现自动滚动功能
    - 新报文时自动滚动到底部
    - 用户手动向上滚动时暂停自动滚动
    - _Requirements: 3.3_
  - [ ] 3.5 实现报文详情显示
    - 选中报文时显示完整十六进制内容
    - 显示字段解析结果
    - _Requirements: 3.4_
  - [ ] 3.6 编写十六进制转换属性测试
    - **Property 4: 十六进制转换往返一致性**
    - **Validates: Requirements 3.4**
  - [ ] 3.7 实现报文导出功能
    - 支持导出为CSV和JSON格式
    - _Requirements: 3.5_
  - [ ] 3.8 编写数据导出格式属性测试
    - **Property 5: 数据导出格式正确性**
    - **Validates: Requirements 3.5, 8.2, 8.3**

- [ ] 4. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. 带宽监控仪表盘重构
  - [ ] 5.1 重构带宽仪表盘组件
    - 重构 `components/BandwidthDashboard.vue`
    - 使用ECharts实现仪表盘图形
    - 显示各总线实时负载率（百分比）
    - _Requirements: 4.1_
  - [ ] 5.2 实现带宽历史趋势图
    - 使用ECharts折线图显示历史趋势
    - 保留最近10分钟数据
    - _Requirements: 4.2_
  - [ ] 5.3 实现负载率阈值状态显示
    - 超过80%显示黄色警告
    - 超过95%显示红色危险
    - _Requirements: 4.3, 4.4_
  - [ ] 5.4 编写负载率计算属性测试
    - **Property 6: 负载率计算正确性**
    - **Validates: Requirements 4.1**
  - [ ] 5.5 实现端口详情展开
    - 点击总线仪表盘展开显示端口详细数据
    - _Requirements: 4.5_

- [ ] 6. 告警面板增强
  - [ ] 6.1 增强告警面板组件
    - 重构 `components/AlarmPanel.vue`
    - 支持显示拥塞、冲突、丢包、带宽超限、数值溢出告警
    - 按严重程度（error/warning/info）分类显示
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7_
  - [ ] 6.2 编写告警阈值触发属性测试
    - **Property 7: 告警阈值触发正确性**
    - **Validates: Requirements 4.3, 4.4, 5.1**
  - [ ] 6.3 编写告警分类排序属性测试
    - **Property 8: 告警分类排序正确性**
    - **Validates: Requirements 5.7**
  - [ ] 6.4 实现输入范围验证告警
    - 在报文配置界面输入超出字节范围时显示红色告警
    - _Requirements: 5.6_
  - [ ] 6.5 编写输入范围验证属性测试
    - **Property 9: 输入范围验证正确性**
    - **Validates: Requirements 5.6**
  - [ ] 6.6 实现告警过滤功能
    - 支持按类型和时间过滤告警
    - _Requirements: 5.7_

- [ ] 7. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. 故障注入功能
  - [ ] 8.1 创建故障注入菜单组件
    - 创建 `components/FaultInjectorMenu.vue`
    - 实现右键菜单：断开连接、注入错误帧、模拟设备故障
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ] 8.2 创建故障注入composable
    - 创建 `composables/useFaultInjection.js`
    - 实现丢包率设置功能
    - 实现延迟参数设置功能
    - _Requirements: 6.4, 6.5_
  - [ ] 8.3 实现故障状态可视化
    - 在受影响的链路或节点上显示故障标识
    - _Requirements: 6.6_

- [ ] 9. 关键事件触发功能
  - [ ] 9.1 创建事件触发面板组件
    - 创建 `components/EventTriggerPanel.vue`
    - 显示事件列表，支持新增、编辑、删除
    - _Requirements: 7.1_
  - [ ] 9.2 实现事件条件配置
    - 支持时间点、报文数量、带宽阈值、特定报文内容条件
    - _Requirements: 7.2_
  - [ ] 9.3 实现事件动作配置
    - 支持发送特定报文、注入故障、暂停仿真、记录日志动作
    - _Requirements: 7.3_
  - [ ] 9.4 创建事件触发composable
    - 创建 `composables/useEventTrigger.js`
    - 实现条件匹配逻辑
    - 实现手动触发功能
    - _Requirements: 7.4, 7.5_
  - [ ] 9.5 编写事件条件匹配属性测试
    - **Property 11: 事件条件匹配正确性**
    - **Validates: Requirements 7.4**

- [ ] 10. 协议分析器组件
  - [ ] 10.1 创建协议分析器组件
    - 创建 `components/ProtocolAnalyzer.vue`
    - 使用虚拟滚动显示协议帧列表
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [ ] 10.2 创建协议解析工具
    - 创建 `utils/protocolParser.js`
    - 实现1553B协议解析（命令字、状态字、数据字）
    - 实现CAN协议解析（帧ID、DLC、数据、CRC）
    - 实现RS422/RS485协议解析（帧头、数据长度、校验和）
    - 实现以太网协议解析（MAC、IP、端口、负载）
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [ ] 10.3 编写1553B协议解析属性测试
    - **Property 15: 1553B协议解析正确性**
    - **Validates: Requirements 11.1**
  - [ ] 10.4 编写CAN协议解析属性测试
    - **Property 16: CAN协议解析正确性**
    - **Validates: Requirements 11.2**
  - [ ] 10.5 实现错误帧高亮显示
    - 协议帧包含错误时以红色高亮显示错误字段
    - _Requirements: 11.5_

- [ ] 11. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. 仿真控制逻辑
  - [ ] 12.1 重构仿真控制composable
    - 重构 `composables/useSimulationControl.js`
    - 实现暂停/继续状态管理
    - 实现速度调节（0.5x-4x）
    - 实现单步执行
    - 实现定时停止
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [ ] 12.2 编写仿真速度范围验证属性测试
    - **Property 12: 仿真速度范围验证**
    - **Validates: Requirements 9.3**
  - [ ] 12.3 编写仿真状态转换属性测试
    - **Property 18: 仿真状态转换正确性**
    - **Validates: Requirements 9.1, 9.2**

- [ ] 13. 性能优化
  - [ ] 13.1 实现数据清理策略
    - 带宽数据超过600个采样点时自动清理旧数据
    - 报文数据超过限制时清理旧数据
    - _Requirements: 10.4_
  - [ ] 13.2 编写数据清理阈值属性测试
    - **Property 13: 数据清理阈值正确性**
    - **Validates: Requirements 10.4**
  - [ ] 13.3 实现增量数据推送
    - WebSocket仅推送新增数据
    - _Requirements: 10.3_
  - [ ] 13.4 编写增量数据提取属性测试
    - **Property 14: 增量数据提取正确性**
    - **Validates: Requirements 10.3**
  - [ ] 13.5 实现前端节流策略
    - 动画触发频率限制在每100ms一次
    - _Requirements: 10.5_

- [ ] 14. 数据导出功能
  - [ ] 14.1 创建数据导出工具
    - 创建 `utils/dataExporter.js`
    - 实现报文导出为CSV/JSON格式
    - 实现带宽数据导出为CSV格式
    - _Requirements: 8.2, 8.3_
  - [ ] 14.2 实现仿真报告生成
    - 增强 `components/SimulationReport.vue`
    - 生成包含仿真摘要、带宽统计、告警汇总的报告
    - _Requirements: 8.4_

- [ ] 15. 仿真前置条件检查
  - [ ] 15.1 增强健康自检功能
    - 检查拓扑中是否存在至少两个设备节点和一条连接
    - 检测未配置协议的端口
    - 检测不兼容的协议连接
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  - [ ] 15.2 编写拓扑验证属性测试
    - **Property 17: 拓扑验证正确性**
    - **Validates: Requirements 12.1, 12.2, 12.3**

- [ ] 16. Checkpoint - 确保所有前端测试通过
  - Ensure all tests pass, ask the user if questions arise.

## 第二部分：后端实现

- [ ] 17. SimPy 仿真内核重构
  - [ ] 17.1 创建 SimPy 仿真运行器
    - 创建 `service/simulation_runner.py`
    - 实现 `SimulationRunner` 类继承 `threading.Thread`
    - 使用 `simpy.rt.RealtimeEnvironment` 实现实时同步
    - 实现步进循环模式（每次推进100ms）
    - 实现线程安全的控制信号（paused/stopped Event）
    - _Requirements: 9.1, 9.2, 9.4_
  - [ ] 17.2 重构仿真引擎为 SimPy 架构
    - 修改 `simulation_engine.py`
    - 集成 SimulationRunner
    - 实现设备进程和总线资源的创建
    - 实现暂停/继续/停止控制
    - _Requirements: 9.1, 9.2_
  - [ ] 17.3 实现仿真速度调节
    - 通过 `RealtimeEnvironment.factor` 参数控制速度
    - 支持0.5x-4x速度调节，实时生效
    - _Requirements: 9.3_
  - [ ] 17.4 实现单步执行功能
    - 执行一个时间片（100ms）后自动暂停
    - _Requirements: 9.4_
  - [ ] 17.5 实现定时停止功能
    - 达到设定时长后自动停止
    - _Requirements: 9.5_

- [ ] 18. 协议仿真模型实现
  - [ ] 18.1 创建协议模型基类
    - 创建 `service/protocol_models/base_protocol.py`
    - 定义协议模型接口（start_process, emit_message, inject_fault）
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [ ] 18.2 实现 MIL-STD-1553B 协议模型
    - 创建 `service/protocol_models/mil1553b_model.py`
    - 实现 BC（总线控制器）进程：调度表执行、指令发送
    - 实现 RT（远程终端）进程：监听响应、状态字生成
    - 使用 `simpy.Resource` 模拟总线独占
    - 模拟12-32μs响应时间
    - _Requirements: 11.1_
  - [ ] 18.3 实现 CAN 总线协议模型（集成 python-can）
    - 创建 `service/protocol_models/can_model.py`
    - 使用 `python-can` 的 `virtual` 接口创建虚拟CAN通道
    - 实现 `can.Notifier` 消息监听
    - 实现非破坏性位仲裁模拟
    - 支持错误帧注入
    - _Requirements: 11.2, 6.2_
  - [ ] 18.4 实现 RS422/RS485 协议模型
    - 创建 `service/protocol_models/rs485_model.py`
    - 使用 `simpy.Resource(capacity=1)` 模拟半双工总线
    - 实现冲突检测和退避机制
    - 根据波特率计算传输时间
    - _Requirements: 11.3_
  - [ ] 18.5 实现 LAN/以太网协议模型
    - 创建 `service/protocol_models/lan_model.py`
    - 使用 `simpy.Store` 模拟交换机缓冲区
    - 模拟排队延迟和处理延迟
    - _Requirements: 11.4_

- [ ] 19. 故障注入服务
  - [ ] 19.1 创建故障注入服务
    - 创建 `service/fault_injector.py`
    - 实现链路断开模拟（停止对应边的报文传输）
    - 实现设备故障模拟（停止节点进程）
    - _Requirements: 6.1, 6.3_
  - [ ] 19.3 实现丢包率控制
    - 按设定概率随机丢弃报文
    - 记录丢包统计
    - _Requirements: 6.4_
  - [ ] 19.4 编写丢包率统计属性测试
    - **Property 10: 丢包率统计正确性**
    - **Validates: Requirements 6.4**
  - [ ] 19.5 实现延迟注入
    - 为报文传输添加额外延迟
    - _Requirements: 6.5_

- [ ] 20. 事件触发服务
  - [ ] 20.1 创建事件触发服务
    - 创建 `service/event_trigger.py`
    - 实现事件配置管理（CRUD）
    - _Requirements: 7.1_
  - [ ] 20.2 实现条件匹配引擎
    - 支持时间点、报文数量、带宽阈值、报文内容条件
    - _Requirements: 7.2, 7.4_
  - [ ] 20.3 实现动作执行引擎
    - 支持发送报文、注入故障、暂停仿真、记录日志动作
    - _Requirements: 7.3, 7.4_

- [ ] 21. 告警检测器增强
  - [ ] 21.1 增强告警检测器
    - 修改 `alarm_detector.py`
    - 实现拥塞检测（负载率>95%）
    - 实现冲突检测（同时竞争总线，集成SimPy资源竞争事件）
    - 实现丢包检测
    - 实现带宽超限检测
    - 实现数值溢出检测
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 22. 协议解析服务
  - [ ] 22.1 创建协议解析服务
    - 创建 `service/protocol_parser.py`
    - 实现1553B协议编解码（Command Word, Status Word, Data Word）
    - 实现CAN协议编解码（集成python-can消息格式）
    - 实现RS422/RS485协议编解码
    - 实现以太网协议编解码
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 23. Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 24. API接口增强
  - [ ] 24.1 增强仿真控制接口
    - 修改 `simulation_controller.py`
    - 添加暂停/继续接口（控制SimulationRunner线程）
    - 添加速度调节接口（修改RealtimeEnvironment.factor）
    - 添加单步执行接口
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ] 24.2 添加故障注入接口
    - 添加故障注入API（链路断开、错误帧、设备故障）
    - 添加故障清除API
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ] 24.3 添加事件触发接口
    - 添加事件配置CRUD API
    - 添加手动触发API
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  - [ ] 24.4 增强数据导出接口
    - 支持PCAP格式导出
    - 支持PDF报告生成
    - _Requirements: 8.2, 8.4_

- [ ] 25. WebSocket增强
  - [ ] 25.1 增强WebSocket消息协议
    - 添加动画事件推送（traffic/error/node_active类型）
    - 添加事件触发通知
    - 优化增量数据推送（背压策略：50ms缓冲合并）
    - _Requirements: 2.1, 7.4, 10.3_

- [ ] 26. 数据持久化增强
  - [ ] 26.1 增强数据访问层
    - 修改 `simulation_dao.py`
    - 添加故障配置表操作
    - 添加事件配置表操作
    - 添加历史会话查询
    - _Requirements: 8.1, 8.5_

- [ ] 27. 依赖安装和配置
  - [ ] 27.1 更新后端依赖
    - 在 `requirements.txt` 中添加 `simpy>=4.0.0`
    - 在 `requirements.txt` 中添加 `python-can>=4.0.0`
    - 添加 `hypothesis>=6.0.0` 用于属性测试
    - _Requirements: 全部后端需求_

- [ ] 28. 清理旧仿真代码
  - [ ] 28.1 清理前端旧代码
    - 删除不再使用的旧仿真组件和composables
    - 清理未使用的导入和废弃的样式
    - 确保 `simulation/` 目录结构清晰
    - _Requirements: 代码质量_
  - [ ] 28.2 清理后端旧代码
    - 删除被SimPy架构替代的旧仿真逻辑
    - 清理未使用的导入和废弃的函数
    - 确保 `service/` 目录结构清晰
    - _Requirements: 代码质量_
  - [ ] 28.3 验证其他功能不受影响
    - 测试项目管理功能正常
    - 测试设备管理功能正常
    - 测试协议管理功能正常
    - 测试用户权限功能正常
    - _Requirements: 系统稳定性_

- [ ] 29. Final Checkpoint - 确保所有测试通过
  - Ensure all tests pass, ask the user if questions arise.
