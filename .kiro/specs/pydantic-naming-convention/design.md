# Pydantic 命名约定优化 - 设计文档

## 1. 设计概述

### 1.1 设计目标

本设计旨在建立项目级命名标准：后端内部统一 snake_case、对外 API 统一 camelCase。通过统一模型基类、统一响应序列化出口与自动化校验，修复当前测试失败与命名混用问题，并确保后续开发不会回归。

### 1.2 设计原则

1. **单一标准**：内部 snake_case、外部 camelCase，禁止混用
2. **统一出口**：所有对外响应走统一序列化层
3. **向后兼容**：响应语义不变，格式标准化为 camelCase
4. **自动化防回归**：新增检查避免 snake_case 外泄
5. **可持续维护**：通过基类/模板固化规范

## 2. 技术方案

### 2.1 命名规则与层次划分

**标准：**
- **后端内部**：Python/ORM/业务代码统一 **snake_case**
- **对外 JSON**：所有 API 响应统一 **camelCase**
- **输入兼容**：接口入参允许 snake/camel 双写，输出严格 camelCase

### 2.2 统一模型基类（CamelModelBase）

#### 2.2.1 当前问题分析

**问题根源：**
```python
# 当前配置
class ConfigModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # 自动生成 camelCase 别名
        from_attributes=True
        # ❌ 缺失：populate_by_name=True
    )

    config_id: Optional[int]  # 字段名：config_id
                              # 别名：configId（由 alias_generator 生成）

# 问题表现
config = ConfigModel(config_id=1)  # ❌ 失败！字段为 None
config = ConfigModel(configId=1)   # ✅ 成功！
```

**原因：**
- `alias_generator=to_camel` 改变了字段的**输入别名**
- 默认情况下只接受别名（configId），不接受字段名（config_id）
- 测试与业务代码仍使用 snake_case 创建实例

#### 2.2.2 解决方案

**方案：引入统一基类 `CamelModelBase`**
```python
class CamelModelBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True  # ✅ 同时支持字段名和别名
    )

class ConfigModel(CamelModelBase):
    config_id: Optional[int]

# 现在两种方式都可以工作
config1 = ConfigModel(config_id=1)      # ✅ snake_case
config2 = ConfigModel(configId=1)       # ✅ camelCase

# API 响应（不受影响）
config1.model_dump(by_alias=True)  # {"configId": 1}  ✅ camelCase
```

**优势：**
1. **统一输入**：snake/camel 双写兼容
2. **统一输出**：由响应出口强制 camelCase
3. **避免漏改**：基类集中配置，VO 统一继承

#### 2.2.3 标准模板

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModelBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True
    )

class XxxModel(CamelModelBase):
    """模型说明"""
    # 字段定义...
```

### 2.3 统一序列化出口（serialize_for_response）

**目的：** 所有对外响应统一走序列化出口，避免 snake_case 外泄。

**规则：**
- BaseModel → `model_dump(by_alias=True, mode="json")`
- dict/list → `CamelCaseUtil.transform_result`
- ORM/Row → `jsonable_encoder` + camelCase 转换

**要求：**
- ResponseUtil/ResponseUtilNew 内部统一调用该序列化器
- Controller/Service 禁止直接返回未转换对象

### 2.4 统一响应层

- 规定所有对外响应必须通过 ResponseUtil（或统一响应模型）输出
- `response_model_by_alias=False` 视为违规，必须移除
- `model_dump()` 需统一由响应出口处理，不在接口层直接调用

### 2.5 自动化校验

**方案：** 新增测试或 CI 脚本，检查响应 JSON 是否含 `_` 字段（可白名单）。

### 2.6 测试修复策略

**推荐策略：**
- **现有测试**：保持 snake_case，依赖 `populate_by_name`
- **新测试**：可使用 camelCase，覆盖 API 输入
- **集成测试**：必须断言输出无 `_` 字段

### 2.7 异常导入修复

**问题分析：** 部分 Service 缺少异常导入（如 PermissionException）。

**标准导入模板：**
```python
from exceptions.new_exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessException,
    SystemException,
    PermissionException,
    AuthException
)
from config.error_codes import ErrorCode
```

### 2.8 错误码补充

**问题分析：** 部分 Service 使用未定义错误码。

**修复策略：**
- 优先使用现有具体错误码
- 必要时补充通用错误码，并确保语义明确

## 3. 实施计划

### 3.1 实施阶段

#### Phase 1: 模型层标准化（2-3 小时）

**任务：**
1. 新增 `CamelModelBase` 统一配置
2. 迁移所有 VO/Response 模型继承基类
3. 统一 `device_category_vo.py` 等历史例外
4. 修正分页/列表模型的输出配置

**验收标准：**
- 所有 VO/Response 模型统一基类
- snake/camel 输入兼容生效

#### Phase 2: 序列化与响应出口统一（2-3 小时）

**任务：**
1. 实现 `serialize_for_response()` 统一序列化
2. `ResponseUtil/ResponseUtilNew` 全部走统一序列化
3. 清理 `response_model_by_alias=False`
4. 禁止接口层直接 `model_dump()` 未指定 alias

**验收标准：**
- 所有对外响应 JSON 不包含 `_`
- 旧响应与新响应均符合 camelCase

#### Phase 3: 自动化校验与测试（2-3 小时）

**任务：**
1. 新增响应命名检查测试/脚本
2. 跑单元测试与集成测试
3. 修复缺失导入与错误码

**验收标准：**
- `pytest tests/unit/services/ -x` 全部通过
- 响应命名检查通过
- 无 NameError/AttributeError

### 3.2 回滚方案

如果修复过程中出现问题，可快速回滚：

**回滚步骤：**
1. 恢复 VO/Response 模型基类修改
2. 恢复 ResponseUtil 序列化逻辑
3. 恢复新增测试/脚本

**回滚脚本：**
```bash
# 使用 git 回滚
git checkout -- module_admin/entity/vo/
git checkout -- utils/response_util.py
git checkout -- utils/response_util_new.py
git checkout -- tests/
```

## 4. 受影响的文件清单

### 4.1 VO 模型文件（需要添加配置）

**核心模块（10 个）：**
1. `module_admin/entity/vo/config_vo.py` - 参数配置
2. `module_admin/entity/vo/dept_vo.py` - 部门管理
3. `module_admin/entity/vo/dict_vo.py` - 字典管理
4. `module_admin/entity/vo/menu_vo.py` - 菜单管理
5. `module_admin/entity/vo/notice_vo.py` - 通知公告
6. `module_admin/entity/vo/role_vo.py` - 角色管理
7. `module_admin/entity/vo/user_vo.py` - 用户管理
8. `module_admin/entity/vo/post_vo.py` - 岗位管理
9. `module_admin/entity/vo/job_vo.py` - 定时任务
10. `module_admin/entity/vo/log_vo.py` - 日志管理

**业务模块（5 个）：**
11. `module_admin/entity/vo/project_vo.py` - 工程管理
12. `module_admin/entity/vo/protocol_vo.py` - 协议管理
13. `module_admin/entity/vo/device_vo.py` - 设备管理
14. `module_admin/entity/vo/simulation_vo.py` - 仿真管理
15. `module_admin/entity/vo/project_version_vo.py` - 工程版本

**补充：**
16. `module_admin/entity/vo/device_category_vo.py` - 当前使用旧 Config，无 alias
17. `module_admin/entity/vo/base.py` - 新增 CamelModelBase（统一基类）

### 4.2 测试文件（可能需要修复）

**Service 测试（14 个）：**
1. `tests/unit/services/test_config_service.py` ✅ 已修复
2. `tests/unit/services/test_dept_service.py` - 需要修复导入
3. `tests/unit/services/test_dict_service.py` - 需要检查
4. `tests/unit/services/test_menu_service.py` - 需要检查
5. `tests/unit/services/test_notice_service.py` - 需要修复错误码
6. `tests/unit/services/test_role_service.py` - 需要检查
7. `tests/unit/services/test_user_service.py` - 需要检查
8. `tests/unit/services/test_post_service.py` - 需要检查
9. `tests/unit/services/test_job_service.py` - 需要检查
10. `tests/unit/services/test_log_service.py` - 需要检查
11. `tests/unit/services/test_project_service.py` - 需要检查
12. `tests/unit/services/test_protocol_service.py` - 需要检查
13. `tests/unit/services/test_device_service.py` - 需要检查
14. `tests/unit/services/test_simulation_service.py` - 需要检查

### 4.3 Service 文件（需要修复导入）

**已知问题：**
1. `module_admin/service/dept_service.py` - 缺少 `PermissionException` 导入
2. `module_admin/service/notice_service.py` - 错误码问题
3. 其他可能的 Service 文件（需要全面检查）

### 4.4 响应层与工具

- `utils/response_util.py` - 统一序列化出口（camelCase）
- `utils/response_util_new.py` - RFC7807 响应输出统一 camelCase
- `utils/page_util.py` - 分页输出统一 camelCase
- `utils/common_util.py` - CamelCaseUtil 转换工具

### 4.5 自动化校验

- `tests/unit/utils/test_response_naming.py`（新增）- 响应命名检查

## 5. 测试策略

### 5.1 单元测试

**测试范围：**
- 所有 Service 层测试
- 所有 DAO 层测试（如果受影响）
- 响应命名校验测试（新增）

**测试命令：**
```bash
# 运行所有 service 测试
pytest tests/unit/services/ -v

# 运行单个测试文件
pytest tests/unit/services/test_config_service.py -v

# 运行响应命名检查
pytest tests/unit/utils/test_response_naming.py -v

# 运行失败时停止
pytest tests/unit/services/ -x
```

**验收标准：**
- 所有测试通过
- 无 NameError, AttributeError, TypeError
- 测试覆盖率 ≥ 当前水平

### 5.2 集成测试

**测试范围：**
- API 响应格式验证
- 前后端集成测试

**测试方法：**
```bash
# 启动后端服务
python app.py --env=dev

# 测试 API 响应格式
curl http://localhost:8000/system/config/list | jq .

# 验证响应是 camelCase（无下划线字段）
# {"data": {"rows": [{"configId": 1, "configName": "..."}]}}
```

**验收标准：**
- API 响应格式保持 camelCase
- 前端功能正常
- 无 API 行为变化

### 5.3 性能测试

**测试方法：**
```bash
# 运行性能基准测试
pytest tests/unit/services/ --benchmark-only

# 对比修改前后的性能
```

**验收标准：**
- 测试执行时间不显著增加（< 10%）
- API 响应时间不受影响
- 内存使用无异常增长

## 6. 风险评估

### 6.1 技术风险

**风险 1: populate_by_name 可能影响性能**
- **影响**: Pydantic 需要检查两种命名格式
- **概率**: 低
- **影响程度**: 低
- **缓解措施**: 
  - Pydantic v2 性能优化良好
  - 实际影响可忽略不计
  - 可通过性能测试验证

**风险 2: 测试修复可能遗漏**
- **影响**: 部分测试仍然失败
- **概率**: 中
- **影响程度**: 中
- **缓解措施**:
  - 运行完整测试套件
  - 使用 `-x` 参数逐个修复
  - 自动化检查脚本

**风险 3: 异常导入遗漏**
- **影响**: 运行时 NameError
- **概率**: 低
- **影响程度**: 中
- **缓解措施**:
  - 全面搜索异常使用
  - 静态代码检查
  - 运行时测试验证

### 6.2 业务风险

**风险 4: API 行为意外改变**
- **影响**: 前端功能异常
- **概率**: 极低
- **影响程度**: 高
- **缓解措施**:
  - `populate_by_name` 只影响输入，不影响输出
  - 充分的集成测试
  - API 响应格式验证

**风险 5: 旧接口 snake_case 外泄**
- **影响**: 对外规范不一致
- **概率**: 中
- **缓解措施**:
  - 统一 ResponseUtil 输出
  - 自动化检查响应字段

**风险 6: 测试覆盖率降低**
- **影响**: 代码质量下降
- **概率**: 低
- **影响程度**: 中
- **缓解措施**:
  - 修复测试而不是删除测试
  - 运行覆盖率报告
  - 确保覆盖率不降低

## 7. 最佳实践

### 7.1 VO 模型编写规范

**标准模板：**
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional

class CamelModelBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True
    )

class XxxModel(CamelModelBase):
    """
    模型说明
    """
    
    # 字段定义（使用 snake_case）
    xxx_id: Optional[int] = Field(default=None, description='主键')
    xxx_name: Optional[str] = Field(default=None, description='名称')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
```

### 7.2 测试编写规范

**推荐方式：**
```python
# ✅ 推荐：使用 snake_case（符合 Python 习惯）
config = ConfigModel(
    config_id=1,
    config_name="test",
    config_value="value"
)

# ✅ 也可以：使用 camelCase（测试 API 输入格式）
config = ConfigModel(
    configId=1,
    configName="test",
    configValue="value"
)

# ❌ 避免：混合使用
config = ConfigModel(
    config_id=1,
    configName="test",  # 不一致
    config_value="value"
)
```

### 7.3 异常处理规范

**标准导入：**
```python
from exceptions.new_exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessException,
    SystemException,
    PermissionException,
    AuthException
)
from config.error_codes import ErrorCode
```

**使用示例：**
```python
# ✅ 正确：使用具体异常类型 + 错误码
raise ValidationException(
    user_message='参数名称不能为空',
    developer_message=f'Config name is required: config_id={config_id}',
    error_code=ErrorCode.CONFIG_NAME_REQUIRED,
    field='config_name'
)

# ✅ 正确：使用通用异常类型
raise ResourceNotFoundException(
    user_message='参数配置不存在',
    developer_message=f'Config not found: config_id={config_id}',
    error_code=ErrorCode.CONFIG_NOT_FOUND
)
```

### 7.4 响应输出规范

**标准：** Controller/Service 不直接返回裸对象，统一走响应出口。

```python
# ✅ 正确：统一响应出口
return ResponseUtil.success(data=payload)

# ❌ 避免：直接返回 model_dump() 或 dict
return payload.model_dump()
```

## 8. 后续优化建议

### 8.1 短期优化（本次 Spec 后）

1. **文档更新**
   - 更新测试编写指南
   - 记录 Pydantic 配置最佳实践
   - 添加代码示例

2. **代码审查**
   - 审查所有 VO 模型配置
   - 确保配置一致性
   - 检查命名规范

3. **性能验证**
   - 运行性能基准测试
   - 对比修改前后的性能
   - 记录性能数据

### 8.2 长期优化（未来 Spec）

1. **全面命名规范化**
   - 创建独立的命名规范 Spec
   - 统一所有代码的命名约定
   - 建立自动化检查工具

2. **自动化工具开发**
   - 开发配置检查脚本
   - 集成到 CI/CD
   - 自动化修复工具

3. **代码质量提升**
   - 全面审计代码库
   - 优化测试代码
   - 提升代码可维护性

## 9. 参考资料

### 9.1 Pydantic 文档

- [Pydantic V2 - Model Config](https://docs.pydantic.dev/latest/api/config/)
- [Pydantic V2 - Alias Generator](https://docs.pydantic.dev/latest/concepts/alias/)
- [Pydantic V2 - populate_by_name](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name)

### 9.2 命名约定

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google API Design Guide](https://cloud.google.com/apis/design)
- [RFC 8259 - JSON Data Interchange Format](https://tools.ietf.org/html/rfc8259)

### 9.3 测试最佳实践

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**文档版本**: 1.0  
**创建日期**: 2026-01-28  
**作者**: Kiro AI  
**状态**: 待审核
