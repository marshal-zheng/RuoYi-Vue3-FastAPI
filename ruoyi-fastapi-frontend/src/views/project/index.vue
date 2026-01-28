<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProjectData"
      :query-transform="queryTransform"
      class="project-grid zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Plus"
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
          </div>
          <div class="zx-grid-form-bar__filters">
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
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.projectName"
              placeholder="搜索工程名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
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
              shadow="hover"
              :body-style="{ padding: '0' }"
              :class="{
                'border-[#0052d9] shadow-[0_0_0_2px_rgba(0,82,217,0.1)]': ids.includes(
                  project.projectId
                ),
                'hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)]': !ids.includes(project.projectId),
              }"
            >
              <div
                v-if="ids.includes(project.projectId)"
                class="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#0052d9] to-[#3370ff]"
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
                      <h3 class="text-base font-semibold text-[#1d2129] truncate mb-1 leading-tight">
                        <router-link
                          :to="'/project/project-detail/index/' + project.projectId"
                          class="hover:text-[#0052d9] transition-colors no-underline"
                          @click.stop
                        >
                          {{ project.projectName }}
                        </router-link>
                      </h3>
                      <p class="text-xs text-[#86909c] flex items-center gap-1">
                        <ZxIcon icon="Tickets" :size="14" color="#86909c" />
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
                      class="p-1.5 cursor-pointer rounded hover:bg-gray-100 text-[#86909c] hover:text-[#0052d9] transition-colors stroke-[2]"
                      @click.stop="handleDetail(project)"
                    />
                    <ZxIcon
                      v-if="checkPermi(['project:project:edit'])"
                      icon="Edit"
                      :size="16"
                      tooltip="编辑工程"
                      class="p-1.5 cursor-pointer rounded hover:bg-gray-100 text-[#86909c] hover:text-[#0052d9] transition-colors stroke-[2]"
                      @click.stop="handleEdit(project)"
                    />
                    <ZxIcon
                      v-if="checkPermi(['project:project:query'])"
                      icon="Download"
                      :size="16"
                      tooltip="导出工程"
                      class="p-1.5 cursor-pointer rounded hover:bg-gray-100 text-[#86909c] hover:text-[#0052d9] transition-colors stroke-[2]"
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
                  <div class="text-[#4e5969] text-[13px] leading-relaxed line-clamp-2 min-h-[40px]">
                    {{ project.projectDesc || '暂无工程描述信息' }}
                  </div>
                </div>

                <div class="space-y-2.5 mb-4">
                  <div class="flex items-center text-xs">
                    <div class="flex items-center gap-1.5 text-[#86909c] w-[72px] flex-shrink-0">
                      <ZxIcon icon="User" :size="14" color="#86909c" />
                      <span>创建人</span>
                    </div>
                    <span class="text-[#1d2129] font-medium">{{ project.createBy || '-' }}</span>
                  </div>
                  <div class="flex items-center text-xs">
                    <div class="flex items-center gap-1.5 text-[#86909c] w-[72px] flex-shrink-0">
                      <ZxIcon icon="Clock" :size="14" color="#86909c" />
                      <span>创建时间</span>
                    </div>
                    <span class="text-[#4e5969]">{{
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
                    >删除</ZxButton
                  >
                </div>
              </template>
            </el-card>
          </div>

          <div v-if="!grid.loading && grid.list.length === 0" class="text-center py-16 px-4">
            <div
              class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-[#f7f8fa] mb-4"
            >
              <ZxIcon icon="InfoFilled" :size="40" color="#c9cdd4" />
            </div>
            <h3 class="text-base font-semibold text-[#1d2129] mb-2">暂无工程</h3>
            <p class="text-sm text-[#86909c] mb-6 max-w-md mx-auto">
              还没有创建任何工程，点击下方按钮开始创建您的第一个工程
            </p>
            <ZxButton
              type="primary"
              icon="Plus"
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
import { serializeDateRange } from '@/utils/ruoyi';
import { listProject, delProject, exportProject, exportProjectBatch, importProjectBatch } from '@/api/project/project';
import { unlockProjectVersions } from '@/api/project/version';
import { checkPermi } from '@/utils/permission';
import { Document, Delete, Unlock, Download, Edit, View } from '@element-plus/icons-vue';
import { default as ProjectFormDialog } from './components/ProjectFormDialog.vue';
import { confirmInputDanger } from '@zxio/zxui';
import { ElMessage } from 'element-plus';
import { downloadFromResponse, validateFile } from '@/utils/io-toolkit';

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
  projectDialogRef.value && projectDialogRef.value.open();
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

async function handleDelete(row) {
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
    proxy.$modal.msgError('批量删除暂不支持，请逐个删除项目以确保安全性');
    return;
  } else {
    proxy.$modal.msgError('请选择要删除的项目');
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
}

function getProjectMoreActionList() {
  const actions = [];
  if (checkPermi(['project:version:edit'])) {
    actions.push({ label: '批量解除固化', eventTag: 'unlockVersions', icon: Unlock });
  }
  if (checkPermi(['project:project:remove'])) {
    actions.push({ label: '删除工程', eventTag: 'delete', icon: Delete, danger: true });
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
  projectDialogRef.value && projectDialogRef.value.open(project.projectId);
}

function handleUnlockProjectVersions(project) {
  if (!project?.projectId) {
    proxy.$modal.msgError('工程ID不存在，无法操作');
    return;
  }
  proxy.$modal
    .confirm(`是否批量解除工程"${project.projectName}"下的所有固化版本？`)
    .then(async () => {
      await unlockProjectVersions(project.projectId);
      proxy.$modal.msgSuccess('批量解除固化成功');
    })
    .catch(() => {});
}

function handleCreateSuccess(payload) {
  // 编辑模式：刷新列表即可
  if (payload?.mode === 'edit') {
    refreshList();
    proxy.$modal.msgSuccess('修改成功');
    return;
  }

  // 新增模式：跳转到拓扑页面
  let projectId = null;
  let versionId = null;
  if (payload && typeof payload === 'object') {
    const data = payload.data && typeof payload.data === 'object' ? payload.data : payload;
    if (data && typeof data === 'object') {
      projectId = data.projectId || data.id || data?.data?.projectId;
      versionId = data.versionId || data?.data?.versionId;
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
    proxy.$modal.msgSuccess('新增成功');
  }
}

// ========== 工程导出功能 ==========
async function handleExport(project) {
  if (!project?.projectId) {
    proxy.$modal.msgError('工程ID不存在，无法导出');
    return;
  }

  const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const safeName = (project.projectName || 'project').replace(/[\\/:*?"<>|\\s]+/g, '_');
  const filename = `${safeName}_export_${timestamp}.zip`;
  const res = await exportProject(project.projectId);
  await downloadFromResponse(res, filename);

  ElMessage.success('工程导出成功');
}

async function handleBatchExport() {
  if (!ids.value.length) {
    proxy.$modal.msgError('请先勾选要导出的工程');
    return;
  }

  try {
    const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
    const filename = `project_export_${timestamp}.zip`;
    const res = await exportProjectBatch(ids.value);
    await downloadFromResponse(res, filename);

    ElMessage.success('批量导出任务已完成');
  } catch (error) {
    proxy.$modal.msgError(error?.msg || '批量导出失败');
  }
}

// ========== 工程导入功能 ==========
const importFileInputRef = ref(null);

function handleImportClick() {
  importFileInputRef.value?.click();
}

async function handleImportFileChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  // 重置input，以便下次选择同一文件时也能触发change事件
  event.target.value = '';

  const validation = validateFile(file, { accept: ['.zip'], maxSize: 50 * 1024 * 1024 });
  if (!validation.valid) {
    proxy.$modal.msgError(validation.error || '文件校验失败');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);
  const result = await importProjectBatch(formData);
  const summary = result?.data || {};
  const successCount = summary.successCount || 0;
  const failedCount = summary.failedCount || 0;

  if (failedCount > 0) {
    ElMessage.warning(`导入完成，成功 ${successCount} 个，失败 ${failedCount} 个`);
  } else {
    ElMessage.success(`导入完成，成功 ${successCount} 个工程`);
  }
  refreshList();
}
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
  background-color: rgba(0, 0, 0, 0.18);
  border-radius: 999px;
}

.project-grid :deep(.el-card) {
  border-radius: 8px;
}
.project-card {
  background-image:
    linear-gradient(8deg, hsla(0, 0%, 100%, 0.6) 30%, rgba(0, 82, 217, 0.16) 100%),
    linear-gradient(209deg, #cdd8ff 0%, #eef2ff 28%, #ffffff 100%);
  background-size: 180% 180%;
  background-position: center;
  background-repeat: no-repeat;
}
.project-grid {
  grid-template-columns: repeat(4, 1fr);
}
.project-card :deep(.el-card__header) {
  border-bottom: 1px solid #f0f1f5;
  background: transparent;
}
.project-card :deep(.el-card__footer) {
  background: transparent;
}
</style>
