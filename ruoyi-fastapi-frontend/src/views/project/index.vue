<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProjectData"
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
              @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
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

      <template #table="{ grid, refresh: handleRefresh }">
        <div
          v-loading="grid.loading"
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
                    class="mt-0.5 flex-shrink-0"
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
                <ZxMoreAction
                  class="flex-shrink-0"
                  :list="getProjectMoreActionList(project)"
                  @select="handleMoreActionSelect($event, project, handleRefresh)"
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
      </template>
    </ZxGridList>
  </ZxContentWrap>

  <ProjectFormDialog ref="projectDialogRef" @success="handleCreateSuccess" />
</template>

<script setup name="Project">
import { listProject, delProject } from '@/api/project/project';
import { checkPermi } from '@/utils/permission';
import { Document, Delete } from '@element-plus/icons-vue';
import { default as ProjectFormDialog } from './components/ProjectFormDialog.vue';

const { proxy } = getCurrentInstance();

const gridListRef = ref();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);

const projectDialogRef = ref();

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

function handleDelete(row) {
  const projectIds = row.projectId || ids.value;
  proxy.$modal
    .confirm('是否确认删除工程编号为"' + projectIds + '"的数据项？')
    .then(function () {
      return delProject(projectIds);
    })
    .then(() => {
      refreshList();
      proxy.$modal.msgSuccess('删除成功');
    });
}

function getProjectMoreActionList(project) {
  const actions = [];
  if (checkPermi(['project:project:query'])) {
    actions.push({ label: '查看详情', eventTag: 'detail', icon: Document });
  }
  if (checkPermi(['project:project:remove'])) {
    actions.push({ label: '删除工程', eventTag: 'delete', icon: Delete, danger: true });
  }
  return actions;
}

function handleMoreActionSelect(item, project, handleRefresh) {
  switch (item.eventTag) {
    case 'detail':
      handleDetail(project);
      break;
    case 'delete':
      handleDelete(project);
      break;
    default:
      break;
  }
}

function handleCreateSuccess(payload) {
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
</script>
<style scoped>
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
.project-card .text-[#4e5969] {
  color: #4e5969;
}
</style>
