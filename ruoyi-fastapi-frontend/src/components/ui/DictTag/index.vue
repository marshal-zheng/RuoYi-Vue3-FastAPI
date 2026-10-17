<template>
  <span>
    <template v-for="item in displayItems" :key="item.value">
      <span v-if="!item.elTagType || item.elTagType === 'default'" :class="item.elTagClass"
        >{{ item.label }}
      </span>
      <el-tag
        v-else
        :disable-transitions="true"
        :type="tagType(item.elTagType)"
        :class="item.elTagClass"
        >{{ item.label }}
      </el-tag>
    </template>
  </span>
</template>
<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue';
import { queryScope } from '@/queries/context';

interface DictTagOption {
  readonly label: string;
  readonly value: string | number;
  readonly elTagType?: string;
  readonly elTagClass?: string;
}
const props = withDefaults(
  defineProps<{
    options?: readonly DictTagOption[];
    value?: string | number | readonly (string | number)[];
    showValue?: boolean;
    separator?: string;
  }>(),
  { options: () => [], showValue: true, separator: ',' }
);
function tagType(type?: string) {
  switch (type) {
    case 'primary':
    case 'success':
    case 'info':
    case 'warning':
    case 'danger':
      return type;
    default:
      return undefined;
  }
}

const values = computed(() =>
  props.value == null || props.value === ''
    ? []
    : Array.isArray(props.value)
      ? props.value.map(String)
      : String(props.value).split(props.separator)
);
// Display metadata for the selected values only; absence never proves invalidity.
const labels = shallowRef(new Map<string, DictTagOption>());
watch(
  () => [queryScope.value?.key, ...values.value],
  () => {
    labels.value = new Map();
  },
  { flush: 'sync' }
);
watch(
  () => [props.options, values.value],
  () => {
    const next = new Map(labels.value);
    for (const option of props.options ?? []) {
      if (values.value.includes(String(option.value))) next.set(String(option.value), option);
    }
    labels.value = next;
  },
  { immediate: true }
);
const displayItems = computed(() =>
  values.value.flatMap((value) => {
    const option =
      (props.options ?? []).find((item) => String(item.value) === value) ?? labels.value.get(value);
    return option ? [option] : props.showValue ? [{ value, label: value } as DictTagOption] : [];
  })
);
</script>
<style scoped>
.el-tag + .el-tag {
  margin-left: 10px;
}
</style>
