# 测试指南

## 快速开始

### 运行所有测试
```bash
./scripts/run_tests.sh
```

### 运行业务关键测试
```bash
pytest tests/integration/test_business_critical.py -v
```

### 运行特定测试类
```bash
# 密码安全测试
pytest tests/integration/test_business_critical.py::TestPasswordSecurity -v

# 项目业务逻辑测试
pytest tests/integration/test_business_critical.py::TestProjectBusinessLogic -v

# 数据完整性测试
pytest tests/integration/test_business_critical.py::TestDataIntegrity -v
```

### 运行集成测试
```bash
# 所有集成测试
pytest tests/integration/ -v

# 特定模块
pytest tests/integration/test_user_management.py -v
pytest tests/integration/test_project_integration.py -v
```

### 查看覆盖率报告
```bash
# 生成HTML报告
pytest tests/integration/ --cov=module_admin --cov=utils --cov-report=html

# 打开报告
open tests/coverage/html/index.html  # macOS
xdg-open tests/coverage/html/index.html  # Linux
```

## 测试结构

```
tests/
├── conftest.py                    # 全局测试配置
├── integration/                   # 集成测试
│   ├── conftest.py               # 集成测试配置
│   ├── test_business_critical.py # 业务关键测试 ⭐
│   ├── test_core_modules.py      # 核心模块测试
│   ├── test_user_management.py   # 用户管理测试
│   ├── test_role_management.py   # 角色管理测试
│   ├── test_menu_management.py   # 菜单管理测试
│   ├── test_dept_management.py   # 部门管理测试
│   ├── test_dict_config_management.py  # 字典配置测试
│   ├── test_project_integration.py     # 项目集成测试
│   ├── test_protocol_integration.py    # 协议集成测试
│   └── test_simulation_integration.py  # 仿真集成测试
└── unit/                         # 单元测试
    ├── services/                 # 服务层测试
    ├── dao/                      # DAO层测试
    ├── controllers/              # 控制器测试
    └── utils/                    # 工具类测试
```

## 业务关键测试

`test_business_critical.py` 包含19个关键测试，覆盖：

### 密码安全 (6个测试)
- ✅ 密码哈希安全性
- ✅ 防止时序攻击
- ✅ 特殊字符支持
- ✅ 长度限制处理
- ✅ 空值安全
- ✅ bcrypt格式验证

### 项目业务逻辑 (2个测试)
- ✅ 项目编码唯一性
- ✅ 防止删除固化版本

### 数据完整性 (2个测试)
- ✅ 命名转换可逆性
- ✅ 时间格式化边界情况

### 协议验证 (2个测试)
- ✅ 协议类型规范化
- ✅ 字段定义完整性

### 错误处理 (3个测试)
- ✅ 异常消息保留
- ✅ 空字符串处理
- ✅ None值处理

### 安全约束 (2个测试)
- ✅ SQL注入防护文档
- ✅ 软删除数据保留

### 仿真安全 (2个测试)
- ✅ 会话ID唯一性
- ✅ 状态值有效性

## 测试原则

### ✅ 应该做的
1. 测试关键业务逻辑
2. 测试安全相关功能
3. 测试数据完整性
4. 测试错误处理
5. 测试边界情况

### ❌ 不应该做的
1. 为了覆盖率而测试
2. 测试私有方法
3. 测试实现细节
4. 追求100%覆盖率
5. 创建无意义的测试

## 测试配置

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### 覆盖率配置
- 最低覆盖率: 70% (目标)
- 当前覆盖率: 37%
- 排除文件: migrations, tests, __pycache__

## 常见问题

### Q: 为什么覆盖率只有37%？
A: 我们专注于测试关键业务逻辑，而不是追求覆盖率数字。37%覆盖的是最重要的代码路径。

### Q: 如何添加新测试？
A: 
1. 确定测试类型（单元/集成）
2. 在相应目录创建测试文件
3. 遵循现有测试模式
4. 专注于业务价值，而非覆盖率

### Q: 测试失败怎么办？
A:
1. 查看错误信息
2. 检查是否是代码问题
3. 如果是测试问题，修复测试
4. 不要为了通过而删除测试

### Q: 如何运行单个测试？
A:
```bash
pytest tests/integration/test_business_critical.py::TestPasswordSecurity::test_password_hashing_is_secure -v
```

## 更多信息

- 详细总结: `.kiro/specs/unit-testing-coverage/STABILITY_FOCUSED_SUMMARY.md`
- 测试脚本: `scripts/run_tests.sh`
- 覆盖率报告: `tests/coverage/html/index.html`
