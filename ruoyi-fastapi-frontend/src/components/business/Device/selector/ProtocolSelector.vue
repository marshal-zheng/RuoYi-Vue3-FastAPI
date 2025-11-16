<template>
  <el-radio-group
    :model-value="modelValue"
    :disabled="disabled"
    :size="size"
    :style="customStyle"
    @update:model-value="handleChange"
  >
    <el-radio
      v-for="option in protocolOptions"
      :key="option.value"
      :label="option.value"
    >
      {{ option.label }}
    </el-radio>
  </el-radio-group>
</template>

<script setup name="ProtocolSelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default'
  },
  customStyle: {
    type: Object,
    default: () => ({})
  },
  options: {
    type: Array,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 默认协议类型选项
const defaultProtocolOptions = [
  { label: 'TCP', value: 'TCP' },
  { label: 'UDP', value: 'UDP' }
]

// 计算协议类型选项
const protocolOptions = computed(() => {
  return props.options || defaultProtocolOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>