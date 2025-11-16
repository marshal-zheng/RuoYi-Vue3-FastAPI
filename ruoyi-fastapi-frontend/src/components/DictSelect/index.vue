<template>
  <zx-select
    v-model="selectedValue"
    v-model:entity="selectedEntity"
    :options="loadOptions"
    @change="handleChange"
    v-bind="$attrs"
  />
</template>

<script setup>
import { ref, computed } from 'vue';
import { getDicts } from '@/api/system/dict/data';

const props = defineProps({
  modelValue: {
    type: [String, Number, Array],
    default: '',
  },
  dictType: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['update:modelValue', 'change', 'dict-change']);

const lastOptions = ref([]);
const selectedEntity = ref(null);

const selectedValue = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val),
});

const loadOptions = async keyword => {
  if (!props.dictType) return [];
  try {
    const response = await getDicts(props.dictType);
    const raw = Array.isArray(response?.data) ? response.data : [];
    let mapped = raw.map(option => ({
      label: option.dictLabel,
      value: option.dictValue,
      disabled: option.status === '1',
      _raw: option,
    }));
    if (keyword) {
      const k = String(keyword).toLowerCase();
      mapped = mapped.filter(opt => String(opt.label).toLowerCase().includes(k));
    }
    lastOptions.value = mapped;
    return mapped;
  } catch (_error) {
    lastOptions.value = [];
    return [];
  }
};

const handleChange = value => {
  emit('change', value);
  const entity = selectedEntity.value;
  if (entity) {
    emit('dict-change', entity?._raw ?? entity);
    return;
  }
  const selectedItem = Array.isArray(value)
    ? lastOptions.value
        .filter(opt => value.includes(opt.value))
        .map(opt => opt._raw ?? opt)
    : (lastOptions.value.find(opt => opt.value === value)?._raw ?? null);
  if (selectedItem) emit('dict-change', selectedItem);
};

defineExpose({
  refresh: () => {
    lastOptions.value = [];
  },
  getDictLabel: value => {
    const item = lastOptions.value.find(d => d.value === value);
    return item ? item.label : value;
  },
});
</script>
