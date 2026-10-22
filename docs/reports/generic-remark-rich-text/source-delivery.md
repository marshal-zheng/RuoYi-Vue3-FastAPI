# 源分支代码交接

用户已明确要求：“你完成任务告诉我 交付到源分支我自己测”。因此本次交付代码及自动验证结果，真实七入口、主题、density、portal焦点和键盘操作由用户验收。没有使用computer use；不把用户接管验收记为界面已通过，也不声明完整spec的23项验收已完成。

## 集成边界

应用以源分支std的d625a30为集成基线，保留已提交图标更新及源当前其他依赖、resolutions、icons:check。host以codex/http-vue-query-phase-a的0040e473为基线；编辑器独立仓以main的75fcdbd为基线。输入快照、实现提交、集成提交与最终源提交分别记录在Git metadata执行上下文/交付账本中。

正常安装组合为：

| 包 | 候选 | SHA-256 |
| --- | --- | --- |
| @zxio/text-editor | 1.0.0-remark-a.20261022.5 | 42cda3aa6d7cd9528325dbcaabf16149263aa1db3f868a3a1e8adbc3d7ae3f1e |
| @zxio/schema-form | 0.1.0-remark-a.20261022.1 | 1fadc9526ab14583a82172a88216fc126a1cf731b0479ca386be6c29c7545be2 |
| @zxio/zxui | 3.0.0-next.0-remark-raw.20261022.1 | 9a8b2540581fdee21da846ab71e4086d97c4d17a20bb6d17495ff7b7f22fc555 |

ZXUI合成候选从已提交图标基线，仅吸收源已有InputNumber受控原文API的9个路径（实际3源码+1测试变化），避免SchemaForm数字字段退回无text/update:text能力的产物；没有吸收其他dirty库业务。candidate-provenance.json记录来源、输入hash及完整验证。应用正常Vitest直接从已安装公开leaf导入的数字raw/step/readonly探针另行验证产物，未依赖source alias。

## 已知验证与手测边界

后端集成496项、SchemaForm125项、编辑器最终158项通过。应用完整集成测试在editor.4时1440项中1428通过、12失败；失败完整名称集合与最新源HEAD+dirty独立副本的12项完全相等（User Store6、devMenu2、simulation websocket4），新增0。editor.5的链接IME修复另外以发布包公开Field做旧包红/新包绿，并重跑受影响公开往返及最终构建，不把旧版本全量记录伪写为新版本全量。

三个不在交付变更集内的源当前文件（project handler/test、simulation WebSocket composable）在集成验收中作为未暂存runtime overlay保留；它们不属于本轮提交，源原字节不会被覆盖。缺少的测试fixture与库version由已准备且版本匹配的忽略生成资产原样补齐，其来源/hash另有运行证据；不以改业务代码掩盖环境缺口。

Ruff全仓lint/format仍有输入基线问题。92个变更Python文件按路径/规则计数：当前272、输入554，无新增规则计数；format当前6、输入22，无新增未格式化文件。既有handle函数PLR0915指标减少但未达阈值，不声称全库门禁为绿。详见各验证报告及Git metadata中的baseline audit。

## 手测前数据库准备

本轮只在隔离数据库演练，未迁移日常ruoyi-fastapi库。只读检查确认日常七列仍为VARCHAR(500)。测试新代码前，按[升级恢复手册](upgrade-recovery.md)完成停写、验证完整备份、备注迁移及只读核验；不要让旧版应用继续写JSON结构。

原目录历史发布包的既有checksum/capability元数据损坏与全局schema drift继续作为部署限制，见[归因报告](deployment-baseline-boundary.md)。有效legacy样例与隔离副本六CLI通过证明本轮机制，不代表原目录已经可部署；不修改历史checksum，也未发布npm或执行生产发布。

最终源分支验证、提交与保留工作区状态待交付事务记录补充；未验证项目不会被勾选为通过。
