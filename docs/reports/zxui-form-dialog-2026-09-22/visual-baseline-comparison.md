# 历史基线与终态的可比较范围

基线：`../zxui-theme-audit-2026-09-22/dialog-current.png`、`dialog-dom.json`；对应审计 `../2026-09-22-zxui-theme-adoption-audit.md` 明确真实工厂蓝深色添加用户。终态：`browser/matrix-industrial-blue-dark.png/json`。

本人实际查看基线截图并读取两份DOM记录。共同页面为用户管理→添加用户，共同主题是industrial-blue/dark。

| 项目 | 基线 | 终态 |
| --- | --- | --- |
| Dialog宽×高 | 440×600 | 880×482 |
| Dialog背景 | color(srgb 0.0873666 0.181576 0.308571) | 相同 |
| 11个字段label文字色 | color(srgb 0.9165 0.9512 1) | 相同 |
| 状态radio数量 | 0 | 2（0/1） |
| 终态布局 | 原窄双列，截图有截断 | 406px×2，横gap20px |
| 保存图像像素 | 1124×1000 | 1280×720 |
| DOM记录viewport | 未记录 | 1280×720 |

因此T9.4实际非仿真页面的删除前后颜色对比有证据：删除竞争来源后，主题拥有的背景和标签色保持一致，数据/布局同时修复，未声称仿真通过。该结论不依赖不同viewport进行几何差值推断。

R9.AC3明确要求同页面/同主题/同视口的改前后配对。旧图像像素不同、DOM没有viewport字段；不能证明其与新图同视口，不将此项判全覆盖。旧login-before/login-after-dark图片像素同为1124×1000，但属于此前局部登录修复（审计明确当时保留EP dark和局部autofill），不能用来冒充本spec删除重复主题来源的最终同视口证据。
