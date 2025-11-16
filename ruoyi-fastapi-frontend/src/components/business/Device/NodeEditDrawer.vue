<template>
  <el-drawer
    v-model="visible"
    title="编辑节点"
    :size="500"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="节点名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入节点名称"
          clearable
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="设备类型">
        <el-input v-model="formData.deviceType" disabled />
      </el-form-item>

      <el-form-item label="设备型号">
        <el-input v-model="formData.model" disabled />
      </el-form-item>

      <el-form-item label="制造商">
        <el-input v-model="formData.manufacturer" disabled />
      </el-form-item>

      <el-form-item label="版本">
        <el-input v-model="formData.version" disabled />
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="formData.remark" disabled type="textarea" :rows="3" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  nodeData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

// 控制显示/隐藏
const visible = ref(false)
const formRef = ref(null)
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  deviceType: '',
  model: '',
  manufacturer: '',
  version: '',
  remark: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
    if (newVal && props.nodeData) {
      // 打开时初始化表单数据
      initFormData()
    }
  },
  { immediate: true }
)

// 监听 visible 变化，同步到父组件
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 初始化表单数据
const initFormData = () => {
  nextTick(() => {
    const data = props.nodeData?.data || {}
    formData.name = data.name || data.label || ''
    formData.deviceType = data.deviceType || ''
    formData.model = data.model || ''
    formData.manufacturer = data.manufacturer || ''
    formData.version = data.version || ''
    formData.remark = data.remark || data.value || ''
    
    // 清除验证状态
    if (formRef.value) {
      formRef.value.clearValidate()
    }
  })
}

// 关闭抽屉
const handleClose = () => {
  visible.value = false
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    // 验证表单
    await formRef.value.validate()
    
    submitLoading.value = true
    
    // 触发提交事件，传递节点数据和修改后的名称
    emit('submit', {
      nodeId: props.nodeData?.id,
      node: props.nodeData,
      name: formData.name
    })
    
    ElMessage.success('保存成功')
    handleClose()
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-drawer__body) {
  padding: 20px;
}

:deep(.el-drawer__footer) {
  padding: 16px 20px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>

