# Message 真实业务视觉与交互验收

用户已授权 computer use。本轮在本机开发服务中登录 `admin`，主验收页面为 `/system/user`，使用本地直连 ZXUI 源码。
截图来自真实业务的 Vue、ConfigProvider、Theme Host、反馈发送端与 Message 宿主，没有替换组件实现。

## 验收方法与范围

页面加入临时验证入口，通过真实 `showMessage` 接口触发代表性内容。触发消息、切换主题/密度、操作按钮、键盘关闭和触控使用浏览器的真实鼠标、键盘或触控输入。
临时消息中的“导出完成”“重试”等为验证内容，不代表执行了业务导出或服务恢复。没有执行用户、角色等业务数据的增删改。

| 维度 | 覆盖 |
| --- | --- |
| 主题 | 默认、苔绿、森绿、雾蓝、琥珀、墨青、钢蓝、科技蓝、工厂蓝 |
| 明暗 | light / dark |
| 密度 | compact / default / comfortable |
| 内容 | success、warning、error、两行 default/action Slot、标准异步操作按钮 |
| 主视口 | 1440 × 1000，DPR 1 |
| 额外视口 | 360px 窄窗口；360px、DPR 2 的触控模拟；500 × 773、DPR 2 原生窗口 |

共 54 组主题/明暗/密度组合，每组五类消息。主题切换采用业务现有控件，等待提交完成再读取实际模式与颜色。
消息保持显示，检查主题切换及密度变化时的颜色、尺寸和堆叠位置。额外检查长内容、异步重复点击/失败、焦点、关闭和原生计时。
原始 54 组矩阵测量和窄窗口、键盘检查位于已登录用户管理页。部分热更新后的补充截图在登录页复查同一根 Provider；最终交付的墨青六种组合已重新登录用户页保存。原生窗口补充截图位于业务登录页。

## 发现与修正

三个问题均在 ZXUI 中修正：

1. **多行插槽的首行对齐。** 原先图标、操作、关闭按整块正文居中，两行内容时偏离首行 12px。结构样式统一首行尺寸，使正文首行、图标、标准操作和关闭按钮对齐；触控按 44px 交互行处理。
2. **触控操作宽度。** “重试”只有 28px 宽，原先只保障高度。触控样式增加 44px 最小宽度，操作和关闭实测均为 44 × 44px。
3. **程序化关闭标签的语言归属。** API 宿主在 Provider 组件祖先链外渲染，原先使用英文关闭标签。反馈 facade 在调用时捕获所属 Provider 的语言标签；新增 `closeLabel` 支持 Provider、模板和单次调用覆盖。业务中已实测为中文。

没有新增业务视觉覆盖或另一套消息管理器，没有修改生成的主题资产。

## 结果

- 主矩阵的 270 个消息画面均在视口内，正文没有横向溢出。图标中心与首行中心偏差最大为 0px。
- 实际浏览器计算色的正文/背景对比度最低约 10.36:1，状态图标约 7.74:1，关闭前景约 6.11:1；这里针对默认 surface 外观与本轮变体，不代表任意自定义样式的认证。
- 墨青单行消息实测：紧凑 40px、默认 44px、宽松 48px。两行 Slot 分别 64 / 68 / 72px，正文高度随内容增加。其他主题保留自己的密度种子。
- 明暗模式的前景/背景实际变化，普通文本、富内容与操作均可读。图标状态由颜色与图形共同表达，关闭 glyph 与文本比例协调。
- 360px 窄窗口的长正文完整换行，操作移至下一行，消息左右保持 16px 视口边距。
- Slot 操作真实点击后响应并关闭。标准操作双击只执行一次，执行期间 disabled / aria-busy 生效，成功关闭。
- 人为拒绝操作回调后，消息保留且操作恢复可用，重试成功后关闭。预期拒绝产生一次 `QA expected action rejection`，没有其他页面脚本错误。
- Tab 可到达操作与关闭，焦点环可见，Enter 可关闭。中文关闭标签在最后修正后重新验证。
- 原生计时消息在 hover 持续 1.8 秒后仍显示，移开鼠标后按计时关闭。
- 触控 tap 响应一次回调，最后修正后操作和关闭均为 44 × 44px。

默认外观在本轮范围内协调：紧凑与宽松区别明确，状态图标、富内容、操作与关闭形成统一布局。此次发现的首行对齐和触控宽度问题已修正。
没有把浏览器验证扩成完整辅助技术认证；API 原生 live region、窗口失焦暂停和其他 display/高对比度轴保持此前边界。

## 截图与记录

图片均为真实页面截图。矩阵只进行无损裁切拼接，未重绘或美化内容。

- [墨青明暗预览](assets/message-visual-2026-10-13/message-dark-light.png)
- [墨青完整密度矩阵](assets/message-visual-2026-10-13/rocket-moss-matrix.png)
- [默认主题矩阵](assets/message-visual-2026-10-13/default-matrix.png)
- [科技蓝矩阵](assets/message-visual-2026-10-13/tech-blue-matrix.png)
- [苔绿矩阵](assets/message-visual-2026-10-13/defense-green-matrix.png)
- [森绿矩阵](assets/message-visual-2026-10-13/army-pine-matrix.png)
- [雾蓝矩阵](assets/message-visual-2026-10-13/air-gray-matrix.png)
- [琥珀矩阵](assets/message-visual-2026-10-13/pap-olive-matrix.png)
- [钢蓝矩阵](assets/message-visual-2026-10-13/factory-blue-matrix.png)
- [工厂蓝矩阵](assets/message-visual-2026-10-13/industrial-blue-matrix.png)
- [窄窗口长正文](assets/message-visual-2026-10-13/narrow-long.png)
- [键盘焦点](assets/message-visual-2026-10-13/keyboard-focus.png)
- [触控尺寸](assets/message-visual-2026-10-13/touch-message.png)
- [原生窗口补充](assets/message-visual-2026-10-13/native-window.png)
- [测量记录](assets/message-visual-2026-10-13/measurements.json)、[统计](assets/message-visual-2026-10-13/summary.json)

最后的两个补充修正不改变桌面表面与尺寸。墨青六种组合、中文关闭标签和触控目标在补充修正后重新检查；其他矩阵的几何与色彩结果仍适用。

## 源码验证与清理

ZXUI 既有 feedback/merge 三个文件的 13 项检查通过；变更 TS 模块定向诊断为 0。结构 CSS 经 PostCSS 解析，相关 `git diff --check` 通过。
未新增测试用例，未运行 lint/build，未发 npm。
验证浏览器会话已关闭，临时入口只存在于该会话 DOM，没有写入业务页面。前端 80 和后端 8088 服务仍正常响应。

实现背景见 [Message 展示与业务接入评估](2026-10-13-zxui-message-review.md)。

后续用户指出两行富内容与操作的层级仍显杂乱。此报告记录的是前一轮对齐与可读性检查；最终增加可选描述契约及固定首行/左说明右操作布局，见 [Message 富内容层级复查](2026-10-13-message-rich-content-refinement.md)。
