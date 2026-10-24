<template>
  <ZxContentWrap fill>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProtocolData"
      :query-transform="queryTransform"
      :clear-selection-on-load="true"
      class="protocol-grid"
      fill
    >
      <!-- 工具栏：左-操作 | 中-筛选 | 右-搜索 -->
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <DictStatus :types="['sys_normal_disable']" />
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAddProtocol"
              v-hasPermi="['protocol:add']"
              >新增</ZxButton
            >
            <ZxUpload
              ref="importUploadRef"
              v-model="importFileList"
              :auto-upload="false"
              :limit="50"
              :multiple="true"
              accept=".xlsx,.xls,.csv,.json"
              button-text="导入协议"
              :max-size="10 * 1024 * 1024"
              :show-file-list="false"
              :show-tip="false"
              v-hasPermi="['protocol:add']"
              @change="handleImportFileChange"
            />
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleBatchDelete"
              v-hasPermi="['protocol:remove']"
              >批量删除</ZxButton
            >
          </template>

          <template #filters>
            <ProtocolTypeSelector
              v-model="query.protocolType"
              placeholder="请选择协议类型"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('protocolType', v, { handleRefresh, updateState })"
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
          </template>

          <template #search>
            <ZxSearch
              v-model="query.protocolName"
              placeholder="搜索协议名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
      </template>

      <!-- 表格内容 -->
      <template #table="{ grid }">
        <el-table :data="grid.list" style="width: 100%" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column label="协议编号" prop="protocolId" width="100" />
          <el-table-column label="协议名称" :show-overflow-tooltip="true">
            <template #default="scope">
              <span class="link-type">{{ scope.row.protocolName }}</span>
            </template>
          </el-table-column>
          <el-table-column label="协议类型" prop="protocolType" :show-overflow-tooltip="true" />

          <el-table-column label="状态" prop="status" width="100">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>

          <el-table-column
            label="创建人"
            align="center"
            prop="createBy"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="最后修改时间" prop="updateTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.updateTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" class-name="small-padding fixed-width">
            <template #default="scope">
              <div class="op-col__wrap">
                <el-button
                  type="text"
                  @click="handleDetailPage(scope.row)"
                  v-hasPermi="['protocol:query']"
                  >编辑</el-button
                >
                <zx-button
                  type="text"
                  @click="handleExport(scope.row)"
                  v-hasPermi="['protocol:export']"
                  >导出协议</zx-button
                >
                <ZxMoreAction
                  :list="getMoreActionList()"
                  @select="handleMoreActionSelect($event, scope.row)"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 协议表单 Drawer -->
    <ProtocolFormDrawer ref="protocolDrawerRef" :save="handleProtocolSaveSuccess" />
  </ZxContentWrap>
</template>

<script setup name="Protocol">
import { useOperation } from '@/utils/operation';
import { serializeDateRange } from '@/utils/ruoyi';
import {
  listProtocol,
  delProtocolBatch,
  addProtocol,
  updateProtocol,
  importProtocolBatch,
} from '@/api/protocol/protocol';
import ProtocolTypeSelector from '@/components/business/Protocol/selector/ProtocolTypeSelector.vue';
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue';
import { ElMessage } from 'element-plus';

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

// ZxGridList 引用
const gridListRef = ref();

// Drawer 引用
const protocolDrawerRef = ref();

// 选中的协议ID列表
const ids = ref([]);
// 选中的行数据，避免依赖 gridListRef 内部实现
const selectedRows = ref([]);
const single = ref(true);
const multiple = ref(true);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
async function loadProtocolData(params) {
  const response = await listProtocol(params);
  return response;
}

/** 筛选条件变化处理 */
function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState(`query.${field}`, value);
  handleRefresh();
}

/** 搜索处理 */
function onSearch({ handleRefresh }) {
  handleRefresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.protocolId);
  selectedRows.value = selection;
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增协议按钮操作 - 打开 Drawer */
function handleAddProtocol() {
  protocolDrawerRef.value?.open();
}

/** 编辑按钮操作 - 打开编辑 Drawer */
function handleDetailPage(row) {
  protocolDrawerRef.value?.open(row).catch(() => {
    /* 详情读取已负责反馈。 */
  });
}

/** 删除按钮操作 */
const { run: handleDelete } = useOperation(async (row) => {
  const protocolIdsRaw = row.protocolId ? [row.protocolId] : ids.value;
  const protocolIds = (protocolIdsRaw || []).filter((id) => id !== undefined && id !== null);
  let confirmMessage = '';

  if (row?.protocolId) {
    confirmMessage = '是否确认删除协议"' + row.protocolName + '"？';
  } else {
    const selectedProtocols = selectedRows.value || [];
    if (selectedProtocols.length === 1) {
      confirmMessage = '是否确认删除协议"' + selectedProtocols[0].protocolName + '"？';
    } else {
      confirmMessage = '是否确认删除选中的 ' + selectedProtocols.length + ' 个协议？';
    }
  }
  await proxy.$modal
    .confirm(confirmMessage)
    .then(function () {
      if (!protocolIds || protocolIds.length === 0) {
        return Promise.reject(new Error('no_ids'));
      }
      // 单个仍可用批量接口，保持一致的结果结构
      return delProtocolBatch(protocolIds);
    })
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch((err) => {
      if (err?.message === 'no_ids') return;
    });
});

/** 批量删除按钮操作 */
function handleBatchDelete() {
  console.log('ids', ids);
  if (ids.value.length === 0) {
    ElMessage.warning('请选择要删除的协议');
    return;
  }
  handleDelete({});
}

/** 协议保存成功回调 */
const handleProtocolSaveSuccess = async (data) => {
  try {
    if (data.protocolId) {
      await updateProtocol(data);
    } else {
      await addProtocol(data);
    }
    protocolDrawerRef.value?.close();
    gridListRef.value?.refresh();
  } catch (error) {
    throw error;
  }
};

/** 获取更多操作列表 */
function getMoreActionList() {
  return [
    {
      label: '删除',
      eventTag: 'delete',
      icon: 'Delete',
      danger: true,
      permission: 'protocol:remove',
    },
  ];
}

/** 更多操作选择处理 */
function handleMoreActionSelect(item, row) {
  if (item.eventTag === 'delete') {
    handleDelete(row);
  }
}

/** 导出协议配置 */
function handleExport(row) {
  proxy.download(
    'system/protocol/export',
    {
      protocolId: row.protocolId,
    },
    `协议配置_${row.protocolName}_${new Date().getTime()}.xlsx`
  );
}

// ========== 协议导入功能 ==========
const importUploadRef = ref(null);
const importFileList = ref([]);
const importing = ref(false);
let importTimer = null;

// 文件变化时使用防抖，等待所有文件选择完成
function handleImportFileChange(fileList) {
  if (!fileList || fileList.length === 0) return;
  if (importing.value) return;

  // 防抖：等待文件选择稳定后再执行导入
  if (importTimer) {
    clearTimeout(importTimer);
  }
  importTimer = setTimeout(() => {
    doImportFiles(fileList);
  }, 100);
}

// 实际执行批量导入
async function doImportFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  if (importing.value) return;

  importing.value = true;

  const formData = new FormData();
  fileList.forEach((file) => {
    const fileObj = file.raw || file;
    formData.append('files', fileObj);
  });

  let successCount = 0;

  try {
    const result = await importProtocolBatch(formData);
    const batchResults = Array.isArray(result?.results) ? result.results : [];
    successCount = batchResults.filter((item) => item.success).length;
  } catch {
    successCount = 0;
  }

  // 清空文件列表
  importUploadRef.value?.clearFiles();
  importFileList.value = [];
  importing.value = false;

  // 刷新列表
  if (successCount > 0) {
    gridListRef.value?.refresh();
  }
}
</script>

<style scoped>
.link-type {
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
  cursor: pointer;
}
.link-type:hover {
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
  text-decoration: underline;
}
</style>
