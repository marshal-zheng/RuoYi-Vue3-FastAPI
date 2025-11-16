<template>
  <el-dialog
    v-model="visible"
    title="导出项目"
    width="30%"
    append-to-body
    :before-close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="文件类型" prop="fileType">
        <FileTypeSelector
          v-model="form.fileType"
          placeholder="请选择文件类型"
          clearable
        />
      </el-form-item>
      
      <el-form-item label="文件名称" prop="fileName">
        <el-input
          v-model="form.fileName"
          placeholder="请输入文件名称"
          clearable
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取 消</el-button>
        <el-button type="primary" @click="handleExport" :loading="loading">
          <el-icon><Download /></el-icon>
          <span style="margin-left: 4px;">导 出</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup name="ExportDialog">
import { Download } from '@element-plus/icons-vue'
import { FileTypeSelector } from './selector'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  projectData: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'export'])

// Reactive data
const formRef = ref()
const loading = ref(false)

const form = reactive({
  fileType: 'xlsx',
  fileName: ''
})

const rules = {
  fileType: [
    { required: true, message: '请选择文件类型', trigger: 'change' }
  ],
  fileName: [
    { required: true, message: '请输入文件名称', trigger: 'blur' },
    { min: 1, max: 50, message: '文件名称长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// Computed
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Watch
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    // 弹框打开时，初始化表单数据
    initForm()
  }
})

// Methods
const initForm = () => {
  form.fileType = 'xlsx'
  form.fileName = props.projectData.projectName ? `${props.projectData.projectName}_导出` : '项目导出'
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const handleExport = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    loading.value = true
    
    // 构造导出参数
    const exportParams = {
      projectId: props.projectData.projectId,
      projectName: props.projectData.projectName,
      fileType: form.fileType,
      fileName: form.fileName
    }
    
    // 触发导出事件
    emit('export', exportParams)
    
    // 模拟导出过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 关闭弹框
    handleClose()
    
    // 显示成功消息
    ElMessage.success(`${form.fileName}.${form.fileType} 导出成功！`)
    
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    loading.value = false
  }
}

// 获取文件类型对应的图标
const getFileTypeIcon = (type) => {
  const iconMap = {
    doc: Document,
    xlsx: Grid,
    xml: DocumentCopy
  }
  return iconMap[type] || Document
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-radio) {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  margin-right: 0;
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: all 0.3s;
}

:deep(.el-radio:hover) {
  border-color: #409eff;
  background-color: #f0f9ff;
}

:deep(.el-radio.is-checked) {
  border-color: #409eff;
  background-color: #ecf5ff;
}

:deep(.el-radio__input) {
  margin-right: 8px;
}

:deep(.el-radio__label) {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

:deep(.el-checkbox) {
  margin-right: 20px;
  margin-bottom: 8px;
}
</style>