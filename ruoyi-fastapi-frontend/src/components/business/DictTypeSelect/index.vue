<template>
  <zx-select
    :key="queryScope?.key ?? 'signed-out'"
    v-model="selectedValue"
    v-bind="{ ...$attrs, ...selectProps, options: displayOptions }"
    filterable
    remote
    v-on="selectEvents"
    @search="keyword = $event"
    @change="emit('change', $event)"
  >
    <template #option="{ option }">
      <span class="flex items-center justify-between gap-3">
        <span>{{ option.label }}</span>
        <span class="text-zx-text-secondary">{{ option.value }}</span>
      </span>
    </template>
    <template #empty>{{ keyword ? '无匹配结果' : '暂无选项' }}</template>
    <template #error="{ hasData, retry }">
      <span role="alert">{{ hasData ? '字典类型刷新失败' : '字典类型加载失败' }}</span>
      <el-button link type="primary" @click="retry">重试</el-button>
    </template>
    <template #status="{ paused, refreshing, loading }">
      <span v-if="paused">字典类型等待网络连接</span>
      <span v-else-if="refreshing">正在刷新字典类型…</span>
      <span v-else-if="loading">正在加载字典类型…</span>
    </template>
  </zx-select>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuerySelect } from '@zxio/vue-query/ui';
import { dictTypeOptions } from '@/queries/system/dict';
import { queryScope } from '@/queries/context';

defineOptions({ inheritAttrs: false });
const props = withDefaults(defineProps<{ modelValue?: string; active?: boolean }>(), {
  active: true,
});
const emit = defineEmits<{
  'update:modelValue': [value: string | undefined];
  change: [value: string | undefined];
}>();
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value: string | undefined) => emit('update:modelValue', value),
});
const keyword = ref('');
const { selectProps, selectEvents, refresh } = useQuerySelect(
  () => dictTypeOptions(queryScope.value),
  { active: () => props.active }
);
const displayOptions = computed(() => {
  const term = keyword.value.toLowerCase();
  const options = selectProps.value.options;
  return term
    ? options.filter((option) => `${option.label} ${option.value}`.toLowerCase().includes(term))
    : options;
});
watch(queryScope, () => {
  keyword.value = '';
});
defineExpose({ refresh });
</script>
