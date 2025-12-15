<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProtocolData"
      :clear-selection-on-load="true"
      class="protocol-grid zx-grid-list--page"
    >
      <!-- 工具栏：左-操作 | 中-筛选 | 右-搜索 -->
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAddProtocol"
              v-hasPermi="['protocol:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleBatchDelete"
              v-hasPermi="['protocol:remove']"
              >批量删除</ZxButton
            >
            <ZxUpload
              ref="importUploadRef"
              v-model="importFileList"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls,.csv,.json"
              :max-size="10 * 1024 * 1024"
              :show-file-list="false"
              :show-tip="false"
              @change="handleImportFileChange"
            >
              <ZxButton
                type="success"
                icon="Upload"
                v-hasPermi="['protocol:add']"
                >导入协议</ZxButton
              >
            </ZxUpload>
          </div>

          <div class="zx-grid-form-bar__filters">
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
          </div>

          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.protocolName"
              placeholder="搜索协议名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
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
    <ProtocolFormDrawer ref="protocolDrawerRef" @success="handleProtocolSaveSuccess" />
  </ZxContentWrap>
</template>

<script setup name="Protocol">
import { listProtocol, delProtocol, addProtocol, updateProtocol, importProtocol } from '@/api/protocol/protocol';
import ProtocolTypeSelector from '@/components/business/Protocol/selector/ProtocolTypeSelector.vue';
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue';
import { validateFile } from '@/utils/io-toolkit';
import { ElMessage } from 'element-plus';

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

// ZxGridList 引用
const gridListRef = ref();

// Drawer 引用
const protocolDrawerRef = ref();

// 选中的协议ID列表
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);

/** ZxGridList 数据加载函数 */
async function loadProtocolData(params) {
  const queryData = {
    pageNum: params.page,
    pageSize: params.size,
    protocolName: params.query?.protocolName || '',
    protocolType: params.query?.protocolType || '',
  };

  // 添加日期范围
  const finalParams = proxy.addDateRange(queryData, params.query?.dateRange || []);

  try {
    const response = await listProtocol(finalParams);
    return {
      data: response.rows || [],
      total: response.total || 0,
    };
  } catch {
    return {
      data: [],
      total: 0,
    };
  }
}

/** 筛选条件变化处理 */
function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}

/** 搜索处理 */
function onSearch({ handleRefresh }) {
  handleRefresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.protocolId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增协议按钮操作 - 打开 Drawer */
function handleAddProtocol() {
  protocolDrawerRef.value?.open();
}

/** 编辑按钮操作 - 打开编辑 Drawer */
function handleDetailPage(row) {
  protocolDrawerRef.value?.open(row);
}

/** 删除按钮操作 */
function handleDelete(row) {
  const protocolIds = row.protocolId || ids.value;
  let confirmMessage = '';

  if (row.protocolId) {
    confirmMessage = '是否确认删除协议"' + row.protocolName + '"？';
  } else {
    const currentData = gridListRef.value?.getData() || [];
    const selectedProtocols = currentData.filter((item) => ids.value.includes(item.protocolId));
    if (selectedProtocols.length === 1) {
      confirmMessage = '是否确认删除协议"' + selectedProtocols[0].protocolName + '"？';
    } else {
      confirmMessage = '是否确认删除选中的 ' + selectedProtocols.length + ' 个协议？';
    }
  }

  proxy.$modal
    .confirm(confirmMessage)
    .then(function () {
      return delProtocol(protocolIds);
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

/** 批量删除按钮操作 */
function handleBatchDelete() {
  if (ids.value.length === 0) {
    proxy.$modal.msgWarning('请选择要删除的协议');
    return;
  }
  handleDelete({});
}

/** 协议保存成功回调 */
const handleProtocolSaveSuccess = async (data) => {
  try {
    if (data.protocolId) {
      await updateProtocol(data);
      proxy.$modal.msgSuccess('修改成功');
    } else {
      await addProtocol(data);
      proxy.$modal.msgSuccess('新增成功');
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

async function handleImportFileChange(fileList) {
  if (!fileList || fileList.length === 0) return;

  const file = fileList[0];
  const fileObj = file.raw || file;

  const formData = new FormData();
  formData.append('file', fileObj);

  try {
    const result = await importProtocol(formData);
    if (result.code === 200) {
      const data = result.data || {};
      ElMessage.success(`导入成功，协议名称：${data.protocolName || '未知'}`);
      gridListRef.value?.refresh();
      // 清空文件列表
      importUploadRef.value?.clearFiles();
      importFileList.value = [];
    } else {
      proxy.$modal.msgError(result.msg || '导入失败');
      // 清空文件列表
      importUploadRef.value?.clearFiles();
      importFileList.value = [];
    }
  } catch (error) {
    proxy.$modal.msgError(error?.message || '导入失败');
    // 清空文件列表
    importUploadRef.value?.clearFiles();
    importFileList.value = [];
  }
}
</script>

<style scoped>
.link-type {
  color: #409eff;
  cursor: pointer;
}
.link-type:hover {
  color: #66b1ff;
}
</style>
