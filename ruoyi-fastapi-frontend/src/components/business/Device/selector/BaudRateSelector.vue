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
import { defaultSerialBaudRates, defaultCanBaudRates } from './options';
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null,
  },
  interfaceType: {
    type: String,
    default: 'serial', // 'serial' for RS422/RS485, 'can' for CAN
    validator: (value) => ['serial', 'can'].includes(value),
  },
  placeholder: {
    type: String,
    default: '请选择波特率',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'default',
  },
  customStyle: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Array,
    default: null,
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

// 默认波特率选项

// 计算波特率选项
const baudRateOptions = computed(() => {
  if (props.options) {
    return props.options;
  }

  return props.interfaceType === 'can' ? defaultCanBaudRates : defaultSerialBaudRates;
});

function handleChange(value) {
  emit('update:modelValue', value);
  emit('change', value);
}
</script>
