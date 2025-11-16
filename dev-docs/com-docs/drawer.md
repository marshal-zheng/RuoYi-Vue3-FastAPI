# ZxDrawer & useDrawer

抽屉组件及Composable函数。**重点是useDrawer的使用**。

## useDrawer核心用法(推荐)

```ts
import { useDrawer } from '@zxio/hooks'

// 定义数据类型
interface UserForm {
  name: string
  email: string
}

// 创建drawer实例
const userDrawer = useDrawer<UserForm>({
  title: '编辑用户',
  size: 600,
  defaultData: () => ({ name: '', email: '' }),
  
  // 确认回调
  async onConfirm(data) {
    await api.updateUser(data)
    return true  // 返回true自动关闭,返回false阻止关闭
  },
  
  // 表单验证
  formRef: toRef(() => formRef.value),
  preValidate: true,
  autoResetForm: true
})

// 模板中使用
<zx-drawer v-bind="userDrawer.drawerProps" v-on="userDrawer.drawerEvents">
  <el-form ref="formRef" :model="userDrawer.state.data">
    <el-form-item label="姓名" prop="name">
      <el-input v-model="userDrawer.state.data.name" />
    </el-form-item>
  </el-form>
</zx-drawer>

// 打开drawer
userDrawer.open({ name: 'Tom', email: 'tom@example.com' })
```

## useDrawer API

### 创建实例

```ts
const drawer = useDrawer<T>(options)
```

### Options配置

```ts
{
  title: string | ((data) => string),    // 标题
  size: string | number,                 // 宽度,默认'50%'
  placement: 'left' | 'right',           // 方向,默认'right'
  
  // 按钮配置
  okText: '确定',
  cancelText: '取消',
  showContinue: false,
  
  // 数据管理
  defaultData: () => T,                  // 默认数据
  dataTransform: (raw) => T,             // 数据转换
  
  // 回调
  async onConfirm(data, result) {        // 确认回调
    // 业务逻辑
    return true/false  // true自动关闭,false阻止
  },
  onCancel(data) {},
  onOpen(data) {},
  onClose(data) {},
  
  // 表单增强
  formRef: ref,                          // 表单引用
  formModel: ref,                        // 表单数据
  preValidate: true,                     // 确认前验证
  autoResetForm: true,                   // 关闭时重置
  autoScrollToError: true,               // 滚动到错误
}
```

### 返回值API

```ts
drawer.open(data?, title?)        // 打开drawer
drawer.close()                    // 关闭drawer
drawer.state.data                 // 访问数据
drawer.updateField(key, value)    // 更新字段
drawer.updateData(partial)        // 批量更新
drawer.setTitle(title)            // 设置标题
drawer.setLoading(bool)           // 设置loading
```

## 直接使用组件

```vue
<zx-drawer
  v-model="visible"
  title="标题"
  :size="600"
  placement="right"
  :confirm="handleConfirm"
  :form-ref="formRef"
>
  <el-form ref="formRef">
    <!-- 表单内容 -->
  </el-form>
</zx-drawer>
```

## 关键Props

- `visible/v-model`: 显示控制
- `title`: 标题
- `size`: 宽度
- `placement`: 方向 'left'|'right'|'top'|'bottom'
- `confirm`: 确认回调函数
- `form-ref`: 表单引用,自动验证
- `pre-validate`: 确认前验证,默认true
- `draggable`: 可拖拽,默认true
- `show-full-screen`: 显示全屏按钮,默认true

## Context对象

confirm回调接收context参数:

```ts
async confirm(context) {
  context.close()          // 手动关闭
  context.isFullScreen     // 是否全屏
}
```

