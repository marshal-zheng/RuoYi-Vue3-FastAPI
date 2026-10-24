# ZXUI 字体资源与按需装配后续交付

仅修改 RuoYi 与 ZXUI 根仓库，未修改 steamer-front 或独立 feature 包，未提交、推送、发布。完整交付、独立审查和原始证据集中在 [ZXUI 后续说明](/Users/hqz/Downloads/element-plus/docs/specs/http-vue-query/font-chunk-followup.md)。

RuoYi 入口改用公开配置插件和成熟组件 resolver，保留实际服务、图标名称、主题/反馈上下文与样式顺序。动态生成器显式绑定组件对象；VXE 在真实协议模板及表格 owner 的 setup 同步装配，保持 app 隔离，修复既有嵌套 locale 读取。运行时 ZXUI 引用迁往公共 leaf/hooks；仿真专属源码不迁移。图标依赖通过 Yarn 官方 dedupe 复用兼容的既有 2.3.2，未添加 force alias。

源码直连 main JS 的逐资源 gzip9 从 1,378,665 降到 943,375 字节（-31.573%）；收益主要是将组件成本交还实际路由，不能当成全站总 JS 同幅下降。九套主题 manifest 和实际图标 catalog 仍有同步成本。ZXUI 提供通用公共入口，业务领域规则仍留在 RuoYi。

最终主包使用 `vendor/zxio-zxui-3.0.0-next.0-font-chunk.final3.20261017.tgz`；SHA256 `46412845c5884e5ed1fcffd8c5f336e3260ccf0fee9df6780e9b5a288f01e455`。compiler 沿用前轮最终包，没有复用旧 file 缓存名。全部 130 文件 / 1226 tests、UI standards 23 tests、lint/type 通过；源码与 packed 两模式生产构建通过。完整检查时序与 hash 在 ZXUI 证据目录。

通过 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 实际验证：生成器下拉、单选、日期、293 图标搜索选择；LAN 报文 VXE 字典编辑/关闭；取消草稿再打开；深色紧凑 portal、行高 48→44；用户岗位/角色共享下拉。无业务写入，认证 refresh/logout 单独记录，0 pageerror/框架 warning，主题恢复默认。

最终生产文档的七页 SSR→hydration 全通过，正常生产偏好修改并重载保持一致，均无 warning/pageerror。验收中修复了 Docs 四字段偏好误入严格两字段 receipt，以及 Select 数组仅 beforeMount 初始化导致的 SSR ID 错位；库保持通用，函数 loader 语义保留。最新源码再次验证岗位 4 项、角色 1 项选择后取消，无业务写入。当前 Docs 回归 47 项、独立 7 项与 Select 定向 35 项通过。

根全库类型六套通过，本轮 87 个生产/测试文件 lint 通过；全库 lint 剩下并发 Dashboard 三份证据 JSON 的格式错误，未修改他人证据。字体缺失属于独立 Drive 的实际资源及公开部署合同，普通源码 Select 未发缺失字体请求，Drive 页自然请求 1 个 Roboto 并失败；19 声明不代表 19 个真实请求。源码 dev 的 HTTP200 实为 HTML fallback，生产产物无该字体引用。未以假字体、私有 alias 或告警过滤掩盖它。

日常启动仍依根 AGENTS.md 使用 Docker MySQL、Redis、8088 后端与 80 前端；不使用 scripts/start.sh 或 Homebrew MySQL。未把浏览器验收结果延伸为仿真业务、全主题 token 或性能基准测试。
