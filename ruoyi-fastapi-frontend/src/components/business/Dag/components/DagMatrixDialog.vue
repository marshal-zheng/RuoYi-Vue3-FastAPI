<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <!-- 对话框头部 -->
    <template #header>
      <div class="matrix-dialog-header">
        <span class="dialog-title">{{ props.title }}</span>
        <div class="header-actions">
          <el-button
            size="small"
            :icon="isFullscreen ? Minus : FullScreen"
            @click="toggleFullscreen"
            title="切换全屏"
          />
        </div>
      </div>
    </template>

    <!-- 矩阵视图内容 -->
    <DagMatrixView
      ref="matrixViewRef"
      :graph-data="props.graphData"
      :readonly="props.readonly"
      :loading="props.loading"
      :columns="props.columns"
      :node-renderer="props.nodeRenderer"
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
          <el-button v-if="!props.readonly" type="primary" @click="handleSave" :loading="saving">
            保存更改
          </el-button>
        </div>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Close, FullScreen, Minus, Download } from '@element-plus/icons-vue';
import { useDialog } from '@zxio/zxui';
import DagMatrixView from './DagMatrixView.vue';

defineOptions({
  name: 'DagMatrixDialog',
});

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '矩阵视图',
  },
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] }),
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  columns: {
    type: Array,
    default: () => [],
  },
  nodeRenderer: {
    type: Function,
    default: null,
  },
});

// Emits
const emit = defineEmits([
  'update:modelValue',
  'node-add',
  'node-update',
  'node-delete',
  'row-click',
  'save',
  'close',
]);

// 响应式数据
const matrixViewRef = ref(null);
const isFullscreen = computed(() => state.isFullscreen);
const saving = ref(false);

// 使用 useDialog hook
const { state, dialogProps, dialogEvents, open, close, toggleFullscreen } = useDialog({
  dialogSize: 'xl',
  noContentPadding: true,
  title: () => props.title,

  closeOnClickModal: false,
  defaultData: () => ({}),
  onClose: handleClose,
});

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      open();
    } else {
      close();
    }
  }
);

// 监听对话框关闭，同步 modelValue
watch(
  () => state.visible,
  (val) => {
    if (!val) {
      emit('update:modelValue', false);
    }
  }
);

// 方法

const handleNodeAdd = (nodeData) => {
  emit('node-add', nodeData);
};

const handleNodeUpdate = (nodeData) => {
  emit('node-update', nodeData);
};

const handleNodeDelete = (nodeData) => {
  emit('node-delete', nodeData);
};

const handleRowClick = (data) => {
  emit('row-click', data);
};

const handleRefresh = () => {
  if (matrixViewRef.value) {
    matrixViewRef.value.refresh();
  }
};

const handleExport = () => {
  if (matrixViewRef.value) {
    const matrixData = matrixViewRef.value.getMatrixData();
    const dataStr = JSON.stringify(matrixData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `matrix-data-${new Date().getTime()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    ElMessage.success('数据导出成功');
  }
};

const handleSave = async () => {
  try {
    saving.value = true;
    // 这里可以获取矩阵数据并转换为图数据
    const graphData = props.graphData; // 简化处理
    emit('save', graphData);
    ElMessage.success('保存成功');
  } catch (error) {
    console.error('保存失败:', error);
    ElMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
};

function handleClose() {
  emit('close');
  emit('update:modelValue', false);
  close();
}

// 暴露方法
defineExpose({
  refresh: () => matrixViewRef.value?.refresh(),
  open,
  close,
});
</script>

<style lang="less" scoped>
.matrix-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0 8px;

  .dialog-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
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
</style>
