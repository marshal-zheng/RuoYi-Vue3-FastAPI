# 字典功能使用指南与最佳实践

## 快速开始

### 基本概念
- **字典类型(dict_type)**：定义字典的类别和用途，如 `sys_normal_disable`
- **字典数据(dict_data)**：具体的键值对数据，如 `{label: '正常', value: '0'}`
- **字典标签(dict_label)**：显示给用户的文本
- **字典键值(dict_value)**：程序中使用的实际值

### 系统预置字典类型

| 字典类型 | 字典名称 | 用途 | 示例值 |
|---------|---------|------|--------|
| `sys_normal_disable` | 系统开关 | 通用状态控制 | 正常(0), 停用(1) |
| `sys_yes_no` | 系统是否 | 布尔值显示 | 是(Y), 否(N) |
| `sys_user_sex` | 用户性别 | 用户性别选择 | 男(0), 女(1), 未知(2) |
| `sys_show_hide` | 菜单状态 | 菜单显示控制 | 显示(0), 隐藏(1) |
| `sys_job_status` | 任务状态 | 定时任务状态 | 正常(0), 暂停(1) |
| `sys_job_group` | 任务分组 | 任务分类管理 | 默认(default), 数据库(sqlalchemy) |
| `sys_notice_type` | 通知类型 | 通知分类 | 通知(1), 公告(2) |
| `sys_notice_status` | 通知状态 | 通知状态管理 | 正常(0), 关闭(1) |
| `sys_oper_type` | 操作类型 | 操作日志分类 | 新增(1), 修改(2), 删除(3) |
| `sys_common_status` | 系统状态 | 通用操作状态 | 成功(0), 失败(1) |

## 使用方法

### 1. 前端组件中使用

#### 基础用法
```vue
<template>
  <div>
    <!-- 下拉选择 -->
    <el-select v-model="form.status">
      <el-option 
        v-for="dict in sys_normal_disable" 
        :key="dict.value"
        :label="dict.label" 
        :value="dict.value" 
      />
    </el-select>
    
    <!-- 单选按钮 -->
    <el-radio-group v-model="form.isPublic">
      <el-radio 
        v-for="dict in sys_yes_no"
        :key="dict.value"
        :value="dict.value"
      >
        {{ dict.label }}
      </el-radio>
    </el-radio-group>
    
    <!-- 状态标签显示 -->
    <dict-tag :options="sys_normal_disable" :value="row.status" />
  </div>
</template>

<script setup>
const { proxy } = getCurrentInstance();
const { sys_normal_disable, sys_yes_no } = proxy.useDict('sys_normal_disable', 'sys_yes_no');
</script>
```

#### 高级用法
```vue
<template>
  <div>
    <!-- 多选框 -->
    <el-checkbox-group v-model="form.types">
      <el-checkbox 
        v-for="dict in sys_notice_type"
        :key="dict.value"
        :value="dict.value"
      >
        {{ dict.label }}
      </el-checkbox>
    </el-checkbox-group>
    
    <!-- 表格列显示 -->
    <el-table :data="tableData">
      <el-table-column label="状态" prop="status">
        <template #default="{ row }">
          <dict-tag :options="sys_normal_disable" :value="row.status" />
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 搜索筛选 -->
    <el-form :model="queryParams">
      <el-form-item label="状态">
        <el-select v-model="queryParams.status" clearable>
          <el-option label="全部" value="" />
          <el-option 
            v-for="dict in sys_normal_disable"
            :key="dict.value"
            :label="dict.label"
            :value="dict.value"
          />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>
```

### 2. 字典值转换

#### 单个值转换
```javascript
// 在表格或其他地方显示字典标签
function statusFormatter(row, column) {
  return proxy.selectDictLabel(sys_normal_disable.value, row.status);
}

// 使用示例
const statusText = proxy.selectDictLabel(sys_normal_disable.value, '0'); // 返回 "正常"
```

#### 多个值转换
```javascript
// 多值转换（用逗号分隔）
function multiStatusFormatter(row, column) {
  return proxy.selectDictLabels(sys_notice_type.value, row.types, ',');
}

// 使用示例  
const typesText = proxy.selectDictLabels(sys_notice_type.value, '1,2', ','); // 返回 "通知,公告"
```

### 3. 动态字典加载

#### 组件中动态加载
```vue
<script setup>
import { useDict } from '@/utils/dict';

// 根据条件动态加载字典
const dictType = computed(() => {
  return userType.value === 'admin' ? 'sys_admin_status' : 'sys_user_status';
});

const { statusOptions } = useDict(dictType);
</script>
```

#### 异步加载示例
```javascript
// 异步加载字典数据
async function loadDynamicDict(dictType) {
  try {
    const response = await getDicts(dictType);
    const dictData = response.data.map(item => ({
      label: item.dictLabel,
      value: item.dictValue,
      elTagType: item.listClass,
      elTagClass: item.cssClass
    }));
    
    // 存储到缓存
    useDictStore().setDict(dictType, dictData);
    return dictData;
  } catch (error) {
    console.error('加载字典失败:', error);
    return [];
  }
}
```

## 新增自定义字典

### 1. 通过界面添加

#### 步骤一：新增字典类型
1. 登录系统，进入 `系统管理 → 字典管理`
2. 点击 `新增` 按钮
3. 填写字典信息：
   - **字典名称**：显示名称，如 "订单状态"
   - **字典类型**：唯一标识，如 "biz_order_status"  
   - **状态**：选择 "正常"
   - **备注**：功能说明

#### 步骤二：添加字典数据
1. 在字典类型列表中，点击字典类型链接进入数据管理
2. 点击 `新增` 按钮添加数据项：
   - **数据标签**：显示文本，如 "待支付"
   - **数据键值**：程序值，如 "1"
   - **显示排序**：排序号
   - **回显样式**：标签样式（primary、success、warning、danger、info）
   - **状态**：正常

### 2. 通过SQL脚本添加

```sql
-- 添加字典类型
INSERT INTO sys_dict_type VALUES 
(NULL, '订单状态', 'biz_order_status', '0', 'admin', NOW(), '', NULL, '电商订单状态管理');

-- 添加字典数据
INSERT INTO sys_dict_data VALUES 
(NULL, 1, '待支付', '1', 'biz_order_status', '', 'warning', 'N', '0', 'admin', NOW(), '', NULL, '订单待支付'),
(NULL, 2, '已支付', '2', 'biz_order_status', '', 'primary', 'N', '0', 'admin', NOW(), '', NULL, '订单已支付'),
(NULL, 3, '配货中', '3', 'biz_order_status', '', 'info', 'N', '0', 'admin', NOW(), '', NULL, '订单配货中'),
(NULL, 4, '已发货', '4', 'biz_order_status', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, '订单已发货'),
(NULL, 5, '已完成', '5', 'biz_order_status', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, '订单已完成'),
(NULL, 6, '已取消', '0', 'biz_order_status', '', 'danger', 'N', '0', 'admin', NOW(), '', NULL, '订单已取消');
```

### 3. 前端使用新字典

```vue
<template>
  <div>
    <!-- 订单状态选择 -->
    <el-select v-model="order.status">
      <el-option 
        v-for="dict in biz_order_status"
        :key="dict.value"
        :label="dict.label"
        :value="dict.value"
      />
    </el-select>
    
    <!-- 订单状态显示 -->
    <dict-tag :options="biz_order_status" :value="order.status" />
  </div>
</template>

<script setup>
const { biz_order_status } = useDict('biz_order_status');
</script>
```

## 高级特性

### 1. 样式定制

#### 预定义样式类型
- `primary`：主要状态（蓝色）
- `success`：成功状态（绿色）
- `warning`：警告状态（橙色）
- `danger`：危险状态（红色）
- `info`：信息状态（灰色）

#### 自定义CSS样式
```css
/* 在 dict_data 表的 css_class 字段中配置自定义类名 */
.custom-vip-tag {
  background: linear-gradient(45deg, #FFD700, #FFA500);
  color: #000;
  font-weight: bold;
  border: none;
}

.custom-urgent-tag {
  animation: blink 1s infinite;
  background-color: #ff4757;
  color: white;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.5; }
}
```

### 2. 缓存管理

#### 手动刷新缓存
```javascript
// 刷新指定字典类型的缓存
useDictStore().removeDict('sys_normal_disable');

// 清空所有字典缓存
useDictStore().cleanDict();

// 重新加载字典
const { sys_normal_disable } = useDict('sys_normal_disable');
```

#### 批量缓存刷新
```javascript
// 系统管理界面的"刷新缓存"功能
async function refreshAllDictCache() {
  try {
    await refreshCache(); // 调用后端接口
    useDictStore().cleanDict(); // 清空前端缓存
    ElMessage.success('字典缓存刷新成功');
  } catch (error) {
    ElMessage.error('字典缓存刷新失败');
  }
}
```

### 3. 条件过滤

#### 按状态过滤
```javascript
// 只获取启用状态的字典项
const enabledOptions = computed(() => {
  return sys_normal_disable.value?.filter(item => item.status === '0') || [];
});
```

#### 按业务条件过滤
```vue
<script setup>
// 根据用户角色显示不同的选项
const filteredOptions = computed(() => {
  const allOptions = sys_user_type.value || [];
  if (currentUser.role === 'admin') {
    return allOptions; // 管理员看到所有选项
  } else {
    return allOptions.filter(item => item.value !== 'admin'); // 普通用户不能选择管理员类型
  }
});
</script>
```

## 常见问题与解决方案

### 1. 字典数据不显示

**问题**：页面上字典数据显示为空或undefined
**原因**：
- 字典类型不存在
- 字典数据状态为停用
- 缓存未正确加载

**解决方案**：
```javascript
// 检查字典是否正确加载
const { sys_normal_disable } = useDict('sys_normal_disable');
console.log('字典数据:', sys_normal_disable.value);

// 添加防御性代码
const safeOptions = computed(() => {
  return sys_normal_disable.value || [];
});
```

### 2. 缓存不更新

**问题**：修改字典数据后前端显示未更新
**解决方案**：
```javascript
// 数据更新后清理缓存
async function updateDictData(data) {
  await updateData(data);
  // 清理相关缓存
  useDictStore().removeDict(data.dictType);
  // 重新加载
  useDict(data.dictType);
}
```

### 3. 性能问题

**问题**：大量字典数据导致页面加载慢
**解决方案**：
```javascript
// 1. 懒加载
const loadDictOnDemand = (dictType) => {
  return new Promise((resolve) => {
    if (useDictStore().getDict(dictType)) {
      resolve(useDictStore().getDict(dictType));
    } else {
      const { [dictType]: dictData } = useDict(dictType);
      watch(dictData, (newVal) => {
        if (newVal) resolve(newVal);
      }, { immediate: true });
    }
  });
};

// 2. 分页加载大字典
async function loadLargeDict(dictType, page = 1, size = 50) {
  const response = await listData({
    dictType,
    pageNum: page,
    pageSize: size
  });
  return response.rows;
}
```

### 4. 多语言支持

**问题**：需要支持多语言字典
**解决方案**：
```javascript
// 创建多语言字典类型
// sys_user_status_zh, sys_user_status_en

const getDictByLocale = (dictType, locale = 'zh') => {
  const localizedDictType = `${dictType}_${locale}`;
  return useDict(localizedDictType);
};

// 使用
const { sys_user_status } = getDictByLocale('sys_user_status', currentLocale.value);
```

## 最佳实践总结

### 1. 命名规范
- **统一前缀**：系统级用 `sys_`，业务级用 `biz_`，应用级用 `app_`
- **语义明确**：使用有意义的名称，避免缩写
- **层次分明**：按模块和功能分类

### 2. 数据设计
- **键值简洁**：使用数字或短字符串作为value
- **标签友好**：label使用用户友好的文本
- **排序合理**：按使用频率或业务重要性排序
- **样式恰当**：选择合适的标签样式

### 3. 使用模式
- **集中管理**：将字典使用集中在组件的setup部分
- **防御编程**：始终检查字典数据是否存在
- **性能优化**：合理使用缓存，避免重复加载
- **用户体验**：提供loading状态和错误处理

### 4. 维护策略
- **版本控制**：记录字典变更历史
- **影响评估**：变更前评估对现有功能的影响
- **测试覆盖**：确保字典相关功能有充分测试
- **文档更新**：及时更新字典使用文档

通过遵循这些最佳实践，可以充分发挥字典功能的优势，提高系统的可维护性和用户体验。