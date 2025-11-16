<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="500px"
    @close="onClose"
  >
    <el-form ref="portFormRef" :model="portForm" :rules="portFormRules" label-width="100px">
      <el-form-item label="总线类型" prop="interfaceType">
        <InterfaceTypeSelector
          v-model="portForm.interfaceType"
          @change="handleBusTypeChange"
        />
      </el-form-item>
      <el-form-item label="端口名称" prop="interfaceName">
        <el-input v-model="portForm.interfaceName" placeholder="请输入端口名称" />
      </el-form-item>
      <el-form-item label="端口位置" prop="position">
        <PositionSelector
          v-model="portForm.position"
          @change="handlePositionChange"
        />
      </el-form-item>
      <el-form-item label="端口描述" prop="description">
        <el-input
          v-model="portForm.description"
          type="textarea"
          :rows="3"
          placeholder="请输入端口描述"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="submitPort">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup name="PortEditDialog">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InterfaceTypeSelector, PositionSelector } from '@/views/fixing/components/selector'

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

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => visible.value = v)
watch(visible, (v) => emit('update:modelValue', v))

const portFormRef = ref()
const portForm = reactive({ ...props.value })

watch(() => props.value, (v) => {
  Object.assign(portForm, v || {})
}, { deep: true })

const portFormRules = {
  interfaceName: [{ required: true, message: '请输入端口名称', trigger: 'blur' }],
  interfaceType: [{ required: true, message: '请选择总线类型', trigger: 'change' }],
  position: [{ required: true, message: '请选择端口位置', trigger: 'change' }]
}

function generatePortName(busType, position) {
  portForm.interfaceName = busType || ''
}

function handleBusTypeChange(busType) {
  if (!portForm.interfaceId && busType) {
    generatePortName(busType, portForm.position)
  }
}

function handlePositionChange(position) {
  if (!portForm.interfaceId && portForm.interfaceType) {
    generatePortName(portForm.interfaceType, position)
  }
}

function submitPort() {
  if (!portFormRef.value) return
  portFormRef.value.validate((valid) => {
    if (!valid) return
    emit('submit', { ...portForm })
  })
}

function closeDialog() {
  visible.value = false
}

function onClose() {
  portFormRef.value?.resetFields()
  emit('close')
}
</script>

<style lang="scss" scoped>
</style>