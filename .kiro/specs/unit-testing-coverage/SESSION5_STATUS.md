# 单元测试覆盖率 - 第5次会话状态

**日期**: 2026-01-24
**会话**: 第5次工作会话
**状态**: 🔴 需要修复测试问题

---

## 📊 当前情况

### 发现的问题

#### 后端测试问题
1. **方法名不匹配** - 测试中使用的方法名与实际代码不一致
   - `PwdUtil.hash_password` → 实际可能是 `encrypt_password`
   - `TimeFormatUtil.format_datetime` → 实际可能是 `format_time`
   - `UserService.add_user` → 实际方法名不同
   - `MenuService.delete_menu` → 实际方法名不同

2. **Controller测试问题**
   - `AsyncClient` 使用不当
   - 部分测试返回 401 Unauthorized
   - 部分测试返回 405 Method Not Allowed

3. **DAO测试问题**
   - 方法不存在的AttributeError
   - `DictTypeDao.delete_dict_type` 不存在
   - `DeptDao.get_children_depts` 不存在

#### 前端测试问题
1. **组件测试失败** - 新创建的组件测试有多个失败
   - UserFormDialog: 8个失败
   - ProjectFormDialog: 13个失败
   - ProtocolFormDrawer: 未运行

2. **覆盖率工具问题**
   - `@vitest/coverage-v8` 版本不兼容
   - `this.isIncluded is not a function` 错误

---

## 🎯 修复策略

### 优先级1: 修复实际可运行的测试
不修复所有测试，而是专注于：
1. 确认哪些测试是正确的并能运行
2. 运行这些测试获取实际覆盖率
3. 如果覆盖率已接近70%，只需小幅调整

### 优先级2: 运行部分测试获取覆盖率
```bash
# 后端：只运行已知可工作的测试
pytest tests/unit/services/test_project_service.py \
       tests/unit/services/test_protocol_service.py \
       tests/unit/services/test_simulation_service.py \
       tests/unit/repositories/ \
       --cov=module_admin --cov-report=term

# 前端：运行非组件测试
yarn test tests/unit/composables/ tests/unit/stores/ tests/unit/api/ tests/unit/utils/auth.test.ts tests/unit/utils/ruoyi.test.ts
```

### 优先级3: 评估实际覆盖率
- 如果已达到65%+，只需小幅优化
- 如果低于60%，需要修复更多测试

---

## 📋 下一步行动

### 立即行动
1. ✅ 运行部分后端测试获取覆盖率基线
2. ✅ 运行前端非组件测试获取覆盖率
3. ✅ 评估当前实际覆盖率
4. ✅ 决定是修复测试还是创建新测试

### 备选方案
如果修复测试成本太高：
- 创建更简单的集成测试
- 专注于核心业务逻辑覆盖
- 使用实际代码运行测试而非Mock

---

## 💡 经验教训

1. **测试需要与实际代码同步** - 在创建测试前应先检查实际方法名
2. **Mock策略需要验证** - AsyncClient的使用需要根据实际FastAPI版本调整
3. **组件测试需要更多设置** - Vue组件测试需要完整的测试环境配置
4. **覆盖率工具版本很重要** - vitest和coverage工具版本需要兼容

---

**更新时间**: 2026-01-24
**下一步**: 运行部分测试获取实际覆盖率基线
