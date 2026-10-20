# Schema Form Formily 任务快照

当前任务使用 `zxio-schema-form-0.1.0-formily.20261020-r2.tgz`，包版本 0.1.0，SHA256 `a046609c0a91d9f343410a10daa5997ee8c00820e767f472feecefabb791592f`。来源为 ZXUI 隔离 worktree packages/schema-form/dist，由 package build 与 npm pack 生成，未发布 npm。

独立表单入口为 @zxio/schema-form/formily，宿主显式安装 @formily/core、@formily/vue、@formily/reactive、@formily/validator 精确 2.3.7。root/fields 的 JS 与声明均无引擎依赖，DAG/Dashboard 继续拥有原 draft/history/preview。

源码联调使用 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus/worktrees/schemaform-formily`。源 checkout 不写回。岗位 Dialog 仅拥有显示、记录身份和读取；Formily 会话拥有编辑值/校验/保存基线，不绑定 Element Plus FormInstance。服务写入未知后读取核对，禁止盲目重发。

本轮回归包括源码挂载与 tarball 消费；本机 Redis/Colima 故障已在保全备份后恢复；真实岗位与协议 HTTP 读写/回读/核对/清理通过。happy-dom 不证明人工视觉。完整证据在 ZXUI docs/specs/SCHEMAFORM-formily-runtime-migration/evidence/execution/。
