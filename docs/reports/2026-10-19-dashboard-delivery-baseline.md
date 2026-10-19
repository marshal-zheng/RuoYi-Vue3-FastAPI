# Dashboard 图表设置交付基线

日期：2026-10-19。当前交付为系统监控 → 服务监控中的单个 CPU 时序图设置，覆盖嵌套配置、
条件字段、实时预览、取消恢复及真实保存回显。未扩大为仿真页面或全量 Dashboard 设置迁移。

同名本地标签：`dashboard-schema-card-2026-10-19`，业务仓与 ZXUI 根仓分别落在最终文档提交。
前一阶段 Schema/岗位/DAG 标签 `schema-cross-scenario-2026-10-19` 保持不变。

| 仓库  | 完整提交                                   | 职责                                                                   |
| ----- | ------------------------------------------ | ---------------------------------------------------------------------- |
| ZXUI  | `7c054513913296c5be82234bc7f556b265ee6743` | feat(dashboard): add revisioned persistence and saved layout baselines |
| ZXUI  | `25d1713874bccf7c0f4d36c5b267514139fec953` | feat(dashboard-widgets): add standard widgets and source integration   |
| ZXUI  | `311094b035ed6b6a74d6aea6952b585d7a09c02c` | feat(dashboard): add nested chart settings and candidate saves         |
| RuoYi | `65ad5dc598f299807f6b572f27365079d7e4b34a` | feat(仪表盘): 增加带版本校验的布局持久化                               |
| RuoYi | `937ff33ac0b9f7a8056b8b0c81ac1e4a57d0fd66` | feat(服务监控): 接入可保存的图表卡片设置                               |

顺序：ZXUI 持久化 → widgets/源码接入 → 嵌套设置/candidate save；业务后端持久化 → 监控设置。
chart 使用独立仓 `7238cd9c1c82df7fbae2362da7601584e4f718a7` 的已提交源码，无新 chart/X6 提交。
Schema 仍消费同一 0.1.0 closeout 产物，运行时代码不变。

| 包                      | 版本  | vendor 文件                                                     | SHA256                                                             |
| ----------------------- | ----- | --------------------------------------------------------------- | ------------------------------------------------------------------ |
| @zxio/chart             | 2.0.0 | `zxio-chart-2.0.0-dashboard-committed.20261019.tgz`             | `97efdb39f74f0cd8dd5c16019e5621db3afcbaf8c821325e30dedccc506f64b1` |
| @zxio/dashboard         | 0.1.0 | `zxio-dashboard-0.1.0-dashboard-committed.20261019.tgz`         | `cb96cba3d3fefcf834f9cca8e63b106acf632da167a9bb477dff649e6a550a59` |
| @zxio/dashboard-widgets | 0.1.0 | `zxio-dashboard-widgets-0.1.0-dashboard-committed.20261019.tgz` | `9577f3689702c010a0ba57c0b2d3c4798ee2003c9d53775e3dd6ae95f39e5115` |
| @zxio/schema-form       | 0.1.0 | `zxio-schema-form-0.1.0-closeout.20261019.tgz`                  | `97b2f642657d4cd6cd3a59138beaa3fcce006199fa3b7412c1df9db2a6a3f98c` |

已提交 package.json/锁文件只含这三个包的切换及 widgets markdown 依赖闭包；Swagger、
图布局性能快照和其他任务条目仍留在工作区。后端 registry/Atlas 仅纳入 Dashboard 注册。
共享文件按片段提交，没有覆盖其他在研修改。

隔离提交快照验证通过 81 项回归（库 49、源码接入 13、后端 8、业务/岗位反馈 11）、库/业务
类型检查、窄 lint、frozen/immutable 安装、chart 构建/打包及业务正式构建。正式构建另完成
15 项浏览器检查；保存为版本 10 并刷新/独立 GET 回读后，条件恢复到版本 11，文档与验收前
版本 9 完全相等。历史修订保留。一次共享账号会话 401 经重新登录恢复后保存成功。

完整原始日志、截图、锁审计、工作区保留与摘要清单位于 ZXUI 同标签下：
`docs/reports/dashboard-schema-card-2026-10-19/commit-baseline/README.md` 和 `manifest.json`。
本地查看：[完整基线](/Users/hqz/Downloads/element-plus/docs/reports/dashboard-schema-card-2026-10-19/commit-baseline/README.md)。
上阶段 44 项浏览器/47 项回归为历史实现证据，不冒充本次新增执行。

没有推送、发布 npm 或部署生产。临时浏览器与端口 4187 preview 已关闭，既有 80/8088 服务保留。
