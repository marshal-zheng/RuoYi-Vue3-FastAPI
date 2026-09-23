<template>
  <div class="dag-matrix-view-simple">
    <!-- 搜索区域 -->
    <div class="search-bar">
      <zx-input
        v-model="searchText"
        placeholder="搜索节点..."
        :prefix-icon="Search"
        clearable
        style="width: 300px; margin-right: 12px"
      />
      <el-text type="info" size="small">
        显示 {{ filteredData.length }} / {{ totalNodes }} 个节点
      </el-text>
    </div>

    <!-- 普通表格 -->
    <div class="table-container">
      <el-table :data="filteredData" style="width: 100%" height="500" @row-click="handleRowClick">
        <!-- 节点名称 - 放在最前面 -->
        <el-table-column label="节点名称" width="200" fixed="left">
          <template #default="{ row }">
            <div class="node-name-cell">
              <el-icon class="node-icon">
                <component :is="getNodeTypeIcon(row.type)" />
              </el-icon>
              <span class="name-text">{{ row.properties?.content?.label || '未命名' }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 层级 -->
        <el-table-column label="层级" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getLevelTagType(row.level)"> L{{ row.level }} </el-tag>
          </template>
        </el-table-column>

        <!-- 类型 -->
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)" size="small">
              {{ getTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 层级路径 - 显示两级，超过用popover -->
        <el-table-column label="层级路径" width="250">
          <template #default="{ row }">
            <div class="hierarchy-path-cell">
              <span class="path-display">{{ getDisplayPath(row._path) }}</span>
              <ZxTooltipOrPopover
                v-if="needsPopover(row._path)"
                :title="'完整路径'"
                trigger="click"
                placement="top"
                :width="300"
              >
                <el-button type="primary" text size="small">...</el-button>
                <template #content>
                  <div class="full-path-content">
                    <div v-for="(pathItem, index) in row._path" :key="index" class="path-item">
                      <span class="path-level">L{{ index + 1 }}</span>
                      <span class="path-name">{{ pathItem }}</span>
                    </div>
                  </div>
                </template>
              </ZxTooltipOrPopover>
            </div>
          </template>
        </el-table-column>

        <!-- 描述 - 使用CSS省略号，hover时显示完整内容 -->
        <el-table-column label="描述" min-width="200">
          <template #default="{ row }">
            <div class="description-cell">
              <el-tooltip
                v-if="row.properties?.content?.description"
                :content="row.properties?.content?.description"
                placement="top"
                :show-after="300"
                :hide-after="0"
                effect="light"
              >
                <div class="description-text">
                  {{ row.properties?.content?.description }}
                </div>
              </el-tooltip>
              <span v-else class="description-empty">-</span>
            </div>
          </template>
        </el-table-column>

        <!-- 自定义列 -->
        <template v-for="column in props.columns" :key="column.key">
          <el-table-column :label="column.title" :width="column.width">
            <template #default="{ row }">
              <div v-if="column.cellRenderer" class="custom-cell-text">
                {{ renderCustomCell(column.cellRenderer, row) }}
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </template>

        <!-- 操作列 - fixed -->
        <el-table-column label="操作" width="200" fixed="right" v-if="!readonly">
          <template #default="{ row }">
            <div class="operation-buttons">
              <el-button size="small" type="primary" text @click="handleAddChild(row)">
                添加
              </el-button>
              <el-button size="small" type="warning" text @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button size="small" type="danger" text @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 编辑对话框 -->
    <ZxDialog
      v-bind="nodeDialog.dialogProps.value"
      v-on="nodeDialog.dialogEvents.value"
      :draggable="false"
      :show-full-screen="false"
      :destroy-on-close="false"
      :close-on-click-modal="true"
    >
      <el-form ref="nodeFormRef" :model="editDialog.nodeData" v-bind="nodeDialog.formProps"
        ><FormGrid v-bind="nodeDialog.layoutProps">
          <el-form-item label="节点类型">
            <el-select v-model="editDialog.nodeData.type" style="width: 100%">
              <el-option label="根节点" value="root-node" />
              <el-option label="子节点" value="sub-node" />
              <el-option label="叶子节点" value="leaf-node" />
            </el-select>
          </el-form-item>
          <el-form-item label="节点名称">
            <zx-input
              v-model="editDialog.nodeData.properties.content.label"
              placeholder="请输入节点名称"
            />
          </el-form-item>
          <el-form-item label="描述">
            <zx-input
              v-model="editDialog.nodeData.properties.content.description"
              type="textarea"
              :rows="3"
              placeholder="请输入节点描述"
            />
          </el-form-item> </FormGrid
      ></el-form>
      <template #footer>
        <el-button @click="nodeDialog.close()">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit">确定</el-button>
      </template>
    </ZxDialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, toRef } from 'vue';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Folder, Document, Connection, Plus, Edit, Delete } from '@element-plus/icons-vue';
import { transformGraphToMatrix } from '../utils/matrixDataTransform.js';

defineOptions({
  name: 'DagMatrixView',
});

// Props
const props = defineProps({
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
const emit = defineEmits(['node-add', 'node-update', 'node-delete', 'row-click']);

// 响应式数据
const flatData = ref([]);
const searchText = ref('');
const nodeFormRef = ref();
const nodeDialog = useFormDialog({
  columns: 1,
  formRef: nodeFormRef,
  title: (data) => (data.isAdd ? '添加节点' : '编辑节点'),
  closeOnClickModal: true,
  destroyOnClose: false,
  preValidate: false,
  autoResetForm: false,
  defaultData: () => ({ isAdd: false, nodeData: {} }),
});
const editDialog = toRef(nodeDialog.state, 'data');

// 计算属性
const totalNodes = computed(() => flatData.value.length);

const filteredData = computed(() => {
  let result = flatData.value;

  if (searchText.value) {
    const search = searchText.value.toLowerCase();
    result = result.filter((item) => {
      const label = item.properties?.content?.label?.toLowerCase() || '';
      const desc = item.properties?.content?.description?.toLowerCase() || '';
      const path = item._pathString?.toLowerCase() || '';
      return label.includes(search) || desc.includes(search) || path.includes(search);
    });
  }

  return result;
});

// 方法
const convertGraphToMatrix = (graphData) => {
  try {
    console.log('🔄 转换图数据:', graphData);
    const treeData = transformGraphToMatrix(graphData, props.nodeRenderer);
    console.log('🌳 树形数据:', treeData);

    const flattened = flattenTreeData(treeData);
    console.log('📊 扁平化数据:', flattened);

    flatData.value = flattened;
  } catch (error) {
    console.error('转换失败:', error);
    flatData.value = [];
  }
};

const flattenTreeData = (treeData, parentPath = []) => {
  const result = [];

  if (!Array.isArray(treeData)) {
    console.warn('treeData 不是数组:', treeData);
    return result;
  }

  treeData.forEach((node) => {
    const currentPath = [...parentPath, node.properties?.content?.label || '未命名'];
    const flatNode = {
      ...node,
      _path: currentPath,
      _pathString: currentPath.join(' > '),
    };

    result.push(flatNode);

    if (node.children && node.children.length > 0) {
      result.push(...flattenTreeData(node.children, currentPath));
    }
  });

  return result;
};

const getNodeTypeIcon = (type) => {
  const iconMap = {
    'root-node': Folder,
    'sub-node': Connection,
    'leaf-node': Document,
  };
  return iconMap[type] || Document;
};

const getTypeTagType = (type) => {
  const typeMap = {
    'root-node': 'primary',
    'sub-node': 'success',
    'leaf-node': 'info',
  };
  return typeMap[type] || 'info';
};

const getTypeText = (type) => {
  const textMap = {
    'root-node': '根节点',
    'sub-node': '子节点',
    'leaf-node': '叶子节点',
  };
  return textMap[type] || '未知';
};

const renderCustomCell = (renderer, row) => {
  if (typeof renderer === 'function') {
    try {
      const result = renderer({ rowData: row });
      if (typeof result === 'string') {
        return result;
      }
      if (result && typeof result === 'object' && result.toString) {
        return result.toString();
      }
      return String(result || '-');
    } catch (error) {
      console.error('自定义单元格渲染错误:', error);
      return '-';
    }
  }
  return '-';
};

// 层级路径处理
const getDisplayPath = (pathArray) => {
  if (!Array.isArray(pathArray) || pathArray.length === 0) {
    return '-';
  }

  if (pathArray.length <= 2) {
    return pathArray.join(' > ');
  }

  // 显示前两级
  return pathArray.slice(0, 2).join(' > ');
};

const needsPopover = (pathArray) => {
  return Array.isArray(pathArray) && pathArray.length > 2;
};

// 层级标签类型
const getLevelTagType = (level) => {
  const types = ['', 'primary', 'success', 'info', 'warning', 'danger'];
  return types[Math.min(level, types.length - 1)] || 'info';
};

// 事件处理
const handleRowClick = (row) => {
  emit('row-click', { row });
};

const handleAddChild = (parentRow) => {
  const newNode = {
    id: `node_${Date.now()}`,
    type: 'leaf-node',
    level: parentRow.level + 1,
    parentId: parentRow.id,
    properties: {
      content: {
        label: '新子节点',
        description: '',
      },
    },
  };

  nodeDialog.open({
    isAdd: true,
    nodeData: { ...newNode },
    parentNode: parentRow,
  });
};

const handleEdit = (row) => {
  nodeDialog.open({
    isAdd: false,
    nodeData: { ...row },
  });
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点"${row.properties?.content?.label}"吗？`,
      '确认删除',
      { type: 'warning' }
    );

    emit('node-delete', row);
    ElMessage.success('删除成功');
  } catch (error) {
    // 用户取消
  }
};

const handleEditSubmit = () => {
  if (editDialog.value.isAdd) {
    emit('node-add', editDialog.value.nodeData);
    ElMessage.success('添加成功');
  } else {
    emit('node-update', editDialog.value.nodeData);
    ElMessage.success('更新成功');
  }

  nodeDialog.close();
};

// 监听数据变化
watch(
  () => props.graphData,
  (newData) => {
    if (newData) {
      convertGraphToMatrix(newData);
    }
  },
  { immediate: true, deep: true }
);

// 暴露方法
defineExpose({
  refresh: () => convertGraphToMatrix(props.graphData),
  search: (text) => {
    searchText.value = text;
  },
});
</script>

<style lang="less" scoped>
.dag-matrix-view-simple {
  display: flex;
  flex-direction: column;
  height: 100%;

  .search-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    background: #f6f8fa;
    border-bottom: 1px solid #eaebed;
  }

  .table-container {
    flex: 1;
    padding: 16px;
  }

  .node-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .node-icon {
      font-size: 14px;

      &:deep(.type-root-node) {
        color: #409eff;
      }

      &:deep(.type-sub-node) {
        color: #67c23a;
      }

      &:deep(.type-leaf-node) {
        color: #909399;
      }
    }

    .name-text {
      font-weight: 500;
      color: #303133;
    }
  }

  .hierarchy-path-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .path-display {
      font-size: 12px;
      color: #606266;
    }
  }

  .description-cell {
    width: 100%;
    max-width: 100%;
    overflow: hidden;

    .description-text {
      font-size: 12px;
      color: #606266;
      line-height: 1.4;
      cursor: help;
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 100%;
    }

    .description-empty {
      font-size: 12px;
      color: #909399;
    }
  }

  .operation-buttons {
    display: flex;
    gap: 4px;
    align-items: center;
  }
}

// Popover内容样式
:deep(.full-path-content) {
  .path-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .path-level {
      font-size: 10px;
      padding: 2px 6px;
      background: #f0f2f5;
      border-radius: 2px;
      color: #606266;
      font-weight: 500;
      min-width: 24px;
      text-align: center;
    }

    .path-name {
      font-size: 12px;
      color: #303133;
      flex: 1;
    }
  }
}
</style>
