<template>
  <span class="dict-status" aria-live="polite">
    <template v-for="entry in entries" :key="entry.type">
      <span v-if="entry.query.isPaused.value">字典等待网络连接</span>
      <span v-else-if="entry.query.isLoading.value">正在加载字典…</span>
      <span v-else-if="entry.query.error.value" role="alert">
        {{ entry.query.data.value ? '字典刷新失败' : '字典加载失败' }}
        <el-button link type="primary" @click="retry(entry)">重试</el-button>
      </span>
      <span v-else-if="entry.query.isFetching.value">正在刷新字典…</span>
    </template>
  </span>
</template>
<script setup lang="ts">
import { computed, nextTick, type Ref } from 'vue';
import { useDictQuery } from '@/queries/system/use-dict-query';

interface NativeDictState {
  isEnabled: Readonly<Ref<boolean>>;
  isPaused: Readonly<Ref<boolean>>;
  isLoading: Readonly<Ref<boolean>>;
  isFetching: Readonly<Ref<boolean>>;
  data: Readonly<Ref<unknown>>;
  error: Readonly<Ref<unknown>>;
  refetch: (options: { cancelRefetch: boolean; throwOnError: boolean }) => Promise<unknown>;
}
const props = defineProps<{ types?: readonly string[]; queries?: readonly NativeDictState[] }>();
// The consuming setup declares its fixed resource types, just like useDict(...types).
const fixedEntries = [...new Set(props.types ?? [])].map((type) => ({
  type,
  ...useDictQuery(type),
}));
const entries = computed(() => [
  ...fixedEntries,
  ...(props.queries ?? []).map((query, index) => ({
    type: `metadata-${index}`,
    query,
    refresh: async () => {
      await nextTick();
      if (query.isEnabled.value) await query.refetch({ cancelRefetch: false, throwOnError: true });
    },
  })),
]);
function retry(entry: (typeof entries.value)[number]): void {
  void entry.refresh().catch(() => {
    /* The same observer presents the retry failure. */
  });
}
</script>
<style scoped>
.dict-status {
  color: var(--zx-text-secondary);
  font-size: 12px;
}
.dict-status > span + span {
  margin-inline-start: 8px;
}
</style>
