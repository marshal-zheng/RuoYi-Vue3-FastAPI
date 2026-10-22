# 备注 A 协议验证记录

本记录覆盖共享契约、Python 接纳边界及独立资源探针。验证工作区为项目本地 `.worktrees/generic-remark-rich-text`；没有修改源工作区，没有使用 computer use，也没有将单元测试标为真实业务界面验收。

## 环境与入口

- Python 3.13.12、Pydantic 2.11.7、Pydantic Core 2.33.2，macOS 15.5 ARM64。
- 冻结入口：`ruoyi-fastapi-backend/common/remark_document_v1.py`；完整 Document v2 与 `null` 为唯一业务值。
- Pydantic 入口：`module_admin/entity/vo/remark_vo.py`；通过迭代预检后解析递归类型，保留必须存在的 `null` 属性。
- 共享文件：`shared/remarks/remark-a-v1/manifest.json`，102 项：25 个合法文档、73 个非法输入、4 个纯文本转换样例。manifest SHA-256：`353c9dafb2f2735f7c7466ab3b4a9773e4f9fdf93c32068cd4c8f3a85f49b8ec`。

共享样例的语义期望由固定文件给出，未在测试中调用被测转换器生成期望结果。较大的资源样例采用紧凑 JSON；fixture 文件末尾的换行不属于输入文档大小。

## 覆盖与结果

| 边界 | 证据 | 结果 |
| --- | --- | --- |
| Document v2 外壳、精确 meta、空资源、未知字段 | shared valid/invalid vectors | Python 通过 |
| 段落、软换行、嵌套列表与起始编号、标记与链接 | shared vectors，固定 literal/display 期望 | Python 通过 |
| 唯一块 ID、未知节点/标记、未知或缺失属性、错误属性类型 | shared invalid vectors | Python 拒绝；对象/数组类型的 node.type/mark.type 已验证为安全字段错误 |
| 规范化：相邻同标记 text 合并、标记顺序、空可选数组省略 | shared canonical vectors，Pydantic 序列化探针 | 通过；必需的 null 属性保留 |
| 唯一空值规则 | null、单空段落、多空段落、空白、hardBreak vectors | 通过；不 trim 空白，不将多空段落归一化为 null |
| 字符预算 | 5,000 / 5,001 个 astral 码点，正文加结构 LF 探针 | 接纳上限，拒绝上限加一 |
| UTF-8 JSON 字节预算 | 紧凑文档恰好 262,144 / 262,145 bytes；原输入与规范文档分别检查 | 接纳上限，拒绝上限加一；原输入不能借合并 text 绕过预算 |
| 节点预算 | 含 doc、paragraph 的 2,000 / 2,001 节点；可合并 text 探针 | 接纳上限，拒绝上限加一；在规范化前计数 |
| 列表层级 | 3 / 4 层共享向量 | 接纳三层，拒绝四层 |
| 树深度与原始容器深度 | 受控阈值计数探针、32/33 层原始对象、1,000 层 Pydantic 输入 | 防护先于递归模型生效，无未处理的 RecursionError |
| href 预算 | 2,048 / 2,049 码点；Unicode href 单独探针 | 按码点计数，接纳上限，拒绝上限加一 |
| 链接解析 | 明确协议、大小写、编码 Unicode、IDN、emoji 域名、IPv4/IPv6；非法编码、UTF-8、主机、凭据、端口、空白与协议 | Python 通过固定正反例；保留原 href，不通过 URL 重写改变权威值 |
| 只读派生值与 API 空值/遗漏 | `test_remark_api.py`，read projection 伪造输入与再次解析探针 | 写入拒绝 remarkText；读取始终从文档重算；显式 null 与遗漏可区分 |
| 纯文本与 Excel | 4 个确定性转换样例；公式样式文字的真实 xlsx 单元格类型 | 通过；HTML/JSON 外观保持字面文本，Excel 单元格保持文字 |
| 错误正文保密 | 非法链接含正文 sentinel 的错误探针 | codec 错误不包含正文或 href |

A 的合法父子关系与三层列表约束使合法文档最多达到 9 层节点深度；深层 text 携带 link 时最多达到 22 层对象/数组深度。设计中的 12/32 是额外的前置资源防护，不能虚构“合法 A 文档恰好 12/32 层”的通过证据。测试分别以实际可达深度确认计数，并用非法深层输入确认固定防护先于语法及 Pydantic 递归解析。

## 链接方案依据

`urllib.parse.unquote` 默认以替换字符处理无效 UTF-8，且 `urlsplit` 本身不负责完整验证。备注入口额外拒绝不完整 `%HH`，采用严格 UTF-8 解码，再检查空白、C0、DEL 与反斜杠。HTTP(S) 的 authority 必须显式存在且无凭据、`@` 或百分号。mailto/tel 必须有非空目标。链接原值保留。

主机、IDNA、IPv4 与 IPv6 由已有依赖 `pydantic_core.Url` 校验。该公开类型使用 Rust `url` crate，后者实现 WHATWG URL Standard；不增加依赖，也不在备注代码中维护另一套 IPv4 或 IDNA 解析算法。这里直接采用现有机制，备注只保留自己的安全策略与长度预算。依据：[Pydantic Core Url 官方类型说明](https://github.com/pydantic/pydantic-core/blob/main/python/pydantic_core/_pydantic_core.pyi)、[Pydantic 官方迁移说明](https://github.com/pydantic/pydantic/blob/main/docs/migration.md)、[Rust url 官方说明](https://docs.rs/crate/url/latest)、[Python urllib.parse 官方文档](https://docs.python.org/3/library/urllib.parse.html)。

JavaScript `JSON.parse` 无法保留 JSON 数字 `1` 与 `1.0` 的词法区别，`Number.isInteger` 对两者均为真。已批准设计要求 Python `StrictInt`，因此 Python-only 测试保留对显式 `1.0` 的拒绝；共享非整数负例使用 `1.5`。真实编辑器由 `JSON.stringify` 序列化整数为 `1`。这是解析表示的边界，不能宣称 JavaScript 可以检出输入文件的 `1.0` 词法形式。

## 可复现命令

在 `ruoyi-fastapi-backend` 中运行：

```bash
./venv/bin/python -m pytest tests/unit/common/ -n 0 --no-cov --tb=short
./venv/bin/ruff check common/remark_document_v1.py module_admin/entity/vo/remark_vo.py tests/unit/common/
./venv/bin/ruff format --check common/remark_document_v1.py module_admin/entity/vo/remark_vo.py tests/unit/common/
```

2026-10-22 协议子任务截点结果：124 passed；Ruff check 通过；6 个文件 format check 通过。后续加入嵌套投影与 OpenAPI 边界后，`tests/unit/common/` 共 159 项，已在 431 项后端相关测试组中再次全部通过，见 [后端 API 验证](backend-api-verification.md)。此次先用新增向量复现了旧实现的链接错误接纳，以及对象/数组类型造成的 TypeError，再修复并重新运行。完整临时日志为 `/tmp/remark-contract-final.log`；失败复现日志为 `/tmp/remark-contract-red.log`、`/tmp/remark-contract-url-red.log`、`/tmp/remark-contract-json-type-red.log`。

仓库级 `backend-conventions/scripts/validate.sh --changed` 另执行过：guardrails 通过，但整个实现工作区的 Ruff lint/format 当时仍有其他文件的错误；不能用本记录的六文件检查替代全工作区最终门禁。其临时日志为 `/tmp/remark-backend-conventions.log`。

## 证据边界

- 以上为 Python 单元/集成探针与静态规范核对，不是浏览器、数据库或七入口真实业务验收。
- ZXUI 端必须镜像同一组 102 项固定文件并运行公开校验器测试；最终运行结果由主代理统一记录。本记录的 Python 结果不代替该结果。
- 不承诺穷尽所有 Unicode 字符及未来 URL 实现版本；升级 Pydantic Core 或 ZXUI 时仍须重新执行同一组样例。
- 真实 UI、权限、事务、MySQL 升级、PostgreSQL 与完整生成器验收由总验收记录说明，本记录没有将这些未执行项目标为通过。
