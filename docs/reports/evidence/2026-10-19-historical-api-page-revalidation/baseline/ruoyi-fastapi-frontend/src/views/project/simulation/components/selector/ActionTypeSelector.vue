<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    placeholder="选择动作类型"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from 'vue';
import { actionTypeOptions } from '../eventOptions';

const props = defineProps({
  modelValue: {
    type: String,
    default: 'send_command',
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const options = actionTypeOptions;

const handleChange = (value) => {
  emit('change', value);
};
</script>
