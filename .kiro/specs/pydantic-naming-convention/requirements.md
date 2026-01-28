# Pydantic 命名约定优化 - 需求文档

## 1. 项目背景

### 1.1 当前问题

在统一错误处理系统迁移过程中，发现测试用例大量失败，根本原因是 Pydantic 模型的 `alias_generator=to_camel` 配置导致字段命名不一致：

**问题表现：**
```python
# ❌ 当前测试代码（失败）
config = ConfigModel(config_id=1, config_name="test")
# 结果：所有字段都是 None！

# ✅ 正确的方式
config = ConfigModel(configId=1, configName="test")
# 结果：字段正确赋值
```

**影响范围：**
- 14+ 个测试文件失败
- 涉及所有使用 `alias_generator=to_camel` 的 VO 模型
- 包括：config, dept, dict, menu, notice, role, user 等核心模块

### 1.2 行业标准分析

**行业没有统一命名唯一标准，但“单一命名 + 全局一致”是共识。**

| 方面 | 本项目标准 | 依据 |
|------|------------|------|
| Python 内部代码 | snake_case | PEP 8 官方规范 |
| 对外 JSON API | camelCase | 前端生态习惯、跨语言契约一致性 |
| 实现方式 | 统一转换层 | 避免散落手工转换导致不一致 |

**选择 camelCase 对外输出的原因：**
1. **前端友好**：JavaScript/TypeScript 默认风格
2. **契约统一**：API 对外格式固定，便于多端接入
3. **兼容性**：通过统一转换层保持内部 snake_case 不变

### 1.3 当前架构

```python
# 当前 VO 模型配置
class ConfigModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,  # ✅ 正确：API 自动转换
        from_attributes=True
        # ❌ 缺失：populate_by_name=True
    )
    
    config_id: Optional[int]  # Python 内部：snake_case
    config_name: Optional[str]
    
# API 响应（正确）
# {"configId": 1, "configName": "test"}  ✅ camelCase
```

## 2. 需求目标

### 2.1 短期目标（本次 Spec）

**P0 - 紧急修复测试失败 + 全量标准化：**
1. 修复所有因 Pydantic 字段命名导致的测试失败
2. 确保测试代码能够正常运行
3. 不影响现有 API 行为（保持对外 camelCase 输出）
4. 后端代码统一 snake_case，对外统一 camelCase
5. 响应出口与自动校验机制落地，防止回归

**范围限定：**
- ✅ 修复测试代码中的字段命名问题
- ✅ 添加必要的 Pydantic 配置支持
- ✅ 修复现存 snake_case 外泄的接口
- ✅ 统一响应序列化出口与自动校验
- ❌ 不涉及业务逻辑重构
- ❌ 不改变 API 响应语义（仅规范化为 camelCase）

### 2.2 长期目标（未来 Spec）

**P1 - 全面命名规范化（单独任务）：**
1. 统一所有 VO 模型的 Pydantic 配置
2. 建立命名约定最佳实践文档
3. 创建自动化检查工具
4. 全面审计和优化代码库

## 3. 功能需求

### 3.1 统一模型基类（CamelModelBase）

**FR-1: 全量 VO 继承 CamelModelBase**

**需求描述：**
为所有 VO/Response 模型统一使用 `CamelModelBase`（或统一 ConfigDict 配置），确保：
- 输入同时支持 snake_case 和 camelCase（`populate_by_name=True`）
- 输出统一 camelCase（`alias_generator=to_camel` + 统一响应出口）
- ORM 对象可直接转模型（`from_attributes=True`）

**配置示例：**
```python
class CamelModelBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True
    )

class ConfigModel(CamelModelBase):
    config_id: Optional[int]

# 现在两种方式都可以工作
config1 = ConfigModel(config_id=1)      # ✅ snake_case
config2 = ConfigModel(configId=1)       # ✅ camelCase
```

**优先级：** P0  
**验收标准：**
- 所有 VO 模型统一基类或统一配置
- 测试代码可以使用 snake_case 创建实例
- API 响应仍然是 camelCase（不受影响）

### 3.2 统一响应序列化出口

**FR-2: 统一 Response 输出层**

**需求描述：**
所有 Controller/Service 返回必须经由统一序列化出口，强制 `by_alias=True`，并统一处理：
- BaseModel / ResponseModel
- ORM/Row 对象
- dict/list 嵌套结构

**优先级：** P0  
**验收标准：**
- 任何对外 JSON 字段不出现 `_`
- response_util 与 response_util_new 输出一致遵循 camelCase

### 3.3 测试代码修复

**FR-3: 修复测试用例字段命名**

**需求描述：**
修复所有因字段命名不匹配导致失败的测试用例。

**修复策略（二选一）：**

**方案 A：使用 camelCase（推荐用于新测试）**
```python
# 测试代码使用 camelCase
config = ConfigModel(configId=1, configName="test")
dept = DeptModel(deptId=1, deptName="test")
```

**方案 B：依赖 populate_by_name（推荐用于现有测试）**
```python
# 添加 populate_by_name 后，现有测试无需修改
config = ConfigModel(config_id=1, config_name="test")  # ✅ 仍然有效
```

**优先级：** P0  
**验收标准：**
- 所有测试用例通过
- 测试覆盖率不降低
- 测试代码清晰易读

### 3.4 自动化校验

**FR-4: 响应字段命名自动检查**

**需求描述：**
新增自动化校验（测试或 CI 脚本），检测响应 JSON 是否含 `_` 字段（可配置白名单）。

**优先级：** P0  
**验收标准：**
- CI/测试对 snake_case 外泄有阻断能力
- 白名单规则可配置、可维护

### 3.5 缺失导入修复

**FR-5: 修复缺失的异常类导入**

**需求描述：**
修复部分 Service 文件中缺失的新异常类导入。

**问题示例：**
```python
# dept_service.py
# ❌ 缺失导入
raise PermissionException(...)  # NameError: name 'PermissionException' is not defined

# ✅ 需要添加
from exceptions.new_exception import PermissionException
```

**优先级：** P0  
**验收标准：**
- 所有新异常类正确导入
- 无 NameError 或 ImportError
- 代码通过静态检查

### 3.6 错误码完整性

**FR-6: 补充缺失的错误码**

**需求描述：**
补充部分 Service 使用但未定义的错误码。

**问题示例：**
```python
# notice_service.py
raise ResourceConflictException(
    error_code=ErrorCode.RESOURCE_CONFLICT,  # ❌ 不存在
    ...
)

# 需要使用正确的错误码或添加新错误码
```

**优先级：** P1  
**验收标准：**
- 所有使用的错误码都已定义
- 错误码语义正确
- 无 AttributeError

## 4. 非功能需求

### 4.1 兼容性

**NFR-1: API 响应格式不变**
- API 响应必须保持 camelCase 格式
- 前端代码无需任何修改
- 向后兼容现有客户端

**NFR-2: Python 代码风格不变**
- Python 内部代码继续使用 snake_case
- 符合 PEP 8 规范
- 代码可读性不降低

### 4.2 测试质量

**NFR-3: 测试覆盖率**
- 修复后测试覆盖率不降低
- 所有核心功能有测试覆盖
- 测试用例清晰易维护

**NFR-4: 测试执行效率**
- 测试执行时间不显著增加
- 测试用例独立可运行
- 支持并行测试执行

### 4.3 代码质量

**NFR-5: 代码一致性**
- 所有 VO 模型配置一致
- 命名约定统一
- 代码风格符合项目规范

## 5. 约束条件

### 5.1 技术约束

1. **Pydantic 版本**：使用当前版本（v2.x），不升级
2. **Python 版本**：Python 3.9+
3. **测试框架**：pytest + pytest-asyncio
4. **不破坏现有功能**：所有现有 API 行为保持不变

### 5.2 范围约束

**本次 Spec 包含：**
- ✅ 修复测试失败
- ✅ 添加 `populate_by_name` 配置
- ✅ 修复缺失导入和错误码
- ✅ 确保测试通过

**本次 Spec 不包含：**
- ❌ 全面代码重构
- ❌ 命名规范文档编写
- ❌ 自动化检查工具开发
- ❌ 历史代码全面审计

### 5.3 时间约束

**预计工期：** 0.5-1 天

**里程碑：**
- 配置优化：2-3 小时
- 测试修复：3-4 小时
- 验证测试：1-2 小时

## 6. 受影响的模块

### 6.1 VO 模型（需要添加 populate_by_name）

**核心模块：**
- `config_vo.py` - 参数配置
- `dept_vo.py` - 部门管理
- `dict_vo.py` - 字典管理
- `menu_vo.py` - 菜单管理
- `notice_vo.py` - 通知公告
- `role_vo.py` - 角色管理
- `user_vo.py` - 用户管理
- `post_vo.py` - 岗位管理
- `job_vo.py` - 定时任务
- `log_vo.py` - 日志管理

**业务模块：**
- `project_vo.py` - 工程管理
- `protocol_vo.py` - 协议管理
- `device_vo.py` - 设备管理
- `simulation_vo.py` - 仿真管理
- `project_version_vo.py` - 工程版本

**补充：**
- `device_category_vo.py` 当前仍使用旧 `Config` 且无 alias，需统一为 camelCase 输出

### 6.2 测试文件（需要修复）

**Service 测试：**
- `test_config_service.py` ✅ 已修复
- `test_dept_service.py` - 需要修复
- `test_dict_service.py` - 需要修复
- `test_menu_service.py` - 需要修复
- `test_notice_service.py` - 需要修复
- 其他 service 测试文件

**DAO 测试：**
- 可能需要修复部分 DAO 测试

### 6.3 Service 文件（需要修复导入）

**缺失导入：**
- `dept_service.py` - 缺少 `PermissionException`
- `notice_service.py` - 错误码问题
- 其他可能的 Service 文件

### 6.4 响应层与工具

- `utils/response_util.py` - 统一输出 camelCase（data/rows/model_content）
- `utils/response_util_new.py` - RFC7807 输出字段保持 camelCase
- `utils/page_util.py` - 分页响应字段输出 camelCase
 - `utils/common_util.py` - CamelCaseUtil 作为统一转换工具

## 7. 验收标准

### 7.1 功能验收

**AC-1: Pydantic 配置完整**
- [ ] 所有 VO 模型添加 `populate_by_name=True`
- [ ] 配置格式统一一致
- [ ] 不影响 API 响应格式

**AC-2: 测试全部通过**
- [ ] `pytest tests/unit/services/ -x` 全部通过
- [ ] 无 NameError, AttributeError, TypeError
- [ ] 测试覆盖率 ≥ 当前水平

**AC-3: 导入和错误码完整**
- [ ] 所有新异常类正确导入
- [ ] 所有错误码已定义
- [ ] 代码通过静态检查

### 7.2 质量验收

**AC-4: 代码质量**
- [ ] 符合 PEP 8 规范
- [ ] 通过 ruff 检查
- [ ] 无明显代码异味

**AC-5: 文档完整**
- [ ] 修改说明清晰
- [ ] 配置示例准确
- [ ] 注释充分

### 7.3 性能验收

**AC-6: 性能不降低**
- [ ] 测试执行时间不显著增加（< 10%）
- [ ] API 响应时间不受影响
- [ ] 内存使用无异常增长

## 8. 风险与缓解

### 8.1 技术风险

**风险 1: populate_by_name 可能影响性能**
- **影响**: Pydantic 需要检查两种命名格式
- **概率**: 低
- **缓解**: 
  - Pydantic v2 性能优化良好
  - 实际影响可忽略不计
  - 可通过性能测试验证

**风险 2: 测试修复可能遗漏**
- **影响**: 部分测试仍然失败
- **概率**: 中
- **缓解**:
  - 运行完整测试套件
  - 使用 `-x` 参数逐个修复
  - 自动化检查脚本

### 8.2 业务风险

**风险 3: API 行为意外改变**
- **影响**: 前端功能异常
- **概率**: 极低
- **缓解**:
  - `populate_by_name` 只影响输入，不影响输出
  - 充分的集成测试
  - 灰度发布验证

**风险 4: 历史接口 snake_case 外泄**
- **影响**: 新规范与旧接口不一致
- **概率**: 中
- **缓解**:
  - 统一响应出口 + 自动检查
  - 为历史接口提供迁移说明

## 9. 后续规划

### 9.1 短期（本次 Spec 后）

1. **验证修复效果**
   - 运行完整测试套件
   - 确认所有测试通过
   - 性能基准测试

2. **文档更新**
   - 更新测试编写指南
   - 记录 Pydantic 配置最佳实践

### 9.2 长期（未来 Spec）

**创建独立的命名规范化 Spec：**

1. **全面审计**
   - 审计所有 VO 模型配置
   - 检查命名一致性
   - 识别潜在问题

2. **规范文档**
   - 编写命名约定指南
   - 提供代码示例
   - 建立最佳实践

3. **自动化工具**
   - 开发配置检查脚本
   - 集成到 CI/CD
   - 自动化修复工具

4. **代码优化**
   - 统一所有配置
   - 优化测试代码
   - 提升代码质量

## 10. 参考资料

### 10.1 技术文档

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Pydantic V2 Documentation - Model Config](https://docs.pydantic.dev/latest/api/config/)
- [Google API Design Guide](https://cloud.google.com/apis/design)
- [RFC 8259 - JSON Data Interchange Format](https://tools.ietf.org/html/rfc8259)

### 10.2 行业实践

- Stripe API - camelCase 响应格式
- AWS SDK - 自动命名转换
- GitHub API - camelCase 标准
- Microsoft Azure - camelCase 约定

---

**文档版本**: 1.0  
**创建日期**: 2026-01-28  
**作者**: Kiro AI  
**状态**: 待审核
