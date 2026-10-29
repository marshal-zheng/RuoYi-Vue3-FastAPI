# Office 校验样本

来源：[decalage2/oletools](https://github.com/decalage2/oletools) `master` 分支 `tests/test-data/`（2026-10-24 下载），按 BSD 许可（见 `OLETOOLS-LICENSE.md`）随测试分发。文件名为 `<原目录>_<原文件名>`。

`decrypted-autostart.xls` / `decrypted-autostart.xlsm` 由 `encrypted/autostart-encrypt-standardpassword.*` 用 Excel 标准只读密码（VelvetSweatshop）经 msoffcrypto 解密得到，用作真实的含 VBA 自动宏样本。

这些样本只在测试中做静态结构解析，不执行、不预览、不模拟宏。
