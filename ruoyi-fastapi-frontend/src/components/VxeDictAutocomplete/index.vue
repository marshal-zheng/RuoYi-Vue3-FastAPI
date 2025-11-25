<template>
  <dict-autocomplete
    v-if="dictType"
    v-model="cellValue"
    :dict-type="dictType"
    :placeholder="placeholder"
    :clearable="clearable"
    :disabled="disabled"
    style="width: 100%"
  />
  <el-input
    v-else
    v-model="cellValue"
    :type="inputType"
    :placeholder="placeholder"
    :disabled="disabled"
    style="width: 100%"
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

const dictType = computed(() => props.params?.dictType || '');
const placeholder = computed(() => props.params?.placeholder || '请输入');
const clearable = computed(() => props.params?.clearable !== false);
const disabled = computed(() => props.params?.disabled || false);
const inputType = computed(() => props.params?.inputType || 'text');

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
</script>
