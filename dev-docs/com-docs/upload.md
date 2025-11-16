# ZxUpload

文件上传组件,基于Element Plus Upload,增强UI和功能。

## 基础用法

```vue
<zx-upload
  v-model="fileList"
  action="/api/upload"
  :headers="{ Authorization: token }"
  @success="handleSuccess"
/>

<script setup>
const fileList = ref([])
const handleSuccess = (res) => {
  // res为服务器返回的数据
}
</script>
```

## 拖拽上传

```vue
<zx-upload
  v-model="fileList"
  action="/api/upload"
  :drag="true"
  main-text="将文件拖到此处"
  sub-text="或点击上传"
/>
```

## 文件限制

```vue
<zx-upload
  v-model="fileList"
  action="/api/upload"
  accept=".jpg,.png,.pdf"
  :limit="5"
  :max-size="10 * 1024 * 1024"
  :before-upload="beforeUpload"
/>

<script setup>
const beforeUpload = (file) => {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  return true
}
</script>
```

## 列表类型

```vue
<!-- text(默认) | picture | picture-card -->
<zx-upload
  v-model="fileList"
  action="/api/upload"
  list-type="picture-card"
/>
```

## 自定义文本

```vue
<zx-upload
  v-model="fileList"
  action="/api/upload"
  main-text="上传附件"
  sub-text="支持扩展名: .rar .zip .doc .docx .pdf"
  button-text="选择文件"
  tip-text="最多上传5个文件,每个不超过10MB"
/>
```

## 手动上传

```vue
<zx-upload
  v-model="fileList"
  action="/api/upload"
  :auto-upload="false"
/>

<zx-button @click="submitUpload">手动上传</zx-button>

<script setup>
const uploadRef = ref()
const submitUpload = () => {
  uploadRef.value?.submit()
}
</script>
```

## 关键Props

- `v-model`: 文件列表
- `action`: 上传地址(必需)
- `headers`: 请求头
- `data`: 额外参数
- `name`: 文件字段名,默认'file'
- `multiple`: 多选,默认false
- `accept`: 接受的文件类型,默认'*'
- `limit`: 最大文件数
- `max-size`: 单个文件最大尺寸(字节),默认10MB
- `list-type`: 列表类型 'text'|'picture'|'picture-card'
- `drag`: 拖拽上传,默认false
- `auto-upload`: 自动上传,默认true
- `show-file-list`: 显示文件列表,默认true
- `custom-file-list`: 自定义文件列表,默认false
- `allow-preview`: 允许预览,默认true
- `allow-download`: 允许下载,默认true
- `allow-remove`: 允许删除,默认true
- `before-upload`: 上传前钩子
- `before-remove`: 删除前钩子

## Events

- `@change`: 文件列表变化
- `@success`: 上传成功,参数 `(response, file, fileList)`
- `@error`: 上传失败
- `@progress`: 上传进度
- `@preview`: 预览文件
- `@remove`: 删除文件
- `@download`: 下载文件
- `@exceed`: 超过限制数量

