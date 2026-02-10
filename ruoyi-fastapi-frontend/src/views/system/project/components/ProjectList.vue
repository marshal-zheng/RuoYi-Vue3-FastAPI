<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadProjectData"
    :query-transform="queryTransform"
    :show-pagination="true"
    :load-on-mounted="true"
    class="zx-grid-list--page"
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <div class="zx-grid-form-bar">
        <div class="zx-grid-form-bar__left">
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
            v-model="query.projectDesc"
            placeholder="搜索工程描述"
            :loading="loading"
            search-mode="click"
            @search="() => onSearch({ handleRefresh, updateState })"
            @clear="() => onSearch({ handleRefresh, updateState })"
          />
        </div>
      </div>
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
  <el-dialog title="工程详情" v-model="detailOpen" width="600px" append-to-body>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="工程编号">{{ detailData.projectId }}</el-descriptions-item>
      <el-descriptions-item label="工程描述">{{ detailData.projectDesc }}</el-descriptions-item>
      <el-descriptions-item label="创建人">{{ detailData.createBy }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ parseTime(detailData.createTime) }}</el-descriptions-item>
      <el-descriptions-item label="更新人">{{ detailData.updateBy }}</el-descriptions-item>
      <el-descriptions-item label="更新时间">{{ parseTime(detailData.updateTime) }}</el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="detailOpen = false">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts" name="ProjectList">
import { listProject, getProject, delProject } from '@/api/system/project';
import { serializeDateRange } from '@/utils/ruoyi';
import ProjectDlg from './ProjectDlg.vue';

const { proxy } = getCurrentInstance();

const ids = ref<number[]>([]);
const multiple = ref(true);
const gridListRef = ref(null);
const projectDlgRef = ref(null);
const detailOpen = ref(false);
const detailData = ref<any>({});

function queryTransform(query: any) {
  return serializeDateRange(query);
}

async function loadProjectData(params: any) {
  try {
    return await listProject(params);
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field: string, value: any, { handleRefresh, updateState }: any) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }: any) {
  handleRefresh();
}

function handleSelectionChange(selection: any[]) {
  ids.value = selection.map((item) => item.projectId);
  multiple.value = !selection.length;
}

function handleAdd() {
  projectDlgRef.value?.open();
}

async function handleUpdate(row?: any) {
  const projectId = row?.projectId || ids.value[0];
  if (!projectId) return;
  
  try {
    const response = await getProject(projectId);
    projectDlgRef.value?.open(response);
  } catch (e) {
    proxy.$modal.msgError('获取数据失败');
  }
}

async function handleDetail(row: any) {
  try {
    const response = await getProject(row.projectId);
    detailData.value = response;
    detailOpen.value = true;
  } catch (e) {
    proxy.$modal.msgError('获取数据失败');
  }
}

function handleDelete(row?: any) {
  const projectIds = row?.projectId || ids.value;
  proxy.$modal
    .confirm('是否确认删除工程编号为"' + projectIds + '"的数据项？')
    .then(() => delProject(projectIds))
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
</script>
