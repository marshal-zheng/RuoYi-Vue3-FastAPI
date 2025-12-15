<template>
  <zx-select
    v-model="selectedValue"
    :options="nodeOptions"
    :placeholder="placeholder"
    filterable
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  nodes: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: "选择设备",
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const nodeOptions = computed(() => {
  if (!props.nodes || props.nodes.length === 0) {
    return [];
  }
  return props.nodes.map((node) => ({
    value: node.id,
    label: node.data?.label || node.data?.name || node.label || node.id,
  }));
});

const handleChange = (value) => {
  emit("change", value);
};
</script>
