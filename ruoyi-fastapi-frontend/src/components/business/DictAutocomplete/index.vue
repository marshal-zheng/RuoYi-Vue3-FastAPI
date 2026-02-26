<template>
  <el-autocomplete
    v-model="inputValue"
    :fetch-suggestions="fetchSuggestions"
    value-key="label"
    @select="handleSelect"
    @input="handleInput"
    @blur="handleBlur"
    v-bind="$attrs"
  />
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { getDicts } from '@/api/system/dict/data';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  dictType: {
    type: String,
    required: true,
  },
  // 是否将字典标签转为大写展示（仅影响展示，不影响实际存储值）
  uppercaseLabel: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'change', 'dict-change']);

const allOptions = ref([]);
const lastOptions = ref([]);
const inputValue = ref('');

const loadDictData = async () => {
  if (!props.dictType) return;
  try {
    const response = await getDicts(props.dictType);
    const raw = Array.isArray(response) ? response : [];
    const dedupMap = {};
    raw.forEach((option) => {
      const baseLabel = option.dictLabel ?? option.dictValue ?? '';
      const key = String(baseLabel ?? option.dictValue ?? '').toLowerCase();
      if (!key) return;
      const isUppercase = String(baseLabel) === String(baseLabel).toUpperCase();
      const existing = dedupMap[key];
      if (!existing || (!existing.isUppercase && isUppercase)) {
        dedupMap[key] = {
          option,
          baseLabel,
          isUppercase,
        };
      }
    });
    allOptions.value = Object.values(dedupMap).map((item) => {
      const baseLabel = item.baseLabel;
      const label = props.uppercaseLabel ? String(baseLabel).toUpperCase() : baseLabel;
      return {
        label,
        value: item.option.dictValue,
        disabled: item.option.status === '1',
        _raw: item.option,
      };
    });
  } catch (_error) {
    allOptions.value = [];
  }
};

const fetchSuggestions = (queryString, cb) => {
  if (allOptions.value.length === 0) {
    loadDictData().then(() => {
      const results = filterOptions(queryString);
      cb(results);
    });
  } else {
    const results = filterOptions(queryString);
    cb(results);
  }
};

const filterOptions = (queryString) => {
  if (!queryString) {
    lastOptions.value = allOptions.value;
    return allOptions.value;
  }
  const k = String(queryString).toLowerCase();
  const filtered = allOptions.value.filter(
    (opt) =>
      String(opt.label).toLowerCase().includes(k) || String(opt.value).toLowerCase().includes(k)
  );
  lastOptions.value = filtered;
  return filtered;
};

const handleSelect = (item) => {
  console.log('itemsssss', item);
  inputValue.value = item.label;
  emitValue(item.value);
  emit('dict-change', item._raw ?? item);
};

const handleInput = (val) => {
  inputValue.value = val;
};

const isSameValue = (a, b) => String(a) === String(b);

const syncInputValue = () => {
  const target = allOptions.value.find((d) => isSameValue(d.value, props.modelValue));
  if (target) {
    inputValue.value = target.label;
    emitValue(props.modelValue, target.label);
  } else {
    inputValue.value = props.modelValue ?? '';
  }
};

const findOptionByLabel = (label) => {
  return allOptions.value.find(
    (opt) =>
      String(opt.label).toLowerCase() === String(label).toLowerCase() ||
      isSameValue(opt.value, label)
  );
};

const emitValue = (val, label = '') => {
  emit('update:modelValue', val);
  emit('change', { value: val, label });
};

const handleBlur = () => {
  if (!inputValue.value) {
    emitValue('');
    return;
  }
  const match = findOptionByLabel(inputValue.value);
  if (match) {
    inputValue.value = match.label;
    emitValue(match.value, match.label);
  } else {
    // 没有匹配的字典项时，直接使用用户输入的自定义值
    emitValue(inputValue.value, inputValue.value);
  }
};

watch(
  () => props.dictType,
  () => {
    allOptions.value = [];
    loadDictData().then(syncInputValue);
  },
  { immediate: true }
);

watch(
  () => props.modelValue,
  () => {
    syncInputValue();
  }
);

defineExpose({
  refresh: () => {
    allOptions.value = [];
    loadDictData();
  },
  getDictLabel: (value) => {
    const item = allOptions.value.find((d) => d.value === value);
    return item ? item.label : value;
  },
});
</script>
