<template>
  <zx-select
    v-model="selectedValue"
    :options="options"
    placeholder="选择协议类型"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from "vue";
import { protocolTypeOptions } from "../eventOptions";

const props = defineProps({
  modelValue: {
    type: String,
    default: "LAN",
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

const options = protocolTypeOptions;

const handleChange = (value) => {
  emit("change", value);
};
</script>
