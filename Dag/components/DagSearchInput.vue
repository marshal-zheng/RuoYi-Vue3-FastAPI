<template>
  <el-input
    v-model="keyword"
    class="dag-search-input"
    :class="className"
    :placeholder="placeholder"
    clearable
    size="small"
  >
    <template #prefix>
      <el-icon><Search /></el-icon>
    </template>
  </el-input>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  placeholder: {
    type: String,
    default: ''
  },
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['search'])

const keyword = ref('')
let timer = 0

watch(keyword, (val) => {
  if (timer) {
    window.clearTimeout(timer)
  }
  timer = window.setTimeout(() => {
    emit('search', val)
  }, 200)
})

onBeforeUnmount(() => {
  if (timer) {
    window.clearTimeout(timer)
  }
})
</script>

<style scoped lang="scss">
.dag-search-input {
  height: 28px;

  :deep(.el-input__wrapper) {
    border-color: #d4d7da;

    &:hover,
    &.is-focus {
      border-color: #0068fa;
      box-shadow: 0 0 0 1px rgba(0, 104, 250, 0.2);
    }
  }
}
</style>
