<template>
  <ZxDialog
    v-bind="dialogProps"
    v-on="dialogEvents"
    @close="onDialogClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="设备名称" prop="deviceName">
        <el-input v-model="form.deviceName" placeholder="请输入设备名称" />
      </el-form-item>
      <el-form-item label="设备分类" prop="categoryName">
        <CategorySelector v-model="form.categoryName" placeholder="请选择设备分类" />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup name="DeviceNameDialog">
import { ref, reactive, watch } from 'vue'
import { useDialog } from '@zxio/zxui'
import { CategorySelector } from './selector'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  value: { 
    type: Object, 
    default: () => ({ deviceName: '', categoryName: '' })
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'close'])

const formRef = ref()
const form = reactive({
  deviceName: props.value?.deviceName || '',
  categoryName: props.value?.categoryName || ''
})

const rules = {
  deviceName: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  categoryName: [{ required: true, message: '请选择设备分类', trigger: 'change' }]
}

const { dialogProps, dialogEvents, open, close, state } = useDialog({
  title: '编辑设备信息',
  width: '500px',
  okText: '确定',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    deviceName: props.value?.deviceName || '',
    categoryName: props.value?.categoryName || ''
  }),
  onConfirm: async (data) => {
    emit('submit', { ...data })
    emit('update:modelValue', false)
    return data
  },
  onConfirmError: (_e) => {}
})

watch(() => props.modelValue, (v) => {
  if (v) {
    state.data.deviceName = props.value?.deviceName || ''
    state.data.categoryName = props.value?.categoryName || ''
    form.deviceName = state.data.deviceName
    form.categoryName = state.data.categoryName
    open()
  } else {
    close()
  }
})

watch(() => props.value, (v) => {
  if (v) {
    state.data.deviceName = v.deviceName || ''
    state.data.categoryName = v.categoryName || ''
    form.deviceName = state.data.deviceName
    form.categoryName = state.data.categoryName
  }
}, { deep: true })

function onDialogClose() {
  formRef.value?.resetFields()
  emit('close')
  emit('update:modelValue', false)
  close()
}
</script>

<style lang="less" scoped>
</style>