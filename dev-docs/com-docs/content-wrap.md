# ZxContentWrap

内容包裹组件,提供标题、底部操作栏、表单验证、步骤导航等功能。

## 基础用法

```vue
<zx-content-wrap 
  title="页面标题"
  :show-footer="true"
  :is-edit="true"
  @save="handleSave"
  @cancel="handleCancel"
>
  <!-- 内容区域 -->
</zx-content-wrap>
```

## 表单验证模式

```vue
<zx-content-wrap
  title="编辑用户"
  :show-footer="true"
  :validate-form="true"
  :form-ref="formRef"
  @save="handleSave"
>
  <el-form ref="formRef" :model="form">
    <el-form-item label="姓名" prop="name" :rules="[{required: true}]">
      <el-input v-model="form.name" />
    </el-form-item>
  </el-form>
</zx-content-wrap>

<script setup>
const formRef = ref()
const form = reactive({ name: '' })

const handleSave = async ({ isValid, formRef }) => {
  // isValid为true表示验证通过
  await api.save(form)
}
</script>
```

## 步骤导航模式

```vue
<zx-content-wrap
  :enable-steps="true"
  :current-step="currentStep"
  :total-steps="3"
  @next="handleNext"
  @prev="handlePrev"
  @save="handleSubmit"
>
  <component :is="stepComponents[currentStep - 1]" />
</zx-content-wrap>
```

## 自定义按钮

```vue
<zx-content-wrap
  :buttons="customButtons"
  @button-click="handleButtonClick"
>
  <!-- 内容 -->
</zx-content-wrap>

<script setup>
const customButtons = [
  { key: 'export', text: '导出', icon: 'Download', type: 'default' },
  { key: 'save', text: '保存', type: 'primary' }
]
</script>
```

## 关键Props

- `title`: 标题
- `message`: 标题旁的提示信息
- `show-footer`: 显示底部操作栏,默认false
- `footer-fixed`: 底部固定定位,默认true
- `loading`: 加载状态
- `is-edit`: 编辑模式,影响保存按钮文案
- `save-text/cancel-text`: 按钮文案
- `validate-form`: 保存前验证表单,默认false
- `form-ref`: 表单引用
- `before-save`: 保存前钩子
- `after-save`: 保存后钩子
- `buttons`: 自定义按钮配置数组
- `button-align`: 按钮对齐 'left'|'center'|'right'
- `enable-steps`: 启用步骤模式
- `current-step/total-steps`: 步骤配置
- `content-padding`: 内容区padding,默认'20px'
- `scroll-offset`: 滚动偏移量配置
- `enable-keyboard-shortcuts`: 启用快捷键,默认true

## Events

- `@save`: 保存事件,参数 `{ isValid, formRef, isEdit }`
- `@cancel`: 取消事件
- `@save-start`: 保存开始,参数 `(done, fail)`
- `@save-success`: 保存成功
- `@save-error`: 保存失败
- `@next`: 下一步,参数 `{ currentStep, totalSteps, targetStep }`
- `@prev`: 上一步,参数同上
- `@button-click`: 自定义按钮点击,参数 `buttonKey`

## Slots

- `default`: 内容区域
- `title`: 自定义标题
- `extra`: 标题右侧额外内容
- `actions`: 底部操作按钮区域
- `icon`: 标题图标

## 快捷键

- `Ctrl+S` / `Cmd+S`: 保存
- `Escape`: 取消

