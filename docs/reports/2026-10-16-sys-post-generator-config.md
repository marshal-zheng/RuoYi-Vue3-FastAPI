# sys_post 生成配置补全与真实 ZIP 验证

日期：2026-10-16。本轮修正本地开发数据库中已有的 `sys_post` 生成配置，未修改业务、后端或 ZXUI 生产代码。

## 根因与责任边界

真实回读的生成记录为 `tableId=1`：表描述、功能名和前端模板类型为空，`options=null`，已有 10 列映射及主键 `post_id`。另以只读查询确认，当前数据库 `sys_post` 的表注释确实为空。

- 初始化：`GenUtils.init_table`（`ruoyi-fastapi-backend/utils/gen_util.py:14`）从数据库表名、表注释和生成器默认配置初始化名称，功能名从表描述派生。它无法从空注释推导“岗位信息”，导入也不代表用户已经完成生成设置。
- 保存：编辑页 `editTable.vue:173` 收集完整表配置、字段映射和 `params`；`PUT /tool/gen` 执行必填校验，`GenTableService.edit_gen_table_services`（`module_generator/service/gen_service.py:117`）将 `params` 序列化为 `options`，事务保存后回读。现有调用能够正常持久化，没有复现字段丢失。
- 生成：`TemplateUtils.prepare_context`（`utils/template_util.py:57`）在 `options` 为空时阻止生成。修复前真实 ZIP 请求返回 HTTP 400、“请先完善生成配置信息”；这是当前配置不完整的保护，不属于 Axios、下载入口或 ZXUI 缺陷。

定向核对了成熟上游 [RuoYi GenUtils 初始化](https://raw.githubusercontent.com/yangzongzhuan/RuoYi-Vue/master/ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java) 和 [VelocityUtils 模板上下文](https://raw.githubusercontent.com/yangzongzhuan/RuoYi-Vue/master/ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java)：初始化同样基于表注释推导名称。上游的菜单默认值不应代替当前业务的真实菜单归属，也没有必要为这条未完成配置引入新的初始化机制。

## 修复

复用现有编辑页生产提交函数和真实 `PUT /tool/gen`，完整携带原表配置及 10 列映射，保存以下值：

| 字段 | 修复前 | 修复后 | 依据 |
| --- | --- | --- | --- |
| tableComment | 空 | 岗位信息表 | 当前 `PostDO` 的领域说明 |
| functionName | 空 | 岗位信息 | 按既有规则从表描述去除“表” |
| tplWebType | 空 | element-plus | 当前 Vue3 业务及既有生成模板 |
| params.parentMenuId / options | null | 父菜单 ID 1，保存为 JSON | 真实“岗位管理”菜单 ID 104 的 parentId；父级为“系统管理” |

保留 `SysPost`、`module_admin.system`、`system`、`post`、作者、ZIP 生成方式、原字段映射和主键；更新时间随正常保存更新。没有改数据库表注释或结构、岗位业务记录，也没有执行 ZIP 中的生成代码或菜单 SQL。

选择已有配置保存流程，是因为当前证据证明问题在该记录缺项。收益是恢复当前真实业务生成，并完整保留保存和生成校验；代价是这是本地数据库配置修复，其他环境若有同样缺项，也需在其生成配置中补全，不能靠代码提交自动改变数据。

## 验证证据

通过 JSDOM 加载现有 Vue 页面生产提交／生成函数、业务 API、真实 Axios 和源码 `@zxio/http`，请求本地 FastAPI :8088、Docker MySQL 和已有 Redis。没有使用浏览器或 computer use。表单校验回调、loading 展示和文件保存适配器由探针替代；后端校验、数据库保存／回读和 ZIP 响应均为真实执行。

| 实际检查 | 结果 |
| --- | --- |
| 修复前生成 | HTTP 400，配置不完整；没有保存错误文件，pending/loading 释放 |
| 空表描述保存 | HTTP 422，“表描述不能为空”；回读完全未改变 |
| 空功能名保存 | HTTP 422，“生成功能名不能为空”；回读完全未改变 |
| 现有编辑页提交与回读 | 成功；4 项补全配置持久化，10 列映射及 PK 保留 |
| 修复后同一生成入口重试 | 成功得到 `vfadmin.zip`，9315 字节、8 个非空文件，ZIP CRC 检查通过 |
| ZIP 内容 | 5 个后端 Python 文件、菜单 SQL、前端 API 和 Vue 页面；确认 Vue3 `<script setup>`，SQL 的父菜单为 1，权限为 `system:post:list` |
| 数据边界 | 4 条岗位记录、94 条菜单记录不变；生成记录仍为原来的 1 条，无临时导入记录 |
| 独立只读复核 | 支持使用现有完整保存，不需要修改生产代码或放宽校验 |

7 项真实链路检查全部通过，详情及配置前后摘要见 [actual.json](evidence/2026-10-16-sys-post-generator-config/actual.json)。探针执行命令为 `node /tmp/ruoyi-sys-post-generator/actual-probe.cjs`，退出码 0。

本轮无生产代码变更，未新增单元测试或重复运行全量构建。原有工作区文件 hash 核对、`git diff --check` 及运行环境清理结果另见同目录证据中的收尾记录。保留修复后的生成配置，临时 ZIP 已删除，验证账号已退出。
