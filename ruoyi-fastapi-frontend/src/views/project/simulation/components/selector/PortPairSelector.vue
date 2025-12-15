<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    :placeholder="placeholder"
    clearable
    filterable
    :loading="loading"
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
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: "源/目标端口",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const handleChange = (value) => {
  emit("change", value);
};
</script>
