<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    placeholder="选择日志级别"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from "vue";
import { logLevelOptions } from "../eventOptions";

const props = defineProps({
  modelValue: {
    type: String,
    default: "info",
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const options = logLevelOptions;

const handleChange = (value) => {
  emit("change", value);
};
</script>
