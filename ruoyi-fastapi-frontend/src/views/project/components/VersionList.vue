<template>
  <div class="version-list">
    <ZxGridList
      ref="versionGridListRef"
      :load-data="loadVersionData"
      class="version-grid zx-grid-list--page"
    >
      <!-- 工具栏：左-操作 | 中-筛选 | 右-搜索 -->
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <!-- <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAddVersion"
              v-hasPermi="['project:version:add']"
              >新增</ZxButton
            > -->
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="() => handleDeleteVersion(null, versionGridListRef?.refresh)"
              v-hasPermi="['project:version:remove']"
              >删除</ZxButton
            >
          </div>

          <div class="zx-grid-form-bar__filters">
            <!-- <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
              @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            /> -->
          </div>

          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.versionName"
              placeholder="搜索版本名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <!-- 表格内容 -->
      <template #table="{ grid, refresh: handleRefresh }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="版本号" prop="versionNumber" width="120" />
          <el-table-column label="版本名称" prop="versionName" min-width="150" />
          <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
          <el-table-column label="创建人" prop="createBy" width="120" />
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="{ row }">
              {{ parseTime(row.createTime) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="isLocked" align="center" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.isLocked === '1'" type="warning">
                <el-icon class="mr-1"><Lock /></el-icon>
                固化
              </el-tag>
              <el-tag v-else type="info">未固化</el-tag>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="220"
            class-name="op-col"
            label-class-name="op-col__header"
          >
            <template #default="{ row }">
              <div class="op-col__wrap">
                <ZxButton
                  link
                  type="primary"
                  @click="handleSimulateVersion(row)"
                  v-hasPermi="['simulation:use']"
                  >仿真</ZxButton
                >
                <ZxButton link type="primary" @click="handleEditVersionTopo(row)">图编辑</ZxButton>
                <ZxMoreAction
                  :list="getMoreActionList(row)"
                  @select="handleMoreActionSelect($event, row, handleRefresh)"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 编辑版本对话框 -->
    <el-dialog
      v-model="editVersionDialog"
      :title="editVersionForm.versionId ? '编辑版本' : '新增版本'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="editVersionForm" label-width="100px" label-position="left">
        <el-form-item label="版本号" required>
          <el-input
            v-model="editVersionForm.versionNumber"
            placeholder="请输入版本号，如：v1.0.0"
            maxlength="50"
            :disabled="!!editVersionForm.versionId"
          />
        </el-form-item>
        <el-form-item label="版本名称" required>
          <el-input
            v-model="editVersionForm.versionName"
            placeholder="请输入版本名称"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="版本描述">
          <el-input
            v-model="editVersionForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入版本描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editVersionDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveEditVersion">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看版本详情 -->
    <VersionDetailDialog ref="detailDialogRef" />

    <!-- 克隆版本 -->
    <VersionCloneDialog ref="cloneDialogRef" />

    <!-- 预览版本 -->
    <VersionPreviewDialog ref="previewDialogRef" />

    <!-- 导出版本对话框 -->
    <VersionExportDialog ref="exportDialogRef" />
  </div>
</template>

<script setup name="VersionList">
import { ref, reactive, watch, getCurrentInstance } from 'vue';
import { ElMessage } from 'element-plus';
import { View, Delete, Lock, CopyDocument, Download } from '@element-plus/icons-vue';
import {
  listProjectVersion,
  addProjectVersion,
  updateProjectVersion,
  delProjectVersion,
  lockProjectVersion,
} from '@/api/project/version';
import { parseTime } from '@/utils/ruoyi';
import VersionDetailDialog from './VersionDetailDialog.vue';
import VersionCloneDialog from './VersionCloneDialog.vue';
import VersionPreviewDialog from './VersionPreviewDialog.vue';
import VersionExportDialog from './VersionExportDialog.vue';

const { proxy } = getCurrentInstance();

const props = defineProps({
  projectId: {
    type: [String, Number],
    default: null,
  },
});

const versionGridListRef = ref(null);
const detailDialogRef = ref(null);
const cloneDialogRef = ref(null);
const previewDialogRef = ref(null);
const exportDialogRef = ref(null);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);

// 编辑版本对话框
const editVersionDialog = ref(false);
const editVersionForm = reactive({
  versionId: null,
  versionNumber: '',
  versionName: '',
  description: '',
});

/** ZxGridList 版本数据加载函数 */
async function loadVersionData(params = {}) {
  if (!props.projectId) {
    return {
      items: [],
      total: 0,
      page: 1,
      pageSize: 10,
    };
  }

  const queryParams = {
    ...params,
    projectId: props.projectId,
  };

  const response = await listProjectVersion(queryParams);
  return response;
}

watch(
  () => props.projectId,
  (value) => {
    if (value && versionGridListRef.value) {
      versionGridListRef.value.refresh();
    }
  },
  { immediate: true }
);

/** 筛选变化处理 */
function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  updateState('pager.page', 1);
  handleRefresh();
}

/** 搜索处理 */
function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.versionId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

// 获取更多操作列表
const getMoreActionList = (row) => {
  const actions = [];

  // 预览版本
  actions.push({
    label: '预览',
    eventTag: 'preview',
    icon: View,
    type: 'primary',
  });

  // 导出文件
  actions.push({
    label: '导出文件',
    eventTag: 'export',
    icon: Download,
    type: 'primary',
  });

  // 固化版本/解除固化
  if (row.isLocked === '1') {
    actions.push({
      label: '解除固化',
      eventTag: 'unlock',
      icon: Lock,
      type: 'warning',
    });
  } else {
    actions.push({
      label: '固化版本',
      eventTag: 'lock',
      icon: Lock,
      type: 'primary',
    });
  }

  // 克隆版本
  actions.push({
    label: '克隆版本',
    eventTag: 'clone',
    icon: CopyDocument,
    type: 'primary',
  });

  // 删除版本（固化版本不能删除）
  if (row.isLocked !== '1') {
    actions.push(
      { isDivider: true },
      {
        label: '删除',
        eventTag: 'delete',
        icon: Delete,
        danger: true,
      }
    );
  }

  return actions;
};

// 处理更多操作选择
const handleMoreActionSelect = async (item, row, handleRefresh) => {
  switch (item.eventTag) {
    case 'preview':
      handlePreviewVersion(row);
      break;
    case 'export':
      handleExportVersion(row);
      break;
    case 'exportExcel':
      handleExportVersionExcel(row);
      break;
    case 'lock':
      handleLockVersion(row, handleRefresh);
      break;
    case 'unlock':
      handleUnlockVersion(row, handleRefresh);
      break;
    case 'clone':
      handleCloneVersion(row);
      break;
    case 'delete':
      handleDeleteVersion(row, handleRefresh);
      break;
    default:
      break;
  }
};

/** 删除版本 */
function handleDeleteVersion(row, handleRefresh) {
  const versionIds = row?.versionId || ids.value.join(',');
  let confirmMessage = '';

  if (row?.versionId) {
    confirmMessage = `是否确认删除版本"${row.versionName}"？`;
  } else {
    confirmMessage = `是否确认删除选中的 ${ids.value.length} 个版本？`;
  }

  proxy.$modal
    .confirm(confirmMessage)
    .then(async () => {
      try {
        await delProjectVersion(versionIds);
        if (handleRefresh) {
          handleRefresh();
        } else if (versionGridListRef.value) {
          versionGridListRef.value.refresh();
        }
      } catch (error) {
        console.error('删除版本失败:', error);
      }
    })
    .catch(() => {});
}

/** 新增版本 */
function handleAddVersion() {
  // 重置表单
  editVersionForm.versionId = null;
  editVersionForm.versionNumber = '';
  editVersionForm.versionName = '';
  editVersionForm.description = '';

  editVersionDialog.value = true;
}

/** 仿真版本（跳转到仿真页面） */
function handleSimulateVersion(row) {
  if (!props.projectId) {
    ElMessage.error('缺少工程ID，无法打开仿真页面');
    return;
  }
  proxy.$router.push({
    path: `/project/simulation/index/${props.projectId}`,
    query: {
      versionId: row.versionId,
    },
  });
}

/** 编辑版本拓扑（跳转到拓扑图进行编辑） */
function handleEditVersionTopo(row) {
  if (!props.projectId) {
    ElMessage.error('缺少工程ID，无法打开拓扑图');
    return;
  }
  proxy.$router.push({
    path: `/project/topo/index/${props.projectId}`,
    query: {
      versionId: row.versionId,
    },
  });
}

/** 保存编辑版本 */
async function handleSaveEditVersion() {
  // 验证表单
  if (!editVersionForm.versionNumber || !editVersionForm.versionName) {
    ElMessage.error('版本号和版本名称不能为空');
    return;
  }

  const data = {
    versionId: editVersionForm.versionId,
    projectId: props.projectId,
    versionNumber: editVersionForm.versionNumber,
    versionName: editVersionForm.versionName,
    description: editVersionForm.description,
  };

  if (editVersionForm.versionId) {
    await updateProjectVersion(data);
  } else {
    await addProjectVersion(data);
  }

  editVersionDialog.value = false;

  // 刷新列表
  if (versionGridListRef.value) {
    versionGridListRef.value.refresh();
  }
}

/** 固化版本 */
function handleLockVersion(row, handleRefresh) {
  proxy.$modal
    .confirm(`确定要固化版本"${row.versionName}"吗？固化后将无法编辑和删除。`)
    .then(async () => {
      try {
        await lockProjectVersion({
          versionId: row.versionId,
          isLocked: '1',
        });
        if (handleRefresh) {
          handleRefresh();
        } else if (versionGridListRef.value) {
          versionGridListRef.value.refresh();
        }
      } catch (error) {
        console.error('固化版本失败:', error);
      }
    })
    .catch(() => {});
}

/** 解除固化版本 */
function handleUnlockVersion(row, handleRefresh) {
  proxy.$modal
    .confirm(`确定要解除版本"${row.versionName}"的固化状态吗？`)
    .then(async () => {
      try {
        await lockProjectVersion({
          versionId: row.versionId,
          isLocked: '0',
        });
        if (handleRefresh) {
          handleRefresh();
        } else if (versionGridListRef.value) {
          versionGridListRef.value.refresh();
        }
      } catch (error) {
        console.error('解除固化失败:', error);
      }
    })
    .catch(() => {});
}

/** 克隆版本 */
function handleCloneVersion(row) {
  cloneDialogRef.value?.open(row, () => {
    // 克隆成功后刷新列表
    if (versionGridListRef.value) {
      versionGridListRef.value.refresh();
    }
  });
}

/** 预览版本 */
function handlePreviewVersion(row) {
  previewDialogRef.value?.open(row);
}

/** 导出版本 */
function handleExportVersion(row) {
  exportDialogRef.value?.open(row);
}

/** 导出版本（直接选择 Excel） */
function handleExportVersionExcel(row) {
  exportDialogRef.value?.open(row, 'excel');
}
</script>

<style scoped lang="less">
.version-list {
  padding: 0;
}
</style>
