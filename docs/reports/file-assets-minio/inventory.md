# 文件资产 MinIO 接入：调用、数据与验证入口盘点（任务 1）

盘点日期：2026-10-24。基线：分支 `std` 提交 `db545dab`（工作区干净，仅 `.cursor/handoffs/`、`.tmp/`、一个 vendor tgz 未跟踪）。方法：只读代码搜索（独立只读子代理逐类复核 + 主代理抽查）与本地只读 SQL/目录检查。本报告只描述当前事实与迁移归属，不代表任何迁移已经执行。

缩写：`B` = `ruoyi-fastapi-backend/`，`F` = `ruoyi-fastapi-frontend/`。

## 1. 持久文件入口与真实消费者

| 入口 | 现状证据 | 真实消费者 | 处理（任务） |
| --- | --- | --- | --- |
| `POST /common/upload` | `B/modules/system/api/common_controller.py:11`，`common_service.py:20-57` 写 `vf_admin/upload_path/upload/Y/M/D/<名>_<时间>A<随机>.<后缀>`，返回 `/profile/...` | 前端唯一网络调用 `F/src/composables/useAuthenticatedUpload.ts:39`；三个组件的 `action="/common/upload"` 只是装饰（被 `http-request` 覆盖）：FileUpload:5、ImageUpload:5、Editor:4 | 迁到 `POST /file-assets/uploads`（9、11）；最终删除（16） |
| `GET /common/download/resource` | `common_service.py:84-109`，把 `/profile` 映射回上传目录 | **无**：前后端均无调用；只有生成 SDK `sdk.gen.ts:998` 与 mock 登记 `real-only.json:147` | 删除（16），无迁移需求 |
| `/profile` 静态挂载 | `B/sub_applications/staticfiles.py:10`，**未鉴权**，扩展名白名单含 `html/htm` | 头像 URL、FileUpload/ImageUpload/ImagePreview/Editor 以 `VITE_APP_BASE_API + /profile/...` 访问 | 由 `/file-assets/{id}/content` 取代；挂载删除（16） |
| `POST /system/user/profile/avatar` | `user_controller.py:389-434`，`avatarfile: bytes` 无类型/大小校验，一律存 `.png` 到 `upload_path/avatar/...`，返回 `{imgUrl}` | `F/src/api/system/user.ts:206`、`queries/system/user.ts:285`、`views/system/user/profile/userAvatar.vue:155-160` | 保留路由与表单字段名，改为 UploadFile + 资产绑定，硬切响应 `{avatarAssetId, avatarUrl}`（10） |
| 公告富文本图片 | `F/src/components/ui/Editor/index.vue:159` 插入 `VITE_APP_BASE_API + res.fileName`，即 **`/api/profile/...` 带环境前缀写入数据库** | 唯一编辑入口 `F/src/views/system/notice/components/NoticeDlg.vue:38` | 稳定地址 + HTML 净化 + 同事务引用绑定（11），历史引用迁移（14） |

## 2. 临时导入导出（不升级为持久资产）

| 入口 | 证据 | 结论 |
| --- | --- | --- |
| `GET /common/download?fileName&delete` | `common_service.py:59-82` 读 `vf_admin/download_path` | **没有任何代码向 `DOWNLOAD_PATH` 写文件**（只有 `config/env.py` 与 Dockerfile 的 mkdir）；全部导出在内存 BytesIO 中生成（`utils/excel_util.py`、`utils/common_util.py`、`utils/io_toolkit/exporters/*`、`gen_service.py:346`、`project_version_controller.py:293/338/382`）；前端无调用。按证据删除（16），`DOWNLOAD_PATH` 一并移除 |
| 用户 Excel 导入、设备/协议/工程导入、生成器 zip | `user_service.py:55-66`、`device_service.py:362`、`protocol_service.py:1102+`、`project_service.py:615`、`gen_service.py:337-356` | 内存解析，不落盘，不进入资产模块，语义不变 |
| 生成器 genCode 写源码到 `gen_path` | `gen_service.py:315-331,379-390` | 开发工具输出，非业务数据，不纳入 |

## 3. 共享组件、编辑器与生成器

- `FileUpload`、`ImageUpload`、`ImagePreview` 仅在 `F/src/main.ts:89-91` 全局注册，**没有手写业务消费者**（仿真目录也无）；消费者只有四套生成模板与测试（`tests/unit/components/AuthenticatedUpload.test.ts`、`tests/fixtures/ui-convergence/App.vue:173`）。
- 组件能力（不是消费者证据）：FileUpload 默认 `doc/docx/xls/xlsx/ppt/pptx/txt/pdf`（`FileUpload/index.vue:81-84`），ImageUpload 默认 `png/jpg/jpeg`，Editor 接受 `jpeg/jpg/png/svg`（svg 将被禁止）。值为 URL CSV 字符串，`useUploadModel.ts` 混用字符串、对象与数组。
- 生成模板（`B/module_generator/templates/vue/…`）：`v3/index.vue.jinja2` 119-122/172-178/184-187；`v3/index-tree.vue.jinja2` 109-112/166-172/178-181；`index.vue.jinja2` 124-127/186-196；`index-tree.vue.jinja2` 109-112/178-188。Python 侧 `utils/gen_util.py:92-100` 按列名后缀猜 `*image→imageUpload`、`*file→fileUpload`、`*content→editor`（需改为显式声明）；`config/constant.py:268-270`；生成配置 UI `F/src/views/tool/gen/editTable.vue:111-121`。
- wangEditor：只在 `F/src/views/project/components/VersionPreviewDialog.vue`（版本预览）与测试夹具使用，**无上传代码**，`readOnly: false` 但不保存任何内容；按规格不替换、不迁移。
- 仿真目录 `src/views/project/simulation/**`：不含上传、下载、`/profile`、头像或公告相关代码，不扩入范围。

## 4. 头像与公告数据契约

- 头像：`sys_user.avatar VARCHAR(100)` 存 `/profile/avatar/...`（不带前端前缀）。返回 `avatar` 的接口：`GET /getInfo`、`GET /system/user/list`、`GET/PUT /system/user/profile`、`GET /system/user/{id}`、`GET /system/user/authRole/{id}`。认证依赖 `LoginService.get_current_user` 从用户行构造 `CurrentUserModel`（含 avatar 字符串，不读文件）。前端 `store/modules/user.ts:120-129` 拼前缀；`userAvatar.vue:95` 裁剪器以当前头像为初始图。用户删除为软删除（`user_service.py:473` → `soft_delete`，`del_flag='2'`）。
- 公告：`sys_notice.notice_content LargeBinary`，VO/读模型均为 `bytes`，生成 TS 类型因此为 `Blob|File`，`F/src/api/system/notice.ts:2-5` 手工覆盖为 string。**列表接口返回每行完整内容**；唯一性检查比较标题、类型与内容整体相等（`notice_service.py:55-66`）。前端全仓无 `v-html`，内容只在 Quill 弹框中渲染。公告 mock 登记全部为 `missing`。

## 5. 本地只读数据盘点（不代表生产）

| 项 | 结果 |
| --- | --- |
| 用户 | 127 个；非空 avatar 1 个（`user_id=134`，`del_flag='2'` 已软删除），引用 `/profile/avatar/2026/10/19/avatar_20261019065708A840.png` —— **对应文件不存在**（`vf_admin/upload_path/avatar/2026/10/19/` 为空目录） |
| 公告 | 0 条（含 `<img` 的 0 条） |
| 生成器 | 1 张表 `sys_post`，字段 html_type 无 imageUpload/fileUpload/editor |
| 上传目录 | `B/vf_admin/upload_path` 仅 1 个文件 `upload/2026/02/10/logo图形纯净版_20260210232754A680.png`，无任何数据库引用（孤立历史文件，保留不删）；仓库根和前端目录另有空的 `vf_admin/*` 目录 |
| 模式管理 | 开发库无 `alembic_version` 表，开发态由 Atlas dev-sync 按 ORM 直接收敛（会直接执行破坏性变更），因此扩展/收缩必须有 dev-sync 前置门禁 |

## 6. 盘点出的风险与非预期事实

1. 公告 HTML 持久保存了 `/api/profile/...` 前缀 URL；迁移需识别 `/profile/` 与 `<VITE_APP_BASE_API>/profile/` 两种形式。
2. `/profile` 公开可读且允许 `html/htm`，同源交付，属于需要随切换消除的暴露面。
3. 现有 nginx 未设置 `client_max_body_size`（默认 1 MiB），容器部署下 >1 MiB 上传本就会失败；`/file-assets/` 需要单独的代理段与上限。
4. 上传响应的 `url` 使用 `request.base_url`（代理后为内部主机）；前端实际只用 `fileName`。
5. 安全头中间件以追加方式写入 CSP/Referrer-Policy，会与文件内容端点自身的 `default-src 'none'; sandbox`、`no-referrer` 形成重复头（后者被覆盖）；gzip 中间件会压缩图片/附件流。均需在实现中修正。
6. 与本任务无关但在盘点中发现：`F/.env.development:26` 存在明文 `VITE_DEEPSEEK_API_KEY`（未入库，但 `VITE_` 前缀会进入前端包）。仅报告，不在本轮修改。

## 7. 契约、生成与验证入口（锁定）

| 用途 | 命令 |
| --- | --- |
| OpenAPI 导出 / 漂移检查 | `cd ruoyi-fastapi-backend && ./venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json [--check]` |
| SDK 生成 | `cd ruoyi-fastapi-frontend && yarn api:generate`（读 `shared/openapi.json`）。不使用 `api:generate:local`（其 live 地址为 8000）；需要 live 时显式 `bash ../scripts/generate-api-types.sh --live --backend-url http://127.0.0.1:8088` |
| mock 覆盖登记 | `yarn mock:contracts`（新增端点缺登记报 `missing-registry-entry`，删除端点残留报 `orphan-registry-entry`） |
| 生成器/表单规范 | `yarn ui:standards` |
| 前端门禁 | `yarn lint:check && yarn type-check && yarn test:run`，`yarn build:prod` |
| 后端门禁 | `./venv/bin/ruff check <paths> && ./venv/bin/ruff format --check <paths>`，`./venv/bin/pytest <focused tests>`；真实 MySQL/MinIO 测试以环境变量显式开启（沿用 `RUN_REMARK_MYSQL` 先例的一次性隔离库） |
| 数据库工作流 | `./venv/bin/python scripts/db.py status / dev-sync / verify --ci`；正式环境 `deploy --revision ...` |

## 8. 待迁移清单与不变范围

待迁移（均有后续任务）：头像接口与读投影（10）、公告内容/编辑器（11）、共享组件与会话上传（9）、四套模板与生成器 Python/元数据（12）、SDK/mock/手写 API（13）、历史头像与公告图片（14）、旧入口/列/挂载收缩（16）。

不变：临时导入导出语义、wangEditor 版本预览、仿真专用页面、`gen_path` 代码生成输出、`/common/tables`。

## 9. 生产发行版待定项

`TBD-PROD-01`（生产 MinIO 发行版、镜像来源/摘要、维护与支持责任）保持未决。本地使用的 MinIO 测试镜像只作为非生产集成夹具，不代表生产选型；该待定项只阻塞任务 19（生产部署/验收），不阻塞任务 1–17。
