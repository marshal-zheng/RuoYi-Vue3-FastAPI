<template>
  <span class="dict-autocomplete">
    <el-autocomplete
      :key="identity"
      ref="autocomplete"
      v-model="inputValue"
      :fetch-suggestions="fetchSuggestions"
      value-key="label"
      v-bind="$attrs"
      @select="handleSelect"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    >
      <template #loading>
        <span>{{ query.isPaused.value ? '字典等待网络连接' : '正在加载字典…' }}</span>
      </template>
    </el-autocomplete>
    <span class="dict-autocomplete-status" aria-live="polite">
      <span v-if="query.isPaused.value">字典等待网络连接</span>
      <span v-else-if="query.isLoading.value">正在加载字典…</span>
      <span v-else-if="query.error.value" role="alert">
        {{ query.data.value ? '字典刷新失败' : '字典加载失败' }}
        <el-button link type="primary" @click="retry">重试</el-button>
      </span>
      <span v-else-if="query.isFetching.value">正在刷新字典…</span>
      <span v-else-if="editing && query.isSuccess.value && !filterOptions(inputValue).length">
        {{ inputValue ? '无匹配结果' : '暂无选项' }}
      </span>
    </span>
  </span>
</template>
<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue';
import { useDictQuery } from '@/queries/system/use-dict-query';
import { queryScope } from '@/queries/context';

defineOptions({ inheritAttrs: false });
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  dictType: { type: String, required: true },
  uppercaseLabel: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'change', 'dict-change']);
const { query, refresh, ensureFresh } = useDictQuery(() => props.dictType);
const autocomplete = ref();
const inputValue = ref('');
const editing = ref(false);
// Metadata for the one selected value, separate from the shared server options.
const selectedLabel = ref(null);
let suggestionGeneration = 0;
const identity = computed(() => `${queryScope.value?.key ?? ''}/${props.dictType}`);
const allOptions = computed(() => {
  const dedup = new Map();
  for (const option of query.data.value ?? []) {
    const baseLabel = String(option.label ?? option.value ?? '');
    const key = baseLabel.toLowerCase();
    if (!key) continue;
    const uppercase = baseLabel === baseLabel.toUpperCase();
    const previous = dedup.get(key);
    if (!previous || (!previous.uppercase && uppercase)) {
      dedup.set(key, {
        ...option,
        label: props.uppercaseLabel ? baseLabel.toUpperCase() : baseLabel,
        uppercase,
      });
    }
  }
  return [...dedup.values()];
});
const isSameValue = (a, b) => String(a) === String(b);
function filterOptions(text) {
  const term = String(text).toLowerCase();
  return allOptions.value.filter(
    (option) =>
      String(option.label).toLowerCase().includes(term) ||
      String(option.value).toLowerCase().includes(term)
  );
}
function fetchSuggestions(text, callback) {
  const generation = ++suggestionGeneration;
  const scope = identity.value;
  const deliver = () => {
    if (generation === suggestionGeneration && scope === identity.value)
      callback(filterOptions(text));
  };
  if (query.data.value === undefined && query.isFetching.value) {
    // Join the initial shared read; typing over loaded data only filters locally.
    void refresh().then(deliver, () => {
      if (generation === suggestionGeneration && scope === identity.value) callback([]);
    });
  } else {
    deliver();
  }
}
function syncInputValue() {
  if (editing.value) return;
  const option = allOptions.value.find((item) => isSameValue(item.value, props.modelValue));
  if (!option && selectedLabel.value && !isSameValue(selectedLabel.value.value, props.modelValue))
    selectedLabel.value = null;
  if (option)
    selectedLabel.value = {
      identity: identity.value,
      value: props.modelValue,
      label: option.label,
    };
  const known = selectedLabel.value;
  inputValue.value =
    option?.label ??
    (known?.identity === identity.value && isSameValue(known.value, props.modelValue)
      ? known.label
      : String(props.modelValue ?? ''));
}
function emitValue(value, label = '') {
  emit('update:modelValue', value);
  emit('change', { value, label });
}
function handleSelect(item) {
  suggestionGeneration++;
  inputValue.value = item.label;
  selectedLabel.value = { identity: identity.value, value: item.value, label: item.label };
  editing.value = false;
  emitValue(item.value, item.label);
  emit('dict-change', item._raw ?? item);
}
function handleInput(value) {
  suggestionGeneration++;
  editing.value = true;
  inputValue.value = value;
}
function handleFocus() {
  editing.value = true;
  void ensureFresh().catch(() => {
    /* Query state owns failures. */
  });
}
function handleBlur() {
  suggestionGeneration++;
  editing.value = false;
  const match = allOptions.value.find(
    (item) =>
      String(item.label).toLowerCase() === String(inputValue.value).toLowerCase() ||
      isSameValue(item.value, inputValue.value)
  );
  if (match) {
    inputValue.value = match.label;
    emitValue(match.value, match.label);
  } else {
    const known = selectedLabel.value;
    if (
      known?.identity === identity.value &&
      isSameValue(known.value, props.modelValue) &&
      String(known.label).toLowerCase() === String(inputValue.value).toLowerCase()
    ) {
      emitValue(props.modelValue, known.label);
    } else emitValue(inputValue.value, inputValue.value);
  }
}
function retry() {
  void refresh().catch(() => {
    /* Query state owns failures. */
  });
}
watch(identity, () => {
  suggestionGeneration++;
  selectedLabel.value = null;
  editing.value = false;
  inputValue.value = String(props.modelValue ?? '');
});
watch(
  () => props.modelValue,
  () => {
    suggestionGeneration++;
    editing.value = false;
    syncInputValue();
  }
);
watch(
  allOptions,
  () => {
    syncInputValue();
    if (editing.value) autocomplete.value?.getData?.(inputValue.value);
  },
  { immediate: true }
);
onBeforeUnmount(() => {
  suggestionGeneration++;
});
defineExpose({
  refresh,
  getDictLabel: (value) =>
    allOptions.value.find((item) => isSameValue(item.value, value))?.label ??
    (selectedLabel.value?.identity === identity.value &&
    isSameValue(selectedLabel.value.value, value)
      ? selectedLabel.value.label
      : value),
});
</script>
<style scoped>
.dict-autocomplete {
  display: inline-flex;
  flex-direction: column;
  width: 100%;
}
.dict-autocomplete-status {
  color: var(--zx-text-secondary);
  font-size: 12px;
}
</style>
