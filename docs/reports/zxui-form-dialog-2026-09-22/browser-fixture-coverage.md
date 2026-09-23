# C/F 独立组件及生成产物浏览器验收

## 最终范围调整（2026-09-23）

用户在收尾时明确不再要求设备、仿真、工程、监控和生成器的后续工作与验收。相关新增验证已停止；此前已完成的代码、fixture和下文历史证据保留。本文既有通过记录仅证明当时实际执行的交互，不将移出范围的模块整体标记通过，也不以其未验证分支阻塞本次收尾。

新增场景N02–N06的边界如下。它们保留在独立fixture中，但不计入本次已通过数量：

| ID | 场景 | 截止停止时的实际状态 |
| --- | --- | --- |
| N02 | VersionList新增版本 | 已准备派生fixture入口；首次选择发生依赖预构建重载，未成功打开表单，未验收 |
| N03 | VersionList编辑版本 | 已准备派生fixture入口，未执行交互，未验收 |
| N04 | VersionDetailDialog | 已准备真实组件与样例props，未执行交互，未验收 |
| N05 | monitor/job任务只读详情 | 已准备真实页面组件与内存任务行，未执行详情交互，未验收 |
| N06 | monitor/job/log失败日志只读详情 | 已准备真实页面组件与内存失败日志行，未执行详情交互，未验收 |

fixture中可选`open`调用已改为方法可选调用，修复两处TS2722。随后完整`vue-tsc --noEmit`退出0，`/tmp/zxui-fixture-final-typecheck.log`为空；这是类型检查证据，不是上述分支运行通过证据。收到最后范围调整后，仅更新证据文档，未继续修改代码或执行浏览器验证。

## 已执行的历史证据

执行：2026-09-23，Chrome 扩展浏览器，页面 `http://127.0.0.1:4182/`，真实业务 SFC + 已安装公开 ZXUI + 公开 deployment Host/Provider。页面位于 `ruoyi-fastapi-frontend/tests/fixtures/ui-convergence`，没有加入产品路由，没有登录业务，也没有提交真实业务数据。所有接口通过测试专用内存 adapter；图片为本地 fixture SVG。

本表覆盖路线清单的 **F01–F12、C01–C04 的 17 个文件**：对应迁移前 **30 个 input、7 个原生 dialog**。C04 分为两个组件实例。这里的“通过”只表示表中具体交互在这些样例 props/内存数据下通过，不能登记为生产页面/真实 API 验收，也不代表每组件所有主题排列均验过。

## 实际组件交互

| ID | 真实组件 | 实际执行与观察 | 结果边界 |
| --- | --- | --- | --- |
| F01 | DagMatrixView | 搜索不存在节点，显示0/1；恢复Fixture显示1/1；点编辑，修改节点名称与描述，点取消关闭 | 3个迁移输入；真实矩阵节点弹框 |
| F02 | DagMatrixViewSimple | 相同搜索过滤闭环；编辑名称/描述、取消关闭 | 3个迁移输入；真实精简矩阵弹框 |
| F03 | DagSearchInput | 输入needle；页面收到`search: "needle"`事件 | prefix搜索图标/防抖输出 |
| F04 | DeviceClazzDialog | 公开open新增分类；输入分类名称/描述；Cancel关闭 | 未保存分类 |
| F05 | Device ExportDialog | modelValue打开导出；默认Fixture project_导出；文件名改fixture-export；取消关闭 | 未下载；没有把该组件等同设备页真实导出 |
| F06 | Device NodeEditDrawer | modelValue打开；名称改Node edited；另外5字段显示fixture数据并保持disabled；取消关闭 | 6个迁移输入；ElDrawer本身不在原生dialog替换计数 |
| F07 | Project ExportDialog | modelValue打开；文件名改project-fixture-export；取消关闭 | 未下载；与VersionExportDialog区分 |
| F08 | ProjectEditDialog | 公开open；输入项目名称及描述；Cancel关闭 | 未保存工程 |
| F09 | ProtocolConfigDrawer | 公开open传CAN端口；端口名称只读；输入1Mbps和协议描述；Cancel关闭 | 3个迁移输入通过；内嵌VXE边界见下文 |
| F10 | ThemeValidation | 用户名/密码输入；密码DOM类型为password；点击组件自身暗色按钮，Host提交dark variant | 不采用组件文字中“328+变量已覆盖”作为证据 |
| F11 | ImageUpload | 已有本地SVG缩略图；点击真实预览图标；预览dialog内image.complete且naturalWidth>0；关闭 | 不上传文件 |
| F12 | RightToolbar | columns样例+transfer模式，点组件自身显隐列按钮；真实弹框显示两侧Fixture column/Fixture extra；关闭 | 只验证显隐列弹框入口/展示，非生产job/log同一路径 |
| C01 | CategoryFormDialog | 公开open；填写分类名称/备注；Cancel关闭 | 当前生产route仍未证明 |
| C02 | DeviceCloneDialog | 公开open传Fixture device；默认新名Fixture device_副本；修改名称、Cancel关闭 | 未创建克隆 |
| C03 | ProtocolFormDrawer | 公开open；填写协议名称/描述；Cancel关闭 | 未保存协议；全协议模板由B27另验 |
| C04a | 旧ProjectDlg | 公开open；工程描述输入Legacy fixture；Cancel关闭 | 与当前project页面不同组件 |
| C04b | 旧ProjectList | 有高度flex宿主，内存列表Total1；点真实详情按钮；描述列表显示工程1/Fixture description；关闭 | 初始fixture宿主高度0导致不可点击，补齐宿主后重验通过；未修改业务组件 |

F01–F10及C01–C04a首次检查使用前一候选bd267；库边界修复后安装085dfd并隔离缓存。随后在085dfd实际复验F01/F02搜索、F09三输入、C04b详情、G01全交互和容器/密度。前后候选证据保留分界，不把旧候选检查伪装为全部新包复验。

## 完整生成 SFC：G01

`prepare.mjs`调用真实`makeUpHtml + makeUpJs`产生三字段对话框：required普通text（含https:// prepend和.com append）、原生number、整行textarea。浏览器看到正确三个原生类型及初值。

1. 打开生成表单，直接OK，显示“请输入名称”，弹框保持打开。
2. 填写名称Generated browser、number 42、说明Browser generated notes，OK回传：`{"name":"Generated browser","quantityText":"42","notes":"Browser generated notes"}`。
3. 提交后dialog数量为0；重开得到`["", "", "initial notes"]`；Cancel关闭。
4. 表单grid实测两列`409.444px 409.444px`，textarea所在form item的grid-column为`1 / -1`。

另有真实公开组件JSDOM回归直接调用保留的原生FormInstance.validate/resetFields，覆盖required拒绝、合法通过、reset恢复初值、提交回传及关闭。2026-09-23 focused命令15/15通过，日志`fixture-focused-tests.log`。浏览器结果与JSDOM结果分开记录。

## 容器响应式与密度

使用真实`FormGrid`和同一`useFormDialog({columns:3})`输出的form/layout props，仅改变外部宿主宽度：

| 实际容器宽度 | computed grid-template-columns | scrollWidth | 结果 |
| ---: | --- | ---: | --- |
| 1100 | 353.333px 353.333px 353.333px | 1100 | 3列；整行项宽1100 |
| 650 | 315px 315px | 650 | 2列；第3项折到下一行，整行项宽650 |
| 320 | 320px | 320 | 1列；全部依次排列，整行项宽320 |

长中文标签换行，未溢出320px容器。浏览器viewport没有被本证据改小，**不据此宣称完整业务页面移动视口验收完成**。

在dark/default主题，密度选择经业务统一偏好入口提交：compact/default/comfortable对应input实际高度约28/32/36px，form-item margin-bottom为16/18/20px。切回light/default，Host提交light variant，input高度约32px，wrapper背景为`color(srgb 0.991 0.9928 0.9964)`。

## 限制与诊断

- F09内嵌VXE可挂载，协议输入可操作；仍有`[vxe table v4.17.15]`空文本error/warn。测试沿用真实`setupVXETable`；其i18n函数直接`zhCN[key]`无法提供点路径诊断文本。本记录不把VXE全编辑/主题状态标通过。字典fixture起初用旧envelope格式，已改当前`{items}`契约后重验；字典map警告不再出现。
- 业务root矩阵曾观察到`dataset.vxeUiTheme=light`而ZX variant随light/dark变化。该属性本身不是computed外观失败证明；VXE主题边界需要主线程B27单独证据，不扩大为本轮已修复事项。
- 独立端口最初误用默认Vite缓存，共享业务`.vite/deps`，导致业务优化依赖失效。已经改为`node_modules/.vite/ui-convergence`，停止旧4182并独立重启；主线程重启80恢复其缓存。最终配置不会共享优化产物。
- 本表无生产路由不可达问题的“绕过通过”：C类生产route仍待真实菜单证据，F类仍无消费/相应分支，仅其真实组件fixture交互已完成。

## 静态与可重复运行检查

`prepare.mjs`从干净派生入口成功重建资产/SFC；最终fixture及runtime测试文件ESLint为0 errors/0 warnings。严格门禁扫描496文件0违规；聚焦三文件15项测试通过。未重跑全项目构建，也未将旧候选构建结果用于新候选结论。已安装ZXUI与085dfd候选tarball的1648个文件逐字节核对0差异，见business-theme-deployment.json。

## 追加：真实窄视口 N01 用户弹框

2026-09-23追加有界验收，使用`src/views/system/user/components/UserFormDialog.vue`真实组件；独立页仅增加N01场景与内存部门/岗位/角色样例。不登录，不创建用户，不替代B03真实业务页面及API验收。

Chrome支持viewport覆盖，但当前浏览器缩放导致API宽度不等于CSS像素。最初请求640×700，读取到innerWidth711/innerHeight777；因此校准请求576×630后，实际`window.innerWidth=640, innerHeight=700, documentElement.clientWidth=640`。再请求351×567后，实际`innerWidth=390, innerHeight=630`。所有下述尺寸按页面实际DOM读数，不按请求参数推断。

| 实际视口 | 实际`.el-dialog`面板 | FormGrid实测 | 整行备注 |
| --- | --- | --- | --- |
| 1920（恢复后对照） | 宽880 | 408.889px 408.889px，两列 | grid-column=1/-1 |
| 640×700 | x16.007，宽607.986，y23.993，高651.997 | 573.785px，单列 | 宽573.785，grid-column=1/-1 |
| 390×630 | x16.007，宽357.986，right373.993，y23.993，高581.997，bottom605.990 | 323.785px，单列 | 宽323.785，grid-column=1/-1 |

- 640下body.clientHeight524、scrollHeight604。填写底部备注时body.scrollTop变为80，焦点保持在备注；footer底部674.879，小于视口700。
- 390下body.clientHeight454、scrollHeight604，面板和页脚均在视口内，footer底部604.879，小于视口630。grid.scrollWidth324是323.785布局宽度的取整，无横向内容溢出。
- 390下填写昵称“390 fixture”，按Tab，焦点进入归属部门combobox，仍在dialog中，同时body滚回顶部。实际截图可见单列字段、内部滚动条以及固定可见的Cancel/创建页脚。
- 点击Cancel后dialog数量为0，document.activeElement为文本“打开当前组件”的BUTTON。最后执行viewport.reset，读取innerWidth1920/innerHeight1013，未把浏览器留在小尺寸。
- 该证据补齐**真实UserFormDialog组件在fixture中的窄视口表现**；依旧不把整个业务shell、B01–B27全部页面或所有弹框宣称移动端通过。

同轮只读复核IconsDialog的`title="选择图标"`与`#headerLeft`修复：与ZXUI公开Dialog插槽契约匹配，搜索字段不再放入未实现的header插槽；未发现该变更的P0/P1。该复核不重复主线程真实B21页面截图证据。
