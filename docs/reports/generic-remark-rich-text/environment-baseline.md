# 环境与隔离基线

- 日期：2026-10-22；未使用 computer use，未切换现有服务。
- 应用源：/Users/hqz/dev/RuoYi-Vue3-FastAPI，std，262ec420；224 个 tracked 路径改动，大量未跟踪历史报告/临时产物。
- 应用实施：/Users/hqz/dev/RuoYi-Vue3-FastAPI/.worktrees/generic-remark-rich-text，codex/generic-remark-rich-text；输入快照 de5a9993f17f0a2d38d46e0d1c8b5dc8a982dda9（304 路径）。manifest/context 在该 worktree 的 Git metadata；不导入 .tmp、旧报告和领域页面修改。依赖使用源 checkout 的只读运行入口，安装或包改动需另行隔离 node_modules。
- ZXUI 宿主：/Users/hqz/Downloads/element-plus/.worktrees/generic-remark-rich-text，codex/generic-remark-rich-text；宿主基线 1c593805 + 110 个当前构建/组件依赖路径快照。
- text-editor 为独立仓库：上述宿主下 packages/text-editor，codex/generic-remark-rich-text，起点 75fcdbd084a9b357c26329b052956f208ab6e0d1，源 main clean；包版本 1.0.0。
- 日常 MySQL 未迁移；真实演练另建 ruoyi_remark_* 隔离库，备份正文不入 Git。
- 基线：post-form.test.ts 12 passed；test_editor_templates.py 21 passed。一次测试路径拼写错误，不作为产品失败。
- 官方方案核对：Tiptap JSON persistence；SQLAlchemy JSON none_as_null / 整值替换；MySQL DDL implicit commit。沿用批准设计，不引入新编辑内核或在线双写机制。

参考：[Tiptap](https://tiptap.dev/docs/editor/core-concepts/persistence)、[SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON)、[MySQL](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html)。

实施补充：前端依赖在安装候选包前已独立复制 node_modules，后续安装只在任务工作区。源码主仓有并发变化，逐路径观察结果见 source-preservation-audit.json；未将其覆盖、同步或交付。宿主补输入146d18ab3仅复制既有公开core出口，属于输入快照，不属于本轮功能改动。
