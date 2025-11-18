<template>
  <ZxContentWrap title="设备列表">
    <ZxGridList ref="gridListRef" :load-data="loadDeviceData" class="zx-grid-list--page">
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['device:list:add']"
              >新增</ZxButton
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
              @change="v => onFilterChange('busType', v, { handleRefresh, updateState })"
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
              @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
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

      <template #table="{ grid, refresh: handleRefresh }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="设备编号" align="center" prop="device_id" width="100" />
          <el-table-column label="设备名称" align="center" :show-overflow-tooltip="true">
            <template #default="scope">
              <router-link
                :to="'/device/detail/index/' + scope.row.device_id"
                class="link-type"
              >
                <span>{{ scope.row.device_name }}</span>
              </router-link>
            </template>
          </el-table-column>
          <el-table-column
            label="设备分类"
            align="center"
            prop="category_name"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="总线接口"
            align="center"
            prop="bus_interfaces"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="创建人"
            align="center"
            prop="create_by"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="最后修改时间" align="center" prop="update_time" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.update_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            align="center"
            width="220"
            class-name="small-padding fixed-width"
          >
            <template #default="scope">
              <ZxButton
                link
                type="primary"
                icon="Edit"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['device:list:edit']"
                >编辑</ZxButton
              >
              <ZxMoreAction
                :list="getDeviceMoreActionList()"
                @select="handleMoreActionSelect($event, scope.row, handleRefresh)"
              />
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
  </ZxContentWrap>
</template>

<script setup name="Device">
import { listDevice, delDevice } from '@/api/device/device';
import { checkPermi } from '@/utils/permission';
import { Edit, Delete } from '@element-plus/icons-vue';
import DeviceNameDialog from '@/components/business/Device/DeviceNameDialog.vue';

const { proxy } = getCurrentInstance();
const router = useRouter();

const gridListRef = ref();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);

const createDialogVisible = ref(false);
const createForm = reactive({
  deviceName: '',
  categoryName: '',
  remark: ''
});

async function loadDeviceData(params) {
    const response = await listDevice(params);
    console.log('response', response.data.rows)
    response.list = response.data?.rows || []
    return response

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
  ids.value = selection.map(item => item.device_id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

function handleAdd() {
  createForm.deviceName = '';
  createForm.categoryName = '';
  createForm.remark = '';
  createDialogVisible.value = true;
}

function handleCreateSubmit(data) {
  // 将数据存入 sessionStorage
  sessionStorage.setItem('newDeviceData', JSON.stringify({
    deviceName: data.deviceName,
    categoryName: data.categoryName,
    remark: data.remark
  }));
  // 跳转到详情页
  router.push('/device/detail/index');
}

function handleUpdate(row) {
  router.push(`/device/detail/index/${row.device_id}`);
}

function handleDelete(row) {
  const deviceIds = row?.device_id || ids.value;
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

function getDeviceMoreActionList() {
  const actions = [];
  if (checkPermi(['device:list:edit'])) {
    actions.push({ label: '编辑', eventTag: 'edit', icon: Edit });
  }
  if (checkPermi(['device:list:remove'])) {
    actions.push({ label: '删除', eventTag: 'delete', icon: Delete, danger: true });
  }
  return actions;
}

function handleMoreActionSelect(item, row, handleRefresh) {
  switch (item.eventTag) {
    case 'edit':
      handleUpdate(row);
      break;
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
