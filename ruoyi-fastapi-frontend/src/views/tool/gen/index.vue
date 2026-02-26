<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadTableData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Download"
              :disabled="multiple"
              @click="handleGenTable"
              v-hasPermi="['tool:gen:code']"
              >生成</ZxButton
            >
            <ZxButton type="primary" icon="Plus" @click="openCreateTable" v-hasRole="['admin']"
              >创建</ZxButton
            >
            <ZxButton
              type="info"
              icon="Upload"
              @click="openImportTable"
              v-hasPermi="['tool:gen:import']"
              >导入</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleEditTable"
              v-hasPermi="['tool:gen:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['tool:gen:remove']"
              >删除</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.tableComment"
              placeholder="请输入表描述"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
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
              v-model="query.tableName"
              placeholder="搜索表名称"
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
          <el-table-column label="序号" type="index" width="50">
            <template #default="scope">
              <span>{{ (grid.page - 1) * grid.size + scope.$index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="表名称" prop="tableName" :show-overflow-tooltip="true" />
          <el-table-column label="表描述" prop="tableComment" :show-overflow-tooltip="true" />
          <el-table-column label="实体" prop="className" :show-overflow-tooltip="true" />
          <el-table-column label="创建时间" prop="createTime" width="160">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" prop="updateTime" width="160">
            <template #default="scope">
              <span>{{ parseTime(scope.row.updateTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="330" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-tooltip content="预览" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="View"
                  @click="handlePreview(scope.row)"
                  v-hasPermi="['tool:gen:preview']"
                ></el-button>
              </el-tooltip>
              <el-tooltip content="编辑" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Edit"
                  @click="handleEditTable(scope.row)"
                  v-hasPermi="['tool:gen:edit']"
                ></el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Delete"
                  @click="handleDelete(scope.row)"
                  v-hasPermi="['tool:gen:remove']"
                ></el-button>
              </el-tooltip>
              <el-tooltip content="同步" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Refresh"
                  @click="handleSynchDb(scope.row)"
                  v-hasPermi="['tool:gen:edit']"
                ></el-button>
              </el-tooltip>
              <el-tooltip content="生成代码" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Download"
                  @click="handleGenTable(scope.row)"
                  v-hasPermi="['tool:gen:code']"
                ></el-button>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 预览界面 -->
    <ZxDialog v-bind="previewDialogProps" v-on="previewDialogEvents">
      <el-tabs v-model="previewState.data.activeName" class="preview-tabs">
        <el-tab-pane
          v-for="(value, key) in previewState.data.codeData"
          :label="key.substring(key.lastIndexOf('/') + 1, key.indexOf('.jinja2'))"
          :name="key.substring(key.lastIndexOf('/') + 1, key.indexOf('.jinja2'))"
          :key="value"
        >
          <div class="preview-content">
            <el-link
              :underline="false"
              icon="DocumentCopy"
              v-copyText="value"
              v-copyText:callback="copyTextSuccess"
              class="copy-link"
              >&nbsp;复制</el-link
            >
            <pre class="code-preview">{{ value }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </ZxDialog>
    <import-table ref="importRef" @ok="handleRefresh" />
    <create-table ref="createRef" @ok="handleRefresh" />
  </ZxContentWrap>
</template>

<script setup name="Gen">
import { listTable, previewTable, delTable, genCode, synchDb } from '@/api/tool/gen';
import { useDialog } from '@zxio/zxui';
import router from '@/router';
import importTable from './importTable';
import createTable from './createTable';

const route = useRoute();
const { proxy } = getCurrentInstance();

const gridListRef = ref(null);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const tableNames = ref([]);
const uniqueId = ref('');

// 使用 useDialog 管理预览对话框
const {
  state: previewState,
  dialogProps: previewDialogProps,
  dialogEvents: previewDialogEvents,
  open: openPreview,
} = useDialog({
  title: '代码预览',
  width: '80%',
  height: '80vh',
  footer: false,
  noContentPadding: true,
  defaultData: () => ({
    codeData: {},
    activeName: 'do.py',
  }),
});

onActivated(() => {
  const time = route.query.t;
  if (time != null && time != uniqueId.value) {
    uniqueId.value = time;
    gridListRef.value?.refresh();
  }
});

/** 加载表数据 */
async function loadTableData(params) {
  const { dateRange, ...restQuery } = params.query || {};
  const queryData = {
    pageNum: params.page,
    pageSize: params.size,
    tableName: restQuery?.tableName,
    tableComment: restQuery?.tableComment,
  };

  // 处理日期范围
  if (Array.isArray(dateRange) && dateRange.length === 2) {
    queryData.beginTime = dateRange[0];
    queryData.endTime = dateRange[1];
  }

  try {
    const response = await listTable(queryData);
    return response;
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}

function handleRefresh() {
  gridListRef.value?.refresh();
}

/** 生成代码操作 */
function handleGenTable(row) {
  const tbNames = row?.tableName || tableNames.value;
  if (!tbNames || tbNames === '') {
    proxy.$modal.msgError('请选择要生成的数据');
    return;
  }
  if (row?.genType === '1') {
    genCode(row.tableName).then(() => {
      proxy.$modal.msgSuccess('成功生成到自定义路径：' + row.genPath);
    });
  } else {
    proxy.$download.zip('/tool/gen/batchGenCode?tables=' + tbNames, 'vfadmin.zip');
  }
}

/** 同步数据库操作 */
function handleSynchDb(row) {
  const tableName = row.tableName;
  proxy.$modal
    .confirm('确认要强制同步"' + tableName + '"表结构吗？')
    .then(() => synchDb(tableName))
    .then(() => {
      proxy.$modal.msgSuccess('同步成功');
      handleRefresh();
    })
    .catch(() => {});
}

/** 打开导入表弹窗 */
function openImportTable() {
  proxy.$refs['importRef'].show();
}

/** 打开创建表弹窗 */
function openCreateTable() {
  proxy.$refs['createRef'].show();
}

/** 预览按钮 */
function handlePreview(row) {
  previewTable(row.tableId).then((response) => {
    openPreview({
      codeData: response,
      activeName: 'do.py',
    });
  });
}

/** 复制代码成功 */
function copyTextSuccess() {
  proxy.$modal.msgSuccess('复制成功');
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.tableId);
  tableNames.value = selection.map((item) => item.tableName);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 修改按钮操作 */
function handleEditTable(row) {
  const tableId = row?.tableId || ids.value[0];
  const currentPage = gridListRef.value?.getState()?.page || 1;
  router.push({
    path: '/tool/gen-edit/index/' + tableId,
    query: { pageNum: currentPage },
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const tableIds = row?.tableId || ids.value;
  proxy.$modal
    .confirm('是否确认删除表编号为"' + tableIds + '"的数据项？')
    .then(() => delTable(tableIds))
    .then(() => {
      handleRefresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
</script>

<style scoped>
.preview-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.preview-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow: auto;
}

.preview-content {
  position: relative;
  height: 100%;
  padding: 16px;
  background-color: var(--el-fill-color-light);
}

.preview-content .copy-link {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 1;
}

.preview-content .code-preview {
  margin: 0;
  padding: 16px;
  background-color: var(--el-bg-color);
  border-radius: 4px;
  overflow: auto;
  max-height: calc(80vh - 200px);
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.5;
}
</style>
