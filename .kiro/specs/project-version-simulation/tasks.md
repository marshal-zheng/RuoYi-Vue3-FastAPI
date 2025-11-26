# 实施计划（基于现有实现扩展）

## 任务列表

- [x] 1. 后端基础设施搭建
- [x] 1.1 创建数据库表结构
  - 在 `ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql` 添加仿真相关表
  - 表：`sys_simulation_session`（会话）、`sys_simulation_message`（报文）、`sys_simulation_bandwidth`（带宽）、`sys_simulation_alarm`（告警）
  - _需求: 1.1, 2.1_

- [x] 1.2 创建后端数据模型
  - 在 `module_admin/entity/do/` 创建DO模型：`simulation_do.py`
  - 在 `module_admin/entity/vo/` 创建VO模型：`simulation_vo.py`
  - 使用Pydantic进行数据验证
  - _需求: 1.1, 2.1_

- [x] 1.3 创建DAO层
  - 在 `module_admin/dao/` 创建 `simulation_dao.py`
  - 实现异步数据库操作（使用SQLAlchemy async）
  - _需求: 1.1, 2.1_

- [x] 2. 后端核心服务实现
- [x] 2.1 实现带宽计算服务
  - 在 `module_admin/service/` 创建 `bandwidth_calculator.py`
  - 实现三种协议的带宽计算公式（LAN、RS422/RS485、CAN）
  - 添加单元测试验证公式正确性
  - _需求: 3.2, 3.3, 3.4_

- [x] 2.2 实现告警检测服务
  - 在 `module_admin/service/` 创建 `alarm_detector.py`
  - 实现回环检测和多连接检测
  - 基于拓扑数据进行静态分析
  - _需求: 4.1, 4.2_

- [x] 2.3 实现仿真引擎核心
  - 在 `module_admin/service/` 创建 `simulation_engine.py`
  - 使用asyncio实现定时任务（100ms tick）
  - 实现报文生成逻辑（基于接口配置的频率参数）
  - 实现仿真状态机（created → running → stopped）
  - _需求: 1.2, 2.1, 2.2_

- [x] 2.4 实现仿真服务层
  - 在 `module_admin/service/` 创建 `simulation_service.py`
  - 整合仿真引擎、带宽计算器、告警检测器
  - 实现会话管理、数据查询、导出功能
  - _需求: 1.1, 1.2, 1.3, 5.3_

- [x] 3. 后端API和WebSocket
- [x] 3.1 创建仿真控制器
  - 在 `module_admin/controller/` 创建 `simulation_controller.py`
  - 实现REST API：创建会话、启动、停止、查询、导出
  - 添加权限控制装饰器
  - _需求: 1.1, 1.2, 1.3, 5.3_

- [x] 3.2 实现WebSocket实时推送
  - 在仿真控制器添加WebSocket端点
  - 实时推送：报文数据、带宽数据、告警数据
  - 实现心跳机制和断线重连
  - _需求: 2.3, 3.5, 4.3_

- [x] 4. 前端Composables重构（工程化）
- [x] 4.1 创建仿真API Composable
  - 在 `ruoyi-fastapi-frontend/src/views/project/simulation/composables/` 创建 `useSimulationApi.js`
  - 封装所有仿真相关的HTTP请求
  - 统一错误处理和loading状态管理
  - _需求: 1.1, 1.2, 1.3_

- [x] 4.2 创建WebSocket Composable
  - 创建 `useSimulationWebSocket.js`
  - 封装WebSocket连接、消息处理、自动重连
  - 提供响应式数据流
  - _需求: 2.3, 3.5_

- [x] 4.3 创建带宽数据管理Composable
  - 创建 `useBandwidthData.js`
  - 管理带宽数据缓存（600秒滑动窗口）
  - 提供数据聚合和计算功能
  - _需求: 3.1, 3.6_

- [x] 4.4 创建告警管理Composable
  - 创建 `useAlarmManager.js`
  - 管理告警列表、过滤、统计
  - 提供告警通知功能
  - _需求: 4.3, 4.4_

- [x] 5. 前端UI组件开发（注重UX）
- [x] 5.1 创建仿真控制面板组件
  - 不需要单独组件，控制功能已在主页面实现
  - 使用现有的SimulationStatusPanel显示进度
  - _需求: 1.2, 1.3_

- [x] 5.2 创建带宽图表组件
  - 创建 `BandwidthChartPanel.vue`
  - 使用ZxChart配置ECharts折线图
  - UX优化：平滑动画、数据点提示、缩放交互、多端口切换
  - 实现600秒滑动窗口
  - _需求: 3.1, 3.5, 3.6, 3.8_

- [x] 5.3 创建报文列表组件
  - 创建 `MessageListPanel.vue`
  - 使用ZxGridList实现列表展示和分页
  - UX优化：实时更新、过滤器、搜索功能
  - 添加导出功能按钮
  - _需求: 5.1, 5.2, 5.3, 5.4_

- [x] 5.4 创建告警面板组件
  - 创建 `AlarmPanel.vue`
  - 设计：告警列表、告警详情、告警统计卡片
  - UX优化：告警分类标签、严重程度颜色、通知提示
  - _需求: 4.3, 4.4_

- [ ] 5.5 优化拓扑图报文流动动画
  - 扩展现有的 `useSimulationAnimation.js`
  - 添加报文流动轨迹动画
  - UX优化：流畅的动画效果、端口高亮、报文计数显示
  - _需求: 1.4, 2.3_

- [x] 6. 前端页面集成和布局优化
- [x] 6.1 重构仿真页面布局
  - 更新 `ruoyi-fastapi-frontend/src/views/project/simulation.vue`
  - 采用zx-floating-panel悬浮面板布局，不占用主界面空间
  - 所有面板可收起/展开，提供更好的用户体验
  - _需求: 1.1_

- [x] 6.2 集成所有组件到仿真页面
  - 集成带宽图表、报文列表、告警面板（均使用zx-floating-panel）
  - 实现WebSocket实时数据流推送
  - 添加组件间数据通信
  - _需求: 1.1, 1.2, 1.3_

- [ ] 6.3 实现仿真数据持久化
  - 仿真结束后自动保存数据到后端
  - 支持查看历史仿真记录
  - _需求: 5.1, 5.3_

- [ ] 7. UX体验优化
- [ ] 7.1 添加操作引导和提示
  - 首次使用时显示操作引导
  - 关键操作添加Tooltip提示
  - 空状态设计（无数据时的友好提示）
  - _需求: 1.1_

- [-] 7.2 优化加载和过渡动画
  - 添加骨架屏loading效果
  - 组件切换添加过渡动画
  - 数据更新添加平滑过渡
  - _需求: 1.1_

- [ ] 7.3 响应式设计适配
  - 适配不同屏幕尺寸
  - 优化小屏幕下的布局
  - _需求: 1.1_

- [ ] 8. 测试和质量保证
- [ ] 8.1 单元测试
  - 测试带宽计算公式
  - 测试告警检测逻辑
  - 测试Composables功能
  - _需求: 3.2, 3.3, 3.4, 4.1, 4.2_

- [ ] 8.2 集成测试
  - 测试完整仿真流程
  - 测试WebSocket实时通信
  - 测试数据导出功能
  - _需求: 1.2, 1.3, 2.3, 5.3_

- [ ] 8.3 性能测试和优化
  - 测试20节点仿真性能
  - 测试600秒数据渲染性能
  - 优化内存使用和渲染性能
  - _需求: 3.8_

- [ ] 9. 文档和部署
- [ ] 9.1 编写技术文档
  - API文档
  - 组件使用文档
  - 架构设计文档

- [ ] 9.2 编写用户手册
  - 仿真功能使用指南
  - 常见问题FAQ

- [ ] 9.3 部署和验收
  - 部署到测试环境
  - 用户验收测试
  - 收集反馈并优化
