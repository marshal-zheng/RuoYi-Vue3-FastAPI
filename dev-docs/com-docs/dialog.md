# ZxDialog & useDialog

对话框组件及Composable函数。**重点是useDialog的使用**。

## useDialog核心用法(推荐)

```ts
import { useDialog } from '@zxio/hooks'

// 定义数据类型
interface UserForm {
  name: string
  email: string
}

// 创建dialog实例
const userDialog = useDialog<UserForm>({
  title: '编辑用户',
  width: 600,
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
<zx-dialog v-bind="userDialog.dialogProps" v-on="userDialog.dialogEvents">
  <el-form ref="formRef" :model="userDialog.state.data">
    <el-form-item label="姓名" prop="name">
      <el-input v-model="userDialog.state.data.name" />
    </el-form-item>
  </el-form>
</zx-dialog>

// 打开dialog
userDialog.open({ name: 'Tom', email: 'tom@example.com' })
```

## useDialog API

### 创建实例

```ts
const dialog = useDialog<T>(options)
```

### Options配置

```ts
{
  title: string | ((data) => string),    // 标题
  width: string | number,                // 宽度,默认'50%'
  height: string | number,               // 高度
  
  // 按钮配置
  okText: '确定',
  cancelText: '取消',
  showCancel: true,
  showContinue: false,
  
  // 数据管理
  defaultData: () => T,                  // 默认数据
  dataTransform: (raw) => T,             // 数据转换
  
  // 回调
  async onConfirm(data) {                // 确认回调
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
  
  // 样式
  dialogSize: 'small' | 'large',
  noContentPadding: false,
  draggable: true,
}
```

### 返回值API

```ts
dialog.open(data?, title?)        // 打开dialog
dialog.close()                    // 关闭dialog
dialog.state.data                 // 访问数据
dialog.updateField(key, value)    // 更新字段
dialog.updateData(partial)        // 批量更新
dialog.setTitle(title)            // 设置标题
dialog.setLoading(bool)           // 设置loading
dialog.setDisabled(bool)          // 设置禁用
```

## 直接使用组件

```vue
<zx-dialog
  v-model="visible"
  title="标题"
  :width="600"
  :confirm="handleConfirm"
  :form-ref="formRef"
>
  <el-form ref="formRef">
    <!-- 表单内容 -->
  </el-form>
</zx-dialog>
```

## 关键Props

- `v-model`: 显示控制
- `title`: 标题
- `width/height`: 尺寸
- `confirm`: 确认回调函数
- `form-ref`: 表单引用,自动验证
- `pre-validate`: 确认前验证,默认true
- `draggable`: 可拖拽,默认true
- `footer`: 是否显示底部,默认true
- `loading`: 加载状态
- `loading-type`: 加载类型 'spin'|'skeleton'
- `enable-steps`: 启用步骤模式
- `current-step/total-steps`: 步骤配置

