<template>
  <zx-select
    :model-value="modelValue"
    :options="fileTypeOptions"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
    v-bind="$attrs"
    @update:model-value="handleChange"
  >
    <template #default="{ option }">
      <div class="file-type-option">
        <el-icon class="file-type-icon">
          <component :is="option.icon" />
        </el-icon>
        <span class="file-type-text">{{ option.label }}</span>
        <span class="file-type-ext">{{ option.extension }}</span>
      </div>
    </template>
  </zx-select>
</template>

<script setup name="FileTypeSelector">
import { computed } from 'vue';
import { Document, Grid, DocumentCopy } from '@element-plus/icons-vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: null,
  },
  placeholder: {
    type: String,
    default: '请选择文件类型',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  clearable: {
    type: Boolean,
    default: false,
  },
  size: {
    type: String,
    default: 'default',
  },
  customStyle: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Array,
    default: null,
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

// 默认文件类型选项
const defaultFileTypeOptions = [
  {
    label: 'Word 文档',
    value: 'word',
    extension: '.doc',
    icon: Document,
    description: 'Microsoft Word文档格式',
  },
  {
    label: 'Excel 表格',
    value: 'excel',
    extension: '.zip',
    icon: Grid,
    description: '导出附录Excel压缩包',
  },
  {
    label: 'XML 文件',
    value: 'xml',
    extension: '.xml',
    icon: DocumentCopy,
    description: '可扩展标记语言格式',
  },
];

// 计算文件类型选项 (返回函数供 zx-select 使用)
const fileTypeOptions = computed(() => {
  return async () => {
    const options = props.options || defaultFileTypeOptions;
    return options;
  };
});

function handleChange(value) {
  emit('update:modelValue', value);
  emit('change', value);
}
</script>

<style scoped>
.file-type-option {
  display: flex;
  align-items: center;
  width: 100%;
}

.file-type-icon {
  margin-right: 8px;
  color: var(--zx-semantic-accent-on-surface);
}

.file-type-text {
  flex: 1;
  font-size: 14px;
  color: var(--zx-semantic-text-primary);
}

.file-type-ext {
  font-size: 12px;
  color: var(--zx-semantic-text-secondary);
  margin-left: 8px;
}

:deep(.el-select-dropdown__item) {
  padding: 8px 20px;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: var(--zx-semantic-fill-accent-hover);
}

:deep(.el-select-dropdown__item.selected) {
  background-color: var(--zx-semantic-fill-selected);
  color: var(--zx-semantic-accent-on-surface);
}
</style>
