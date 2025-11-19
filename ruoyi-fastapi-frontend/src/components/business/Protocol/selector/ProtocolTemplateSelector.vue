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

interface Option {
  label: string;
  value: string | number;
  disabled?: boolean;
  _raw?: any;
}

const props = defineProps<{
  modelValue?: string | number | null;
  protocolType?: string;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: string | number | null];
  change: [value: string | number | null];
  'entity-change': [entity: any];
  entity: [entity: any];
}>();

const lastOptions = ref<Option[]>([]);
const selectedEntity = ref<any>(null);

const selectedValue = computed({
  get: () => props.modelValue ?? '',
  set: (val) => emit('update:modelValue', val),
});

const loadOptions = async (_keyword?: string) => {
  const queryParams: any = { pageNum: 1, pageSize: 9999 };
  if (props.protocolType) {
    queryParams.protocolType = props.protocolType;
  }
  const response: any = await listProtocol(queryParams);
  const list = response?.rows || [];
  lastOptions.value = list;
  return list;
};

const handleChange = (value: string | number | null) => {
  emit('change', value);
  const entity = selectedEntity.value;
  if (entity) {
    emit('entity-change', entity?._raw ?? entity);
    emit('entity', entity?._raw ?? entity);
    return;
  }
  const found = lastOptions.value.find((opt: any) => opt?.protocolId === value);
  if (found) {
    emit('entity-change', found);
    emit('entity', found);
  }
};

const handleSelect = (entity: any) => {
  emit('entity-change', entity);
  emit('entity', entity);
};

defineExpose({
  refresh: () => {
    lastOptions.value = [];
  },
  getLabel: (value: string | number) => {
    const item: any = lastOptions.value.find((d: any) => d?.protocolId === value);
    return item ? (item?.protocolName ?? value) : value;
  },
});
</script>
