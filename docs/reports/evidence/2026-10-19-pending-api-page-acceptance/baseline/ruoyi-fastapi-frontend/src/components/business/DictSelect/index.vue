<template>
  <zx-select
    :key="`${queryScope?.key ?? 'signed-out'}/${props.dictType}`"
    v-model="selectedValue"
    v-model:entity="selectedEntity"
    v-bind="{ ...$attrs, ...selectProps, options: displayOptions }"
    filterable
    remote
    v-on="selectEvents"
    @search="keyword = $event"
    @change="handleChange"
  >
    <template #empty>{{ keyword ? '无匹配结果' : '暂无选项' }}</template>
    <template #error="{ hasData, retry }">
      <span role="alert">{{ hasData ? '字典刷新失败' : '字典加载失败' }}</span>
      <el-button link type="primary" @click="retry">重试</el-button>
    </template>
    <template #status="{ paused, refreshing, loading }">
      <span v-if="paused">字典等待网络连接</span>
      <span v-else-if="refreshing">正在刷新字典…</span>
      <span v-else-if="loading">正在加载字典…</span>
    </template>
  </zx-select>
</template>
<script setup>
import { ref, computed, watch } from 'vue';
import { useQuerySelect } from '@zxio/vue-query/ui';
import { dictOptions } from '@/queries/system/dict';
import { queryScope } from '@/queries/context';

defineOptions({ inheritAttrs: false });
const props = defineProps({
  modelValue: { type: [String, Number, Array], default: '' },
  dictType: { type: String, required: true },
  active: { type: Boolean, default: true },
  valueType: { type: String, default: 'string' },
});
const emit = defineEmits(['update:modelValue', 'change', 'dict-change']);
const selectedEntity = ref(null);
const keyword = ref('');
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});
const { query, selectProps, selectEvents, refresh } = useQuerySelect(
  () => dictOptions(queryScope.value, props.dictType),
  { active: () => props.active }
);
const allOptions = computed(() =>
  props.valueType === 'number'
    ? (query.data.value ?? []).map((option) => ({ ...option, value: Number(option.value) }))
    : (query.data.value ?? [])
);
const displayOptions = computed(() => {
  const term = keyword.value.toLowerCase();
  return term
    ? allOptions.value.filter((option) => String(option.label).toLowerCase().includes(term))
    : allOptions.value;
});
watch(
  () => [queryScope.value?.key, props.dictType],
  () => {
    selectedEntity.value = null;
    keyword.value = '';
  }
);
function handleChange(value) {
  emit('change', value);
  const selected = Array.isArray(value)
    ? allOptions.value.filter((option) => value.includes(option.value)).map((option) => option._raw)
    : allOptions.value.find((option) => option.value === value)?._raw;
  if (selected) emit('dict-change', selected);
}
defineExpose({
  refresh,
  getDictLabel: (value) => allOptions.value.find((item) => item.value === value)?.label ?? value,
});
</script>
