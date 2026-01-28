# GridList 优化 TODO List

## 📊 总体进度

- **总计**: 23 个文件
- **已完成**: 4 个 ✅
- **待完成**: 19 个 ⏳
- **完成率**: 17.4%

---

## 🔴 第一批：高优先级（核心系统模块）

### 1. ✅ system/dict/index.vue
- [x] 添加 queryTransform
- [x] 使用 serializeDateRange
- [x] 简化 loadData
- [x] 优化导出函数

### 2. ✅ system/config/index.vue
- [x] 添加 queryTransform
- [x] 使用 serializeDateRange
- [x] 简化 loadData
- [x] 优化导出函数

### 3. ✅ system/post/index.vue
- [x] 简化 loadData（无日期范围）
- [x] 优化导出函数

### 4. ✅ monitor/job/index.vue
- [x] 简化 loadData（无日期范围）
- [x] 优化导出函数

### 5. ⏳ system/role/index.vue
**日期范围**: ✓ 有
**当前问题**: 使用 `proxy.addDateRange`
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadRoleData`，移除手动参数处理
- [ ] 优化 `handleExport`，移除 addDateRange

### 6. ⏳ system/user/index.vue
**日期范围**: ✓ 有
**当前问题**: 已有 queryTransform，需检查是否正确
**优化步骤**:
- [ ] 检查现有 queryTransform 实现
- [ ] 确认是否使用 serializeDateRange
- [ ] 检查 loadUserData 是否简化
- [ ] 验证功能正常

### 7. ⏳ system/notice/index.vue
**日期范围**: ✗ 无
**当前问题**: 手动解构参数
**优化步骤**:
- [ ] 简化 `loadNoticeData`，直接传 params
- [ ] 添加 try-catch 错误处理
- [ ] 移除手动参数解构

### 8. ⏳ monitor/audit/index.vue
**日期范围**: ✓ 有
**当前问题**: 使用 `proxy.addDateRange`
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadAuditData`，移除 addDateRange
- [ ] 添加 try-catch 错误处理

### 9. ⏳ monitor/logininfor/index.vue
**日期范围**: ✓ 有
**当前问题**: 使用 `proxy.addDateRange`
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadLogininforData`，移除 addDateRange
- [ ] 优化 `handleExport`

---

## 🟡 第二批：中优先级（常用功能）

### 10. ⏳ tool/gen/index.vue
**日期范围**: ✓ 有
**当前问题**: 手动解构参数 + 手动处理日期
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadTableData`，移除手动参数处理
- [ ] 添加 try-catch 错误处理

### 11. ⏳ system/menu/index.vue
**日期范围**: ✗ 无
**当前问题**: 手动解构参数
**优化步骤**:
- [ ] 简化 `loadMenuData`，直接传 params
- [ ] 添加 try-catch 错误处理
- [ ] 移除手动参数解构

### 12. ⏳ system/dept/index.vue
**日期范围**: ✗ 无
**当前问题**: 手动解构参数
**优化步骤**:
- [ ] 简化 `loadDeptData`，直接传 params
- [ ] 添加 try-catch 错误处理
- [ ] 移除手动参数解构

### 13. ⏳ monitor/online/index.vue
**日期范围**: ✗ 无
**当前问题**: 手动解构参数
**优化步骤**:
- [ ] 简化 `loadOnlineData`，直接传 params
- [ ] 添加 try-catch 错误处理
- [ ] 移除手动参数解构

### 14. ⏳ protocol/index.vue
**日期范围**: ✓ 有
**当前问题**: 使用 `proxy.addDateRange`
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadProtocolData`，移除 addDateRange
- [ ] 添加 try-catch 错误处理

### 15. ⏳ project/index.vue
**日期范围**: ✓ 有
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadProjectData` 实现
- [ ] 确认是否需要添加 queryTransform
- [ ] 验证功能正常

### 16. ⏳ system/role/authUser.vue
**日期范围**: ✓ 有
**当前问题**: 手动解构参数
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadAuthUserData`
- [ ] 添加 try-catch 错误处理

---

## 🟢 第三批：低优先级（业务模块和组件）

### 17. ⏳ device/category/index.vue
**日期范围**: ✓ 有
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadCategoryData` 实现
- [ ] 确认是否需要添加 queryTransform
- [ ] 验证功能正常

### 18. ⏳ device/index.vue
**日期范围**: ✓ 有
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadDeviceData` 实现
- [ ] 确认是否需要添加 queryTransform
- [ ] 验证功能正常

### 19. ⏳ system/dict/data.vue
**日期范围**: ✗ 无
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadDictData` 实现
- [ ] 确认是否已优化
- [ ] 验证功能正常

### 20. ⏳ system/user/authRole.vue
**日期范围**: ✗ 无
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadRolesData` 实现
- [ ] 确认是否已优化
- [ ] 验证功能正常

### 21. ⏳ project/components/VersionList.vue
**日期范围**: ✗ 无（注释掉）
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadVersionData` 实现
- [ ] 确认是否已优化
- [ ] 验证功能正常

### 22. ⏳ project/simulation/components/MessageListPanel.vue
**日期范围**: ✗ 无
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadMessageData` 实现
- [ ] 确认是否已优化
- [ ] 验证功能正常

### 23. ⏳ monitor/operlog/index.vue
**日期范围**: ✓ 有
**当前问题**: 需检查实现
**优化步骤**:
- [ ] 检查 `loadOperlogData` 实现
- [ ] 确认是否需要优化
- [ ] 验证功能正常

### 24. ⏳ components/business/Monitor/OperlogGrid.vue
**日期范围**: ✓ 有
**当前问题**: 使用 `proxy.addDateRange`
**优化步骤**:
- [ ] 添加 `:query-transform="queryTransform"` 到 ZxGridList
- [ ] 导入 `serializeDateRange`
- [ ] 创建 `queryTransform` 函数
- [ ] 简化 `loadOperlogData`，移除 addDateRange
- [ ] 优化导出函数

---

## 📝 优化模板

### 有日期范围的文件模板

```vue
<template>
  <ZxGridList 
    ref="gridListRef" 
    :load-data="loadData" 
    :query-transform="queryTransform"
  >
    <!-- ... -->
  </ZxGridList>
</template>

<script setup>
import { serializeDateRange } from '@/utils/ruoyi';

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 - 不处理参数转换 */
async function loadData(params) {
  try {
    return await listApi(params);
  } catch (e) {
    return { data: [], total: 0 };
  }
}

/** 导出 - getCurrentQuery 已返回转换后的参数 */
function handleExport() {
  const query = gridListRef.value?.getCurrentQuery?.() || {};
  proxy.download('api/export', query, `file_${new Date().getTime()}.xlsx`);
}
</script>
```

### 无日期范围的文件模板

```vue
<template>
  <ZxGridList 
    ref="gridListRef" 
    :load-data="loadData"
  >
    <!-- ... -->
  </ZxGridList>
</template>

<script setup>
/** GridList 数据加载函数 - 不处理参数转换 */
async function loadData(params) {
  try {
    return await listApi(params);
  } catch (e) {
    return { data: [], total: 0 };
  }
}

/** 导出 */
function handleExport(query) {
  proxy.download('api/export', query, `file_${new Date().getTime()}.xlsx`);
}
</script>
```

---

## ✅ 验证清单

每个文件优化后需要验证：

- [ ] 移除了手动参数解构和重组
- [ ] 有日期范围的添加了 `queryTransform` 和 `serializeDateRange`
- [ ] 无日期范围的直接传递 `params`
- [ ] `loadData` 函数添加了 try-catch 错误处理
- [ ] 导出函数不再手动处理日期范围
- [ ] 代码通过 ESLint 检查
- [ ] 功能测试通过（列表加载、筛选、导出）

---

## 📈 进度跟踪

### 第一批进度（9个文件）
- ✅ 已完成: 4/9 (44.4%)
- ⏳ 待完成: 5/9 (55.6%)

### 第二批进度（7个文件）
- ✅ 已完成: 0/7 (0%)
- ⏳ 待完成: 7/7 (100%)

### 第三批进度（8个文件）
- ✅ 已完成: 0/8 (0%)
- ⏳ 待完成: 8/8 (100%)

### 总体进度
- ✅ 已完成: 4/24 (16.7%)
- ⏳ 待完成: 20/24 (83.3%)

---

## 🎯 今日目标

**目标**: 完成第一批所有文件（5个待完成）

1. system/role/index.vue
2. system/user/index.vue
3. system/notice/index.vue
4. monitor/audit/index.vue
5. monitor/logininfor/index.vue

**预计时间**: 约 25 分钟

---

## 📚 参考文档

- 优化方案: `dev-docs/front/gridlist-optimization-plan.md`
- 分析报告: `dev-docs/front/gridlist-optimization-analysis.md`
