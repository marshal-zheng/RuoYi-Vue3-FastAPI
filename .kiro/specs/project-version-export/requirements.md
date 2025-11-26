# 需求文档

## 简介

本文档规定了在 RuoYi-Vue3-FastAPI 系统中实现工程版本导出功能的需求。该功能使用户能够基于预定义模板将工程版本数据（包括版本元数据和拓扑信息）导出为 Word 文档格式。此功能对于工程管理工作流程中的文档编制、报告和归档至关重要。

## 术语表

- **系统（System）**: RuoYi-Vue3-FastAPI 工程管理应用程序
- **用户（User）**: 具有访问工程版本适当权限的已认证用户
- **工程版本（Project Version）**: 包含元数据和拓扑数据的工程特定版本
- **拓扑数据（Topology Data）**: 表示工程设备网络结构的 JSON 格式数据
- **导出模板（Export Template）**: 位于 FAQ 目录中的 Word 文档模板（demo.doc）
- **Word 文档（Word Document）**: Microsoft Word 格式文件（.doc 或 .docx）
- **后端 API（Backend API）**: 基于 FastAPI 的服务器应用程序
- **前端 UI（Frontend UI）**: 基于 Vue 3 的客户端应用程序

## 需求

### 需求 1

**用户故事：** 作为工程管理员，我想将工程版本导出为 Word 文档，以便与需要离线访问的利益相关者共享工程文档。

#### 验收标准

1. WHEN 用户点击版本的导出按钮 THEN 系统 SHALL 生成包含版本数据的 Word 文档
2. WHEN 导出过程成功完成 THEN 系统 SHALL 启动文件下载到用户的浏览器
3. WHEN 导出过程失败 THEN 系统 SHALL 向用户显示错误消息
4. WHEN 生成导出文档 THEN 系统 SHALL 使用接口控制文件模板格式
5. WHEN 生成 Word 文档 THEN 系统 SHALL 包含标题、范围、引用文件、术语定义、信息交联关系、通信要求和附录等章节

### 需求 2

**用户故事：** 作为系统管理员，我想要导出功能需要适当的权限，以便只有授权用户才能导出敏感的工程数据。

#### 验收标准

1. WHEN 用户尝试导出版本 THEN 系统 SHALL 验证用户具有 'project:version:export' 权限
2. WHEN 用户缺少所需权限 THEN 系统 SHALL 拒绝导出请求并返回授权错误
3. WHEN 在 UI 中渲染导出按钮 THEN 系统 SHALL 在用户缺少 'project:version:export' 权限时隐藏该按钮

### 需求 3

**用户故事：** 作为开发人员，我想要导出包含拓扑数据，以便导出的文档包含完整的工程信息。

#### 验收标准

1. WHEN 导出具有拓扑数据的版本 THEN 系统 SHALL 从数据库检索拓扑数据
2. WHEN 版本存在拓扑数据 THEN 系统 SHALL 在导出的文档中包含拓扑信息
3. WHEN 版本不存在拓扑数据 THEN 系统 SHALL 在文档中包含占位符或空白部分
4. WHEN 包含拓扑数据 THEN 系统 SHALL 以人类可读的方式格式化 JSON 数据

### 需求 4

**用户故事：** 作为用户，我想要导出的文件名具有描述性，以便我可以在文件系统中轻松识别导出的文档。

#### 验收标准

1. WHEN 系统生成导出文件 THEN 系统 SHALL 使用模式"工程版本_{version_number}_{timestamp}.docx"命名文件
2. WHEN 生成时间戳 THEN 系统 SHALL 使用格式"YYYYMMDD_HHMMSS"
3. WHEN 版本号包含特殊字符 THEN 系统 SHALL 清理文件名以确保文件系统兼容性

### 需求 5

**用户故事：** 作为系统操作员，我想要记录导出操作，以便我可以审计文档生成活动。

#### 验收标准

1. WHEN 用户启动导出 THEN 系统 SHALL 记录操作，包括用户名、版本 ID 和时间戳
2. WHEN 导出成功 THEN 系统 SHALL 记录成功信息，包括生成的文件名
3. WHEN 导出失败 THEN 系统 SHALL 记录错误详细信息，包括异常消息

### 需求 6

**用户故事：** 作为开发人员，我想要导出正确处理模板，以便生成的文档保持适当的格式。

#### 验收标准

1. WHEN 系统处理模板 THEN 系统 SHALL 保留原始模板格式和样式
2. WHEN 填充模板字段 THEN 系统 SHALL 用实际版本数据替换占位符文本
3. WHEN 模板文件缺失 THEN 系统 SHALL 返回错误，指示无法找到模板
4. WHEN 模板文件损坏 THEN 系统 SHALL 返回错误，指示无法处理模板

### 需求 7

**用户故事：** 作为用户，我想要导出过程提供反馈，以便我知道操作正在进行以及何时完成。

#### 验收标准

1. WHEN 用户点击导出按钮 THEN 系统 SHALL 显示加载指示器
2. WHEN 导出成功完成 THEN 系统 SHALL 隐藏加载指示器并显示成功消息
3. WHEN 导出失败 THEN 系统 SHALL 隐藏加载指示器并显示带有详细信息的错误消息
4. WHEN 导出时间超过 30 秒 THEN 系统 SHALL 超时并显示适当的错误消息

### 需求 8

**用户故事：** 作为开发人员，我想要后端使用 Python 库进行 Word 文档生成，以便实现可维护和可靠。

#### 验收标准

1. WHEN 实现导出功能 THEN 系统 SHALL 使用 python-docx 库进行文档操作
2. WHEN python-docx 库未安装 THEN 系统 SHALL 将其包含在 requirements.txt 文件中
3. WHEN 处理文档 THEN 系统 SHALL 适当处理 .doc 和 .docx 格式

### 需求 9

**用户故事：** 作为用户，我想要批量导出多个版本，以便我可以高效地为多个版本生成文档。

#### 验收标准

1. WHEN 选择多个版本 THEN 系统 SHALL 启用批量导出选项
2. WHEN 启动批量导出 THEN 系统 SHALL 生成包含每个版本单独 Word 文档的 ZIP 文件
3. WHEN 生成 ZIP 文件 THEN 系统 SHALL 使用模式"工程版本批量导出_{timestamp}.zip"命名
4. WHEN 批量模式下任何版本导出失败 THEN 系统 SHALL 继续处理剩余版本并报告哪些版本失败

### 需求 10

**用户故事：** 作为系统架构师，我想要导出功能遵循现有的分层架构，以便代码库保持一致和可维护。

#### 验收标准

1. WHEN 实现导出功能 THEN 系统 SHALL 在 project_version_controller 模块中创建导出端点
2. WHEN 实现业务逻辑 THEN 系统 SHALL 向 project_version_service 模块添加导出方法
3. WHEN 实现数据访问 THEN 系统 SHALL 使用现有的 DAO 方法或根据需要向 project_version_dao 添加新方法
4. WHEN 实现前端 THEN 系统 SHALL 向 project/version.js API 模块添加导出 API 调用
