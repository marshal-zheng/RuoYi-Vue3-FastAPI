<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
    :style="customStyle"
    @update:model-value="handleChange"
  >
    <el-option
      v-for="option in baudRateOptions"
      :key="option.value"
      :label="option.label"
      :value="option.value"
    />
  </el-select>
</template>

<script setup name="BaudRateSelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null
  },
  interfaceType: {
    type: String,
    default: 'serial', // 'serial' for RS422/RS485, 'can' for CAN
    validator: (value) => ['serial', 'can'].includes(value)
  },
  placeholder: {
    type: String,
    default: '请选择波特率'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
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

// 默认波特率选项
const defaultSerialBaudRates = [
  { label: '9600 bps', value: 9600 },
  { label: '19200 bps', value: 19200 },
  { label: '38400 bps', value: 38400 },
  { label: '57600 bps', value: 57600 },
  { label: '115200 bps', value: 115200 },
  { label: '230400 bps', value: 230400 },
  { label: '460800 bps', value: 460800 },
  { label: '921600 bps', value: 921600 }
]

const defaultCanBaudRates = [
  { label: '5 Kbps', value: 5000 },
  { label: '10 Kbps', value: 10000 },
  { label: '20 Kbps', value: 20000 },
  { label: '50 Kbps', value: 50000 },
  { label: '100 Kbps', value: 100000 },
  { label: '125 Kbps', value: 125000 },
  { label: '250 Kbps', value: 250000 },
  { label: '500 Kbps', value: 500000 },
  { label: '800 Kbps', value: 800000 },
  { label: '1 Mbps', value: 1000000 }
]

// 计算波特率选项
const baudRateOptions = computed(() => {
  if (props.options) {
    return props.options
  }
  
  return props.interfaceType === 'can' ? defaultCanBaudRates : defaultSerialBaudRates
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>