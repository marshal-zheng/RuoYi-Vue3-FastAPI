# 真实本地部门 Query 验证证据

日期：2026-10-17。独立手工探针位于 `ruoyi-fastapi-frontend/tests/manual/department-query/`，采用真实业务 `deptCommands`、查询工厂、应用 QueryClient、原生 useQuery 订阅和 HTTP 层；不加载 MSW、测试 setup 或接口 fixture，没有 computer use。

安装包模式最初连续创建父子部门后，等待活动列表/树更新超时（15 秒）。`installed-initial-failure.json` 保留原始结论：两个写入完成，管理列表与用户树都确实发生失效后的读取，finally 删除两条并验证本次 marker 已不存在。当时未保留两份缓存各自的临时节点，不能确认是哪份数据未更新，也不能确认根因。后端存在事务 commit 前失效 Redis cache 的潜在旧读回填窗口，这是静态推断，并未被本次证据证明。未通过等待第一个刷新、人工 invalidation 或业务源码补丁掩盖该时序。

随后第一次安装包复跑通过（`installed-actual.json`）；再按相同连续写时序，安装包追加三轮、源码模式共三轮全部通过（`installed-repeat-{1,2,3}.json`、`source-repeat-{1,2,3}.json`；`source-actual.json` 与 source-repeat-1 是同一轮的副本）。即实际业务链路共 8 轮，7 轮通过、1 轮初始超时；后续未再次触发新增的限量诊断。**首次超时根因仍未确定，不能据后续通过声称已消除并发旧读边界。**

通过轮次均验证以下真实行为：两个 user-tree 订阅共享一次冷请求；创建后列表/树出现父子；改名后列表、两份树订阅更新及用户列表真实重读；停用后管理列表保留、正常部门树移除，启用后恢复；排除树不含自身与后代；编辑快照来自真实详情；非法 status 得到真实 HTTP 422，独立成功缓存保留。每轮只创建两个唯一 `codex_dept_query_` 临时部门，删除两个，并验证该前缀在真实管理列表中不存在；8 轮合计创建 16 条、删除 16 条。每轮自建登录会话均已正常退出。

权限约束来自实际后端：管理列表与排除树要求 `system:dept:list`，用户部门树要求 `system:user:list`。使用已有 admin 真实权限完成验证；未调用用户、角色、权限或现有部门的业务写接口，正常登录/退出产生的会话与审计按既有机制处理。用户列表按本次临时部门过滤，验证了写后重读依赖，未创建用户来验证嵌入部门名称的实际用户行。部门清理使用现有删除 API 的软删除语义，没有物理删除审计数据。

`runtime-recovery.json` 记录现有 Redis 的恢复：本机 Colima 内原 Redis 健康且持久化正常，无其他活动客户端，但宿主 6379 拒绝连接。正常重启原容器未恢复；父代理仅重试 Lima 原有 SSH master 的同一原生端口转发，之后宿主 RESP 为 `+PONG`，源后端 `/docs` 为 HTTP 200。没有新增代理、重启共享 Colima、修改业务 env、重置/seed 数据库或改权限。任务自建后端 PID 与停止结果也记入该文件；现有 MySQL/Redis 保持。真实后端来自源目录（HEAD `94528292c3483af52cdfeab6a95cb0d76d87bbb9`，当时有 91 个既有 backend dirty 条目），不是将这些未提交实现当成任务隔离副本基线；该文件保留部门服务、查询缓存、事务管理和两个 controller 的 SHA-256。未复制 env、密钥或完整 dirty diff。

边界：这些是业务查询/命令与实际后端 HTTP 的集成证据，不是组件 DOM、TreeSelect 可见标签、焦点、浏览器表单操作或系统交互验收。组件与单元测试证据由主报告单独列出。本目录不保存 token、密码、请求头、完整错误或完整用户数据。
