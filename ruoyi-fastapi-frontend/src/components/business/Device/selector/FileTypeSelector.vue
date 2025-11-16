<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    :size="size"
    :style="customStyle"
    @update:model-value="handleChange"
  >
    <el-option
      v-for="option in fileTypeOptions"
      :key="option.value"
      :label="option.label"
      :value="option.value"
    >
      <div class="file-type-option">
        <el-icon class="file-type-icon">
          <component :is="option.icon" />
        </el-icon>
        <span class="file-type-text">{{ option.label }}</span>
        <span class="file-type-ext">{{ option.extension }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup name="FileTypeSelector">
import { computed } from 'vue'
import { Document, Grid, DocumentCopy } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: '请选择文件类型'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default'
  },
  customStyle: {
    type: Object,
    default: () => ({})
  },
  options: {
    type: Array,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 默认文件类型选项
const defaultFileTypeOptions = [
  { 
    label: 'Word文档', 
    value: 'doc', 
    extension: '.doc',
    icon: Document,
    description: 'Microsoft Word文档格式'
  },
  { 
    label: 'Excel表格', 
    value: 'xlsx', 
    extension: '.xlsx',
    icon: Grid,
    description: 'Microsoft Excel表格格式'
  },
  { 
    label: 'XML文件', 
    value: 'xml', 
    extension: '.xml',
    icon: DocumentCopy,
    description: '可扩展标记语言格式'
  }
]

// 计算文件类型选项
const fileTypeOptions = computed(() => {
  return props.options || defaultFileTypeOptions
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
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
  color: #409eff;
}

.file-type-text {
  flex: 1;
  font-size: 14px;
  color: #606266;
}

.file-type-ext {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

:deep(.el-select-dropdown__item) {
  padding: 8px 20px;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: #f5f7fa;
}

:deep(.el-select-dropdown__item.selected) {
  background-color: #ecf5ff;
  color: #409eff;
}
</style>