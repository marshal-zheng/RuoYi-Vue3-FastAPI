<template>
  <zx-select
    v-model="value"
    remote
    :options="loadTableNames"
    :placeholder="placeholder"
    v-bind="$attrs"
  />
</template>

<script setup>
import { getTableNames } from '@/api/common';

const props = defineProps({
  modelValue: [String, Number],
  placeholder: {
    type: String,
    default: '表名',
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

// zx-select 的 remote 模式支持传入返回 Promise 的函数
const loadTableNames = async () => {
  try {
    const response = await getTableNames();
    return response || [];
  } catch (error) {
    console.error('获取表名列表失败:', error);
    return [];
  }
};

const value = computed({
  get: () => props.modelValue,
  set: (v) => {
    emit('update:modelValue', v);
    emit('change', v);
  },
});
</script>
