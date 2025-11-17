<template>
  <ZxDialog
    v-bind="dialogProps"
    v-on="dialogEvents"
    @close="onDialogClose"
  >
    <el-form ref="portFormRef" :model="state.data" :rules="portFormRules" label-width="100px">
      <el-form-item label="总线类型" prop="interfaceType">
        <InterfaceTypeSelector v-model="state.data.interfaceType" @change="handleBusTypeChange" />
      </el-form-item>
      <el-form-item label="端口位置" prop="position">
        <PositionSelector v-model="state.data.position" @change="handlePositionChange" />
      </el-form-item>
      <el-form-item label="端口描述" prop="description">
        <el-input v-model="state.data.description" type="textarea" :rows="3" placeholder="请输入端口描述" />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup name="PortEditDialog">
import { ref, reactive, watch, computed } from 'vue'
import { useDialog } from '@zxio/zxui'
import { InterfaceTypeSelector, PositionSelector } from './selector'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '添加端口' },
  value: {
    type: Object,
    default: () => ({
      interfaceId: null,
      deviceId: null,
      interfaceName: '',
      interfaceType: 'RS422',
      position: 'right',
      description: ''
    })
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'close'])

const portFormRef = ref()

const portFormRules = {
  interfaceType: [{ required: true, message: '请选择总线类型', trigger: 'change' }],
  position: [{ required: true, message: '请选择端口位置', trigger: 'change' }]
}

function generatePortName(busType, position) {
  state.data.interfaceName = busType || ''
}

function handleBusTypeChange(busType) {
  if (!state.data.interfaceId && busType) {
    generatePortName(busType, state.data.position)
  }
}

function handlePositionChange(position) { }

const { dialogProps, dialogEvents, open, close, state } = useDialog({
  title: computed(() => props.title),
  width: '500px',
  okText: '确定',
  formRef: portFormRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({ ...props.value }),
  onConfirm: async (data) => {
    const submit = { ...data, interfaceName: data.interfaceType }
    emit('submit', submit)
    emit('update:modelValue', false)
    return submit
  },
  onConfirmError: (_e) => {}
})

watch(() => props.modelValue, (v) => {
  if (v) {
    Object.assign(state.data, { ...props.value })
    state.data.interfaceName = state.data.interfaceType
    open()
  } else {
    close()
  }
})

watch(() => props.value, (v) => {
  Object.assign(state.data, v || {})
}, { deep: true })

function onDialogClose() {
  portFormRef.value?.resetFields()
  emit('close')
  emit('update:modelValue', false)
  close()
}

defineExpose({ open, close })
</script>

<style lang="less" scoped>
</style>