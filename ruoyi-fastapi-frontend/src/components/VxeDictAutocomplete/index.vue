<template>
  <dict-autocomplete
    v-if="dictType"
    v-model="cellValue"
    :dict-type="dictType"
    :placeholder="placeholder"
    :uppercase-label="uppercaseLabel"
    :clearable="clearable"
    :disabled="disabled"
    style="width: 100%"
    @change="handleChange"
  />
  <el-input
    v-else
    v-model="cellValue"
    :type="inputType"
    :placeholder="placeholder"
    :disabled="disabled"
    style="width: 100%"
    @input="handleInput"
    @change="handleChange"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElInput } from 'element-plus';
import DictAutocomplete from '@/components/DictAutocomplete/index.vue';

const props = defineProps({
  params: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['change', 'input']);

const dictType = computed(() => props.params?.dictType || '');
const placeholder = computed(() => props.params?.placeholder || '请输入');
const clearable = computed(() => props.params?.clearable !== false);
const disabled = computed(() => props.params?.disabled || false);
const inputType = computed(() => props.params?.inputType || 'text');
const uppercaseLabel = computed(() => props.params?.uppercaseLabel === true);

const cellValue = computed({
  get() {
    const { row, column } = props.params || {};
    return row?.[column?.field] ?? '';
  },
  set(val) {
    const { row, column } = props.params || {};
    if (row && column) {
      row[column.field] = val;
    }
  },
});

// 触发 change 事件，将值同步到父组件
// 标准化：只传递实际值，符合 Vue 组件常规约定
const handleChange = (val: any) => {
  emit('change', val);
};

// 触发 input 事件
const handleInput = (val: any) => {
  emit('input', val);
};
</script>
