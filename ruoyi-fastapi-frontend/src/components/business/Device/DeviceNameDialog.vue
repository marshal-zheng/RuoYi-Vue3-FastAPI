<template>
  <el-dialog
    v-model="visible"
    title="编辑设备信息"
    width="500px"
    @close="onClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="设备名称" prop="deviceName">
        <el-input v-model="form.deviceName" placeholder="请输入设备名称" />
      </el-form-item>
      <el-form-item label="设备分类" prop="categoryName">
        <CategorySelector v-model="form.categoryName" placeholder="请选择设备分类" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup name="DeviceNameDialog">
import { ref, reactive, watch } from 'vue'
import { CategorySelector } from './selector'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  value: { 
    type: Object, 
    default: () => ({ deviceName: '', categoryName: '' })
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'close'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => visible.value = v)
watch(visible, (v) => emit('update:modelValue', v))

const formRef = ref()
const form = reactive({ 
  deviceName: props.value?.deviceName || '',
  categoryName: props.value?.categoryName || ''
})

watch(() => props.value, (v) => {
  if (v) {
    form.deviceName = v.deviceName || ''
    form.categoryName = v.categoryName || ''
  }
}, { deep: true })

const rules = {
  deviceName: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  categoryName: [{ required: true, message: '请选择设备分类', trigger: 'change' }]
}

function submit() {
  if (!formRef.value) return
  formRef.value.validate((valid) => {
    if (!valid) return
    emit('submit', { ...form })
  })
}

function closeDialog() {
  visible.value = false
}

function onClose() {
  formRef.value?.resetFields()
  emit('close')
}
</script>

<style lang="scss" scoped>
</style>