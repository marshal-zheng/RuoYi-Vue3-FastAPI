<template>
  <ZxDialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :height="height"
    :fullscreen="isFullscreen"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 对话框头部 -->
    <template #header="{ close }">
      <div class="matrix-dialog-header">
        <span class="dialog-title">{{ title }}</span>
        <div class="header-actions">
          <el-button
            size="small"
            :icon="isFullscreen ? Minus : FullScreen"
            @click="toggleFullscreen"
            title="切换全屏"
          />
          <el-button size="small" :icon="Close" @click="close" title="关闭" />
        </div>
      </div>
    </template>

    <!-- 矩阵视图内容 -->
    <DagMatrixView
      ref="matrixViewRef"
      :graph-data="graphData"
      :readonly="readonly"
      :loading="loading"
      :columns="columns"
      :node-renderer="nodeRenderer"
      @node-add="handleNodeAdd"
      @node-update="handleNodeUpdate"
      @node-delete="handleNodeDelete"
      @row-click="handleRowClick"
      @refresh="handleRefresh"
    />

    <!-- 对话框底部 -->
    <template #footer>
      <div class="matrix-dialog-footer">
        <div class="footer-left">
          <el-button size="small" :icon="Download" @click="handleExport"> 导出数据 </el-button>
        </div>
        <div class="footer-right">
          <el-button @click="handleClose">关闭</el-button>
          <el-button v-if="!readonly" type="primary" @click="handleSave" :loading="saving">
            保存更改
          </el-button>
        </div>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, FullScreen, Minus, Download } from '@element-plus/icons-vue'
import DagMatrixView from './DagMatrixView.vue'

defineOptions({
  name: 'DagMatrixDialog'
})

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '矩阵视图'
  },
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  },
  readonly: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  columns: {
    type: Array,
    default: () => []
  },
  nodeRenderer: {
    type: Function,
    default: null
  },
  width: {
    type: String,
    default: '1200px'
  },
  height: {
    type: String,
    default: '80%'
  }
})

// Emits
const emit = defineEmits([
  'update:modelValue',
  'node-add',
  'node-update',
  'node-delete',
  'row-click',
  'save',
  'close'
])

// 响应式数据
const matrixViewRef = ref(null)
const isFullscreen = ref(false)
const saving = ref(false)

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const handleNodeAdd = (nodeData) => {
  emit('node-add', nodeData)
}

const handleNodeUpdate = (nodeData) => {
  emit('node-update', nodeData)
}

const handleNodeDelete = (nodeData) => {
  emit('node-delete', nodeData)
}

const handleRowClick = (data) => {
  emit('row-click', data)
}

const handleRefresh = () => {
  if (matrixViewRef.value) {
    matrixViewRef.value.refresh()
  }
}

const handleExport = () => {
  if (matrixViewRef.value) {
    const matrixData = matrixViewRef.value.getMatrixData()
    const dataStr = JSON.stringify(matrixData, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `matrix-data-${new Date().getTime()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('数据导出成功')
  }
}

const handleSave = async () => {
  try {
    saving.value = true
    // 这里可以获取矩阵数据并转换为图数据
    const graphData = props.graphData // 简化处理
    emit('save', graphData)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  emit('close')
  dialogVisible.value = false
}

// 暴露方法
defineExpose({
  refresh: () => matrixViewRef.value?.refresh()
})
</script>

<style lang="scss" scoped>
.matrix-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 8px;

  .dialog-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.matrix-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .footer-left,
  .footer-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 对话框内容区域样式优化
:deep(.zx-dialog__body) {
  padding: 0 !important;

  .dag-matrix-view {
    height: 100%;
  }
}
</style>
