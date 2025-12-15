<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    placeholder="选择指令类型"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from "vue";
import { commandTypeOptions } from "../eventOptions";

const props = defineProps({
  modelValue: {
    type: String,
    default: "self_check",
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const options = commandTypeOptions;

const handleChange = (value) => {
  emit("change", value);
};
</script>
