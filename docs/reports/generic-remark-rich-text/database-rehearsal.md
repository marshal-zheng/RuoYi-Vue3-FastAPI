# 数据库演练入口

正式证据汇总见 [迁移演练报告](migration-rehearsal.md)，操作顺序见 [升级恢复手册](upgrade-recovery.md)。

- 数据库与门禁：69 tests passed，其中 20 个真实 MySQL 用例。
- 受管写入与产物：33 tests passed。
- 仓库外交付副本：finalize、deploy、bootstrap、dev-sync 两次、verify 全部退出 0。
- 原发布目录历史 artifact 异常保留为交付阻塞；真实 PostgreSQL 和旧应用恢复冒烟未执行。
