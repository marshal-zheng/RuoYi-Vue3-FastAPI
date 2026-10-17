<template>
  <ZxContentWrap data-testid="project-list-page" fill>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProjectData"
      :query-transform="queryTransform"
      class="project-grid"
      fill
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton
              type="primary"
              icon="Plus"
              data-testid="project-add-button"
              @click="handleAdd"
              v-hasPermi="['project:project:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['project:project:remove']"
              :loading="handleDeletePending"
              >删除</ZxButton
            >
            <ZxButton
              type="default"
              icon="Download"
              :disabled="multiple"
              @click="handleBatchExport"
              v-hasPermi="['project:project:query']"
              >批量导出</ZxButton
            >
            <ZxButton
              type="success"
              icon="Upload"
              @click="handleImportClick"
              v-hasPermi="['project:project:add']"
              >导入工程</ZxButton
            >
            <input
              ref="importFileInputRef"
              type="file"
              accept=".zip"
              style="display: none"
              @change="handleImportFileChange"
            />
          </template>
          <template #filters>
            <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="query.projectName"
              placeholder="搜索工程名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
      </template>

      <template #table="{ grid }">
        <div class="project-grid__scroll" v-loading="grid.loading">
          <div
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-5 project-grid"
          >
            <el-card
              v-for="project in grid.list"
              :key="project.projectId"
              class="group relative project-card"
              :data-testid="`project-card-${project.projectId}`"
              shadow="hover"
              :body-style="{ padding: '0' }"
              :class="{ 'project-card--selected': ids.includes(project.projectId) }"
            >
              <div
                v-if="ids.includes(project.projectId)"
                class="project-card__selection-bar absolute top-0 left-0 right-0 h-0.5"
              />
              <template #header>
                <div class="flex items-start justify-between gap-3">
                  <div class="flex items-start gap-3 flex-1 min-w-0">
                    <el-checkbox
                      :model-value="ids.includes(project.projectId)"
                      @change="toggleSelection(project)"
                      @click.stop
                      class="-mt-1 flex-shrink-0"
                    />
                    <div class="flex-1 min-w-0">
                      <h3
                        class="project-card__title text-base font-semibold truncate mb-1 leading-tight"
                      >
                        <router-link
                          :to="'/project/project-detail/index/' + project.projectId"
                          :data-testid="`project-detail-link-${project.projectId}`"
                          class="project-card__link transition-colors no-underline"
                          @click.stop
                        >
                          {{ project.projectName }}
                        </router-link>
                      </h3>
                      <p class="project-card__muted text-xs flex items-center gap-1">
                        <ZxIcon icon="Tickets" :size="14" />
                        <span>编号: {{ project.projectId }}</span>
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 mr-2">
                    <ZxIcon
                      v-if="checkPermi(['project:project:query'])"
                      icon="View"
                      :size="16"
                      tooltip="查看详情"
                      class="project-card__action p-1.5 cursor-pointer rounded transition-colors stroke-[2]"
                      @click.stop="handleDetail(project)"
                    />
                    <span
                      v-if="checkPermi(['project:project:edit'])"
                      :data-testid="`project-edit-${project.projectId}`"
                      role="button"
                      tabindex="0"
                      :aria-label="`编辑工程 ${project.projectName}`"
                      @click.stop="handleEdit(project)"
                      @keyup.enter.stop="handleEdit(project)"
                    >
                      <ZxIcon
                        icon="Edit"
                        :size="16"
                        tooltip="编辑工程"
                        class="project-card__action p-1.5 cursor-pointer rounded transition-colors stroke-[2]"
                      />
                    </span>
                    <ZxIcon
                      v-if="checkPermi(['project:project:query'])"
                      icon="Download"
                      :size="16"
                      tooltip="导出工程"
                      class="project-card__action p-1.5 cursor-pointer rounded transition-colors stroke-[2]"
                      @click.stop="handleExport(project)"
                    />
                  </div>
                  <ZxMoreAction
                    class="flex-shrink-0"
                    :list="getProjectMoreActionList()"
                    @select="handleMoreActionSelect($event, project)"
                  />
                </div>
              </template>

              <div class="px-5 py-4">
                <div class="mb-4">
                  <div
                    class="project-card__muted text-[13px] leading-relaxed line-clamp-2 min-h-[40px]"
                  >
                    {{ project.projectDesc || '暂无工程描述信息' }}
                  </div>
                </div>

                <div class="space-y-2.5 mb-4">
                  <div class="flex items-center text-xs">
                    <div
                      class="project-card__muted flex items-center gap-1.5 w-[72px] flex-shrink-0"
                    >
                      <ZxIcon icon="User" :size="14" />
                      <span>创建人</span>
                    </div>
                    <span class="project-card__title font-medium">{{
                      project.createBy || '-'
                    }}</span>
                  </div>
                  <div class="flex items-center text-xs">
                    <div
                      class="project-card__muted flex items-center gap-1.5 w-[72px] flex-shrink-0"
                    >
                      <ZxIcon icon="Clock" :size="14" />
                      <span>创建时间</span>
                    </div>
                    <span class="project-card__muted">{{
                      parseTime(project.createTime, '{y}-{m}-{d}') || '-'
                    }}</span>
                  </div>
                </div>
              </div>

              <template #footer>
                <div class="flex items-center gap-2">
                  <ZxButton
                    @click.stop="handleDetail(project)"
                    v-hasPermi="['project:project:query']"
                    type="default"
                    icon="Document"
                    class="flex-1"
                    >详情</ZxButton
                  >
                  <ZxButton
                    @click.stop="handleDelete(project)"
                    v-hasPermi="['project:project:remove']"
                    type="danger"
                    icon="Delete"
                    class="flex-1"
                    :loading="handleDeletePending"
                    >删除</ZxButton
                  >
                </div>
              </template>
            </el-card>
          </div>

          <div v-if="!grid.loading && grid.list.length === 0" class="text-center py-16 px-4">
            <div
              class="project-empty__icon inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
            >
              <ZxIcon icon="InfoFilled" :size="40" />
            </div>
            <h3 class="project-empty__title text-base font-semibold mb-2">暂无工程</h3>
            <p class="project-empty__muted text-sm mb-6 max-w-md mx-auto">
              还没有创建任何工程，点击下方按钮开始创建您的第一个工程
            </p>
            <ZxButton
              type="primary"
              icon="Plus"
              data-testid="project-empty-add-button"
              @click="handleAdd"
              v-hasPermi="['project:project:add']"
              >创建工程</ZxButton
            >
          </div>
        </div>
      </template>
    </ZxGridList>
  </ZxContentWrap>

  <ProjectFormDialog ref="projectDialogRef" @success="handleCreateSuccess" />
</template>

<script setup name="Project">
import { useOperation } from '@/utils/operation';
import { serializeDateRange } from '@/utils/ruoyi';
import {
  listProject,
  delProject,
  exportProject,
  exportProjectBatch,
  importProjectBatch,
} from '@/api/project/project';
import { unlockProjectVersions } from '@/api/project/version';
import { checkPermi } from '@/utils/permission';
import { Delete, Unlock } from '@element-plus/icons-vue';
import { default as ProjectFormDialog } from './components/ProjectFormDialog.vue';
import { confirmInputDanger } from '@/theme/confirm-input';
import { ElMessage } from 'element-plus';
import { downloadFromResponse, validateFile } from '@/utils/io-toolkit';
import { isAbortError } from '@zxio/http';

const { proxy } = getCurrentInstance();

const gridListRef = ref();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);

const projectDialogRef = ref();

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
async function loadProjectData(params) {
  const response = await listProject(params);
  return response;
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}

function refreshList() {
  gridListRef.value && gridListRef.value.refresh();
}

function handleAdd() {
  return projectDialogRef.value?.open().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

function toggleSelection(project) {
  const index = ids.value.indexOf(project.projectId);
  if (index > -1) ids.value.splice(index, 1);
  else ids.value.push(project.projectId);
  single.value = ids.value.length != 1;
  multiple.value = !ids.value.length;
}

function handleDetail(row) {
  const projectId = row.projectId;
  proxy.$router.push('/project/project-detail/index/' + projectId);
}

const { run: handleDelete, pending: handleDeletePending } = useOperation(async (row) => {
  let projectName = '';
  let projectIds = [];

  // 如果是单个项目删除
  if (row && row.projectId) {
    projectName = row.projectName;
    projectIds = [row.projectId];
  }
  // 如果是批量删除（暂时不支持，因为需要用户确认每个项目名称）
  else if (ids.value.length === 1) {
    // 找到对应的项目名称
    const grid = gridListRef.value?.grid;
    const project = grid?.list?.find((p) => p.projectId === ids.value[0]);
    if (project) {
      projectName = project.projectName;
      projectIds = ids.value;
    }
  } else if (ids.value.length > 1) {
    ElMessage.error('批量删除暂不支持，请逐个删除项目以确保安全性');
    return;
  } else {
    ElMessage.error('请选择要删除的项目');
    return;
  }

  await confirmInputDanger({
    targetName: projectName,
    targetType: '项目',
    keyword: projectName,
    dangerMessage: `您即将删除项目"${projectName}"。删除的项目及其所有版本数据将无法恢复！`,
    description:
      '此操作是高风险操作，将永久删除项目及其所有版本数据。为防止误操作，请输入项目名称确认您的意图。',
  });

  // 用户确认后执行删除
  await delProject(projectIds.length === 1 ? projectIds[0] : projectIds);
  refreshList();
  // 清空选择状态
  ids.value = [];
  single.value = true;
  multiple.value = true;
});

function getProjectMoreActionList() {
  const actions = [];
  if (checkPermi(['project:version:edit'])) {
    actions.push({
      label: '批量解除固化',
      eventTag: 'unlockVersions',
      icon: Unlock,
    });
  }
  if (checkPermi(['project:project:remove'])) {
    actions.push({
      label: '删除工程',
      eventTag: 'delete',
      icon: Delete,
      danger: true,
    });
  }
  return actions;
}

function handleMoreActionSelect(item, project) {
  switch (item.eventTag) {
    case 'detail':
      handleDetail(project);
      break;
    case 'edit':
      handleEdit(project);
      break;
    case 'export':
      handleExport(project);
      break;
    case 'unlockVersions':
      handleUnlockProjectVersions(project);
      break;
    case 'delete':
      handleDelete(project);
      break;
    default:
      break;
  }
}

function handleEdit(project) {
  return projectDialogRef.value?.open(project.projectId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

const { run: handleUnlockProjectVersions } = useOperation(async (project) => {
  if (!project?.projectId) {
    ElMessage.error('工程ID不存在，无法操作');
    return;
  }
  await proxy.$modal
    .confirm(`是否批量解除工程"${project.projectName}"下的所有固化版本？`)
    .then(async () => {
      await unlockProjectVersions(project.projectId);
    })
    .catch(() => {});
});

function handleCreateSuccess(payload) {
  // 编辑模式：刷新列表即可
  if (payload?.mode === 'edit') {
    refreshList();
    return;
  }

  // 新增模式：跳转到拓扑页面
  let projectId = null;
  let versionId = null;
  if (payload && typeof payload === 'object') {
    const data = payload;
    if (data && typeof data === 'object') {
      projectId = data.projectId || data.id;
      versionId = data.versionId;
    }
  }
  if (projectId) {
    const query = {};
    if (versionId) {
      query.versionId = versionId;
    }
    proxy.$router.push({
      path: '/project/topo/index/' + projectId,
      query,
    });
  } else {
    refreshList();
  }
}

// ========== 工程导出功能 ==========
async function handleExport(project) {
  if (!project?.projectId) {
    ElMessage.error('工程ID不存在，无法导出');
    return;
  }

  const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const safeName = (project.projectName || 'project').replace(/[\\/:*?"<>|\\s]+/g, '_');
  const filename = `${safeName}_export_${timestamp}.zip`;
  try {
    const res = await exportProject(project.projectId);
    await downloadFromResponse(res, filename);
    ElMessage.success('工程导出成功');
  } catch (error) {
    if (!isAbortError(error)) ElMessage.error(error?.message || '工程导出失败');
  }
}

async function handleBatchExport() {
  if (!ids.value.length) {
    ElMessage.error('请先勾选要导出的工程');
    return;
  }

  try {
    const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
    const filename = `project_export_${timestamp}.zip`;
    const res = await exportProjectBatch(ids.value);
    await downloadFromResponse(res, filename);

    ElMessage.success('批量导出任务已完成');
  } catch (error) {
    if (!isAbortError(error)) {
      ElMessage.error(error?.detail || error?.message || '批量导出失败');
    }
  }
}

// ========== 工程导入功能 ==========
const importFileInputRef = ref(null);

function handleImportClick() {
  importFileInputRef.value?.click();
}

const { run: handleImportFileChange } = useOperation(async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // 重置input，以便下次选择同一文件时也能触发change事件
  event.target.value = '';

  const validation = validateFile(file, {
    accept: ['.zip'],
    maxSize: 50 * 1024 * 1024,
  });
  if (!validation.valid) {
    ElMessage.error(validation.error || '文件校验失败');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);
  const result = await importProjectBatch(formData);
  const summary = result?.summary || {};
  const successCount = summary.succeeded || 0;
  if (successCount > 0) {
    refreshList();
  }
});
</script>
<style scoped>
.project-grid__scroll {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  padding: 6px 4px 16px;
}

.project-grid__scroll::-webkit-scrollbar {
  width: 8px;
}

.project-grid__scroll::-webkit-scrollbar-thumb {
  background-color: var(--zx-semantic-border-subtle);
  border-radius: 999px;
}

.project-grid :deep(.el-card) {
  border-radius: 8px;
}
.project-card {
  background-color: var(--zx-semantic-surface-card-fill);
  background-image: var(--zx-semantic-surface-card-highlight);
  color: var(--zx-semantic-surface-card-on-text);
}
.project-card--selected {
  border-color: var(--zx-semantic-accent-base);
  box-shadow:
    0 0 0 1px var(--zx-semantic-accent-base),
    var(--zx-semantic-surface-card-depth);
}
.project-card__selection-bar {
  background-color: var(--zx-semantic-accent-base);
}
.project-card__title {
  color: var(--zx-semantic-surface-card-on-text);
}
.project-card__muted {
  color: var(--zx-semantic-surface-card-on-text-secondary);
}
.project-card__link:hover,
.project-card__action:hover {
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
}
.project-card__action {
  color: var(--zx-semantic-surface-card-on-text-secondary);
}
.project-card__action:hover {
  background-color: var(--zx-semantic-fill-hover);
}
.project-empty__icon {
  background-color: var(--zx-semantic-fill-subtle);
  color: var(--zx-semantic-text-secondary);
}
.project-empty__title {
  color: var(--zx-semantic-surface-canvas-on-text);
}
.project-empty__muted {
  color: var(--zx-semantic-surface-canvas-on-text-secondary);
}
.project-grid {
  grid-template-columns: repeat(4, 1fr);
}
.project-card :deep(.el-card__header) {
  border-bottom: 1px solid var(--zx-semantic-border-subtle);
  background: transparent;
}
.project-card :deep(.el-card__footer) {
  background: transparent;
}
</style>
