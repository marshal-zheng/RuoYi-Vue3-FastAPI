# vxe-table 下拉框选择后回显 [object Object] 问题

## 问题场景

- 在 vxe-table 中使用 `DictAutocomplete` 自定义渲染器作为单元格编辑组件。
- 从下拉框中选择一个字典项后，单元格显示 `[object Object]` 而不是正确的值。
- 涉及组件：`DictAutocomplete`、`VxeDictAutocomplete`、`main.ts` 渲染器。

## 原因分析

问题出在**三个组件之间的事件参数传递不匹配**：

### 数据流追踪

```
DictAutocomplete → VxeDictAutocomplete → main.ts 渲染器
```

1. **`DictAutocomplete` 组件的 emit**：
   ```javascript
   const emitValue = (val, label = '') => {
     emit('update:modelValue', val);      // ✅ 字符串，如 "UINT8"
     emit('change', { value: val, label }); // ⚠️ 对象！
   };
   ```

2. **`VxeDictAutocomplete` 包装组件的处理**（修复前）：
   ```javascript
   const handleChange = (val: any) => {
     emit('change', props.params, val);  // 传两个参数：params 在前，val 在后
   };
   ```

3. **`main.ts` 渲染器的处理**（修复前）：
   ```javascript
   const handleChange = (value: any) => {
     row[field] = normalizeValue(value) ?? '';  // ❌ value 接收的是第一个参数 params！
   };
   ```

### 问题根因

- `VxeDictAutocomplete` emit 时传递了 `(params, val)` **两个参数**
- `main.ts` 渲染器的 `handleChange` 只定义了**一个参数**
- JavaScript 中多余的参数会被丢弃，所以 `value = params`（配置对象）
- `params` 对象没有 `value` 属性，`normalizeValue` 直接返回整个对象
- 对象被赋值给 `row[field]`，显示时自动调用 `toString()` 变成 `[object Object]`

---

## 解决方案

提供两种修复方案，推荐使用方案二（标准化方案）。

### 方案一：防御性兼容（渲染器适配）

只修改 `main.ts` 渲染器，兼容两种参数传递方式。

**修改文件**：`src/main.ts`

```javascript
// 修复前
const handleInput = (value: string | number | undefined) => {
  row[field] = normalizeValue(value) ?? '';
  emitEvent('input', row[field]);
};

const handleChange = (value: any) => {
  row[field] = normalizeValue(value) ?? '';
  emitEvent('change', value);
};

// 修复后
const handleInput = (_paramsOrValue: any, val?: any) => {
  // 兼容两种情况：(params, val) 或 (val)
  const actualValue = val !== undefined ? val : _paramsOrValue;
  row[field] = normalizeValue(actualValue) ?? '';
  emitEvent('input', row[field]);
};

const handleChange = (_paramsOrValue: any, val?: any) => {
  const actualValue = val !== undefined ? val : _paramsOrValue;
  row[field] = normalizeValue(actualValue) ?? '';
  emitEvent('change', actualValue);
};
```

**优点**：
- 向后兼容，不影响其他组件
- 修改范围小

**缺点**：
- 隐含假设：两参数时，值在第二个位置
- 代码不够直观

---

### 方案二：标准化方案（推荐）

同时修改 `VxeDictAutocomplete` 和渲染器，遵循 Vue 组件常规约定。

**修改文件 1**：`src/components/VxeDictAutocomplete/index.vue`

```javascript
// 修复前
const handleChange = (val: any) => {
  emit('change', props.params, val);  // 传两个参数
};

const handleInput = (val: any) => {
  emit('input', props.params, val);
};

// 修复后 - 标准化：只传递实际值
const handleChange = (val: any) => {
  emit('change', val);
};

const handleInput = (val: any) => {
  emit('input', val);
};
```

**修改文件 2**：`src/main.ts`（渲染器简化为标准单参数处理）

```javascript
const handleInput = (value: any) => {
  row[field] = normalizeValue(value) ?? '';
  emitEvent('input', row[field]);
};

const handleChange = (value: any) => {
  row[field] = normalizeValue(value) ?? '';
  emitEvent('change', value);
};
```

**优点**：
- 符合 Vue 组件约定，emit 只传实际值
- 代码简洁，易于理解
- 可直接复用到其他项目

**缺点**：
- 需要修改两个文件

---

## 修复后的数据流

```
DictAutocomplete                    VxeDictAutocomplete              main.ts 渲染器
─────────────────                   ───────────────────              ──────────────
emit('change', { value, label })  →  handleChange(val)              →  handleChange(value)
                                     emit('change', val)                 ↓
                                                                      normalizeValue(value)
                                                                         ↓
                                                                      提取 value.value
                                                                         ↓
                                                                      row[field] = "UINT8" ✅
```

---

## 复用到其他项目

如果需要在其他项目中使用这套组件，需要复制以下文件：

| 文件 | 说明 |
|------|------|
| `src/components/DictAutocomplete/index.vue` | 字典自动完成组件 |
| `src/components/VxeDictAutocomplete/index.vue` | vxe-table 适配层 |
| `main.ts` 中的渲染器注册代码 | `VXETable.renderer.add('DictAutocomplete', {...})` |

确保使用**方案二（标准化方案）**的代码，以保证开箱即用。
