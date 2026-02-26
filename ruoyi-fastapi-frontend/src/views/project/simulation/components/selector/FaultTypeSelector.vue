<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    placeholder="选择故障类型"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from 'vue';
import { faultTypeOptions } from '../eventOptions';

const props = defineProps({
  modelValue: {
    type: String,
    default: 'packet_loss',
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const options = faultTypeOptions;

const handleChange = (value) => {
  emit('change', value);
};
</script>
