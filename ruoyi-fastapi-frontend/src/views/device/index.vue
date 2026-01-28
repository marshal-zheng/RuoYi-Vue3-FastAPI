<template>
  <ZxContentWrap>
    <ZxGridList ref="gridListRef" :load-data="loadDeviceData" class="zx-grid-list--page">
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['device:list:add']"
              >新增</ZxButton
            >
            <ZxUpload
              ref="uploadRef"
              v-model="importFileList"
              :auto-upload="false"
              :multiple="true"
              :limit="50"
              accept=".zip,.json"
              button-text="导入设备"
              :max-size="20 * 1024 * 1024"
              :show-file-list="false"
              :show-tip="false"
              :loading="importing"
              v-hasPermi="['device:list:add']"
              @change="handleImportFileChange"
            />
            <ZxButton
              icon="Download"
              :disabled="multiple"
              :loading="exporting"
              @click="handleBatchExport"
              v-hasPermi="['device:list:list']"
              >批量导出</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['device:list:remove']"
              >删除</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-select
              v-model="query.busType"
              placeholder="请选择总线类型"
              clearable
              style="width: 160px"
              @change="(v) => onFilterChange('busType', v, { handleRefresh, updateState })"
            >
              <el-option label="RS422" value="RS422" />
              <el-option label="RS485" value="RS485" />
              <el-option label="CAN" value="CAN" />
              <el-option label="LAN" value="LAN" />
              <el-option label="1553B" value="1553B" />
            </el-select>
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
              v-model="query.deviceName"
              placeholder="搜索设备名称"
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
          <el-table-column type="selection" align="center" width="55" />
          <!-- <el-table-column label="设备编号" align="center" prop="deviceId" width="100" /> -->
          <el-table-column label="设备名称" :show-overflow-tooltip="true">
            <template #default="scope">
              <router-link :to="'/device/detail/index/' + scope.row.deviceId" class="link-type">
                <span>{{ scope.row.deviceName }}</span>
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="设备分类" prop="categoryName" :show-overflow-tooltip="true" />
          <el-table-column label="总线接口" prop="busInterfaces" :show-overflow-tooltip="true" />
          <el-table-column label="创建人" prop="createBy" :show-overflow-tooltip="true" />
          <el-table-column label="最后修改时间" prop="updateTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.updateTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
            <template #default="scope">
              <div class="op-col__wrap">
                <ZxButton
                  link
                  type="primary"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['device:list:edit']"
                  >编辑</ZxButton
                >
                <ZxButton
                  link
                  type="primary"
                  @click="handleClone(scope.row)"
                  v-hasPermi="['device:list:add']"
                  >克隆</ZxButton
                >
                <ZxMoreAction
                  :list="getMoreActionList(scope.row)"
                  @select="handleMoreActionSelect($event, scope.row)"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <DeviceNameDialog
      v-model="createDialogVisible"
      :value="createForm"
      :is-create="true"
      @submit="handleCreateSubmit"
    />

    <DeviceCloneDialog ref="cloneDialogRef" />
  </ZxContentWrap>
</template>

<script setup name="Device">
import { listDevice, delDevice, importDeviceBatch } from '@/api/device/device';
import { download } from '@/utils/request';
import DeviceNameDialog from '@/components/business/Device/DeviceNameDialog.vue';
import DeviceCloneDialog from '@/components/business/Device/DeviceCloneDialog.vue';

const { proxy } = getCurrentInstance();
const router = useRouter();

const gridListRef = ref();
const cloneDialogRef = ref();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const uploadRef = ref();
const importFileList = ref([]);
const exporting = ref(false);
const importing = ref(false);
let importTimer = null;

const createDialogVisible = ref(false);
const createForm = reactive({
  deviceName: '',
  categoryName: '',
  remark: '',
});

async function loadDeviceData(params) {
  const response = await listDevice(params);
  return response;
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  updateState('pager.page', 1);
  handleRefresh();
}

function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}

function refreshList() {
  gridListRef.value && gridListRef.value.refresh();
}

function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.deviceId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

function handleBatchExport() {
  if (multiple.value) {
    proxy.$modal.msgWarning('请先选择需要导出的设备');
    return;
  }
  exporting.value = true;
  download(
    '/device/export/batch',
    { deviceIds: ids.value },
    `device_export_${Date.now()}.zip`,
    { headers: { 'Content-Type': 'application/json' } }
  ).finally(() => {
    exporting.value = false;
  });
}

// 文件变化时使用防抖，等待所有文件选择完成再导入（避免只提交第一个文件）
function handleImportFileChange(fileList) {
  if (!fileList || fileList.length === 0) return;
  if (importing.value) return;

  if (importTimer) clearTimeout(importTimer);
  importTimer = setTimeout(() => {
    // 优先使用 v-model 的最终列表，避免 change 事件逐个触发时拿到的只是局部列表
    doImportFiles(importFileList.value?.length ? importFileList.value : fileList);
  }, 100);
}

async function doImportFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  if (importing.value) return;
  importing.value = true;

  const formData = new FormData();
  fileList.forEach((file) => {
    const fileObj = file.raw || file;
    formData.append('files', fileObj);
  });

  try {
    // http 客户端已解包 payload.data，res 直接是导入结果
    const res = await importDeviceBatch(formData) || {};
    const success = res.successCount || 0;
    const failed = res.failedCount || 0;
    if (failed === 0) {
      proxy.$modal.msgSuccess(`导入成功，共 ${success} 条`);
    } else if (success > 0) {
      proxy.$modal.msgWarning(`部分成功：成功 ${success} 条，失败 ${failed} 条`);
    } else {
      proxy.$modal.msgError('导入失败');
    }
    refreshList();
  } catch (err) {
    proxy.$modal.msgError(err?.message || '导入失败');
  } finally {
    importing.value = false;
    if (importTimer) {
      clearTimeout(importTimer);
      importTimer = null;
    }
    uploadRef.value && uploadRef.value.clearFiles();
    importFileList.value = [];
  }
}

function handleAdd() {
  createForm.deviceName = '';
  createForm.categoryName = '';
  createForm.remark = '';
  createDialogVisible.value = true;
}

function handleCreateSubmit(data) {
  // 将数据存入 sessionStorage
  sessionStorage.setItem(
    'newDeviceData',
    JSON.stringify({
      deviceName: data.deviceName,
      categoryName: data.categoryName,
      remark: data.remark,
    })
  );
  // 跳转到详情页
  router.push('/device/detail/index');
}

function handleUpdate(row) {
  router.push(`/device/detail/index/${row.deviceId}`);
}

function handleDelete(row) {
  const deviceIds = row?.deviceId || ids.value;
  proxy.$modal
    .confirm('是否确认删除设备编号为"' + deviceIds + '"的数据项？')
    .then(function () {
      return delDevice(deviceIds);
    })
    .then(() => {
      refreshList();
      proxy.$modal.msgSuccess('删除成功');
    });
}

function handleClone(row) {
  cloneDialogRef.value.open(row, () => {
    refreshList();
  });
}

function getMoreActionList() {
  const actions = [];
  actions.push({
    label: '删除',
    eventTag: 'delete',
    icon: 'Delete',
    danger: true,
    permission: 'device:list:remove',
  });
  return actions;
}

function handleMoreActionSelect(item, row) {
  switch (item.eventTag) {
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>

<style scoped>
.op-col__wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.device-import-upload {
  display: none;
}
</style>
