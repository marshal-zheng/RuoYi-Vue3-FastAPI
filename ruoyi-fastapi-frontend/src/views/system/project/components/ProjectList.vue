<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadProjectData"
    :query-transform="queryTransform"
    :show-pagination="true"
    :load-on-mounted="true"
    fill
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <ZxListToolbar aria-label="列表操作与筛选">
        <template #actions>
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:project:add']"
            >新增</ZxButton
          >
          <ZxButton
            type="danger"
            :disabled="multiple"
            @click="handleDelete"
            v-hasPermi="['system:project:remove']"
            >删除</ZxButton
          >
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
            @change="(v: unknown) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
          />
        </template>
        <template #search>
          <ZxSearch
            v-model="query.projectDesc"
            placeholder="搜索工程描述"
            :loading="loading"
            search-mode="click"
            @search="() => onSearch({ handleRefresh, updateState })"
            @clear="() => onSearch({ handleRefresh, updateState })"
          />
        </template>
      </ZxListToolbar>
    </template>

    <template #table="{ grid }">
      <el-table
        v-loading="grid.loading"
        :data="grid.list || []"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="工程编号" prop="projectId" width="100" />
        <el-table-column label="工程描述" prop="projectDesc" :show-overflow-tooltip="true" />
        <el-table-column label="创建人" prop="createBy" width="120" />
        <el-table-column label="创建时间" prop="createTime" width="180">
          <template #default="scope">
            <span>{{ parseTime(scope.row.createTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" prop="updateTime" width="180">
          <template #default="scope">
            <span>{{ parseTime(scope.row.updateTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-button
              link
              type="primary"
              @click="handleDetail(scope.row)"
              v-hasPermi="['system:project:query']"
              >详情</el-button
            >
            <el-button
              link
              type="primary"
              @click="handleUpdate(scope.row)"
              v-hasPermi="['system:project:edit']"
              >修改</el-button
            >
            <el-button
              link
              type="danger"
              @click="handleDelete(scope.row)"
              v-hasPermi="['system:project:remove']"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </template>
  </ZxGridList>

  <ProjectDlg ref="projectDlgRef" @success="gridListRef?.refresh()" />

  <!-- 工程详情对话框 -->
  <ZxDialog
    dialog-size="md"
    :draggable="false"
    :show-full-screen="false"
    :destroy-on-close="false"
    :close-on-click-modal="true"
    title="工程详情"
    v-model="detailOpen"
  >
    <el-descriptions :column="1" border>
      <el-descriptions-item label="工程编号">{{ detailData.projectId }}</el-descriptions-item>
      <el-descriptions-item label="工程描述">{{ detailData.projectDesc }}</el-descriptions-item>
      <el-descriptions-item label="创建人">{{ detailData.createBy }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{
        parseTime(detailData.createTime ?? undefined)
      }}</el-descriptions-item>
      <el-descriptions-item label="更新人">{{ detailData.updateBy }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{
        parseTime(detailData.updateTime ?? undefined)
      }}</el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="detailOpen = false">关 闭</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup lang="ts" name="ProjectList">
import { getCurrentInstance, ref } from 'vue';
import type { GridListState, ZxGridListInstance } from '@zxio/zxui';
import type { ProjectRecord } from '@/api/system/project';
import type { GetSystemProjectListProjectListGetData } from '@/api/_generated/types.gen';
type ListQuery = NonNullable<GetSystemProjectListProjectListGetData['query']> & {
  dateRange?: string[] | null;
};
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { listProject, getProject, delProject } from '@/api/system/project';
import { parseTime, serializeDateRange } from '@/utils/ruoyi';
import ProjectDlg from './ProjectDlg.vue';

const proxy = getCurrentInstance()!.proxy!;

const ids = ref<number[]>([]);
const multiple = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const projectDlgRef = ref<InstanceType<typeof ProjectDlg> | null>(null);
const detailOpen = ref(false);
const detailData = ref<Partial<ProjectRecord>>({});

function queryTransform(query: ListQuery) {
  return serializeDateRange(query);
}

async function loadProjectData(params: ListLoadParams) {
  try {
    return await listProject({
      ...params.query,
      page: params.pager?.page,
      pageSize: params.pager?.size,
    });
  } catch {
    return { data: [], total: 0 };
  }
}

function onFilterChange(
  field: string,
  value: unknown,
  { handleRefresh, updateState }: ListActions
) {
  updateState(`query.${field}`, value);
  handleRefresh();
}

function onSearch({
  handleRefresh,
}: {
  handleRefresh: ListActions['handleRefresh'];
  updateState?: ListActions['updateState'];
}) {
  handleRefresh();
}

function handleSelectionChange(selection: ProjectRecord[]) {
  ids.value = selection.map((item) => item.projectId);
  multiple.value = !selection.length;
}

function handleAdd() {
  projectDlgRef.value?.open();
}

async function handleUpdate(row?: ProjectRecord) {
  const projectId = row?.projectId || ids.value[0];
  if (!projectId) return;

  const response = await getProject(projectId).catch(() => null);
  if (!response) return;
  projectDlgRef.value?.open({
    projectId: response.projectId ?? undefined,
    projectDesc: response.projectDesc ?? undefined,
  });
}

async function handleDetail(row: ProjectRecord) {
  const response = await getProject(row.projectId).catch(() => null);
  if (!response) return;
  detailData.value = response;
  detailOpen.value = true;
}

function handleDelete(row?: ProjectRecord) {
  const projectIds = row?.projectId || ids.value.join(',');
  proxy.$modal
    .confirm('是否确认删除工程编号为"' + projectIds + '"的数据项？')
    .then(() => delProject(projectIds))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}
</script>
