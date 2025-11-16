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
      v-for="option in parityOptions"
      :key="option.value"
      :label="option.label"
      :value="option.value"
    />
  </el-select>
</template>

<script setup name="ParitySelector">
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: '请选择校验方式'
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

// 默认校验方式选项
const defaultParityOptions = [
  { label: '无校验(None)', value: 'None' },
  { label: '奇校验(Odd)', value: 'Odd' },
  { label: '偶校验(Even)', value: 'Even' },
  { label: '标记(Mark)', value: 'Mark' },
  { label: '空格(Space)', value: 'Space' }
]

// 计算校验方式选项
const parityOptions = computed(() => {
  return props.options || defaultParityOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>