<template>
  <zx-select
    v-model="selectedValue"
    v-model:entity="selectedEntity"
    :options="loadOptions"
    @change="handleChange"
    @select="handleSelect"
    valueKey="protocolId"
    labelKey="protocolName"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { listProtocol } from '@/api/protocol/protocol';
import type { ProtocolRecord, ProtocolListQuery } from '@/api/protocol/protocol';
import type { SelectOption } from '@zxio/zxui';

const props = defineProps<{
  modelValue?: string | number | null;
  protocolType?: string;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: string | number | null];
  change: [value: string | number | null];
  'entity-change': [entity: ProtocolRecord | null];
  entity: [entity: ProtocolRecord | null];
}>();

const lastOptions = ref<ProtocolRecord[]>([]);
const selectedEntity = ref<SelectOption | SelectOption[] | null>(null);

const selectedValue = computed({
  get: () => props.modelValue ?? '',
  set: (val) => emit('update:modelValue', val),
});

const loadOptions = async () => {
  const queryParams: ProtocolListQuery = { page: 1, pageSize: 9999 };
  if (props.protocolType) {
    queryParams.protocolType = props.protocolType;
  }
  const response = await listProtocol(queryParams);
  const list = response?.items || [];
  lastOptions.value = list;
  return list;
};

const handleChange = (value: string | number | null) => {
  emit('change', value);
  const found = lastOptions.value.find((opt) => opt?.protocolId === value);
  if (found) {
    emit('entity-change', found);
    emit('entity', found);
  }
};

const handleSelect = (entity: SelectOption | SelectOption[] | null) => {
  const protocolId = entity && !Array.isArray(entity) ? entity.protocolId : null;
  const selected = lastOptions.value.find((option) => option.protocolId === protocolId) ?? null;
  emit('entity-change', selected);
  emit('entity', selected);
};

defineExpose({
  refresh: () => {
    lastOptions.value = [];
  },
  getLabel: (value: string | number) => {
    const item = lastOptions.value.find((d) => d?.protocolId === value);
    return item ? (item?.protocolName ?? value) : value;
  },
});
</script>
