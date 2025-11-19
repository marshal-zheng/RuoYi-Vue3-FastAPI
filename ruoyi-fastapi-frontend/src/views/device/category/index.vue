<template>
  <ZxContentWrap>
    <ZxGridList ref="gridListRef" :load-data="loadCategoryData" class="zx-grid-list--page">
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAdd"
              v-hasPermi="['device:category:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['device:category:remove']"
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
              style="width: 308px; margin-left: 8px"
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.name"
              placeholder="搜索分类名称"
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
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="分类编号" align="center" prop="device_category_id" width="100" />
          <el-table-column label="分类名称" prop="name" :show-overflow-tooltip="true" />
          <el-table-column label="备注" prop="remark" :show-overflow-tooltip="true" />
          <el-table-column label="创建人" prop="create_by" :show-overflow-tooltip="true" />
          <el-table-column label="创建时间" prop="create_time" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.create_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
            <template #default="scope">
              <zx-button
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['device:category:edit']"
                >修改</zx-button
              >
              <zx-button
                link
                type="danger"
                @click="handleDelete(scope.row)"
                v-hasPermi="['device:category:remove']"
                >删除</zx-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <CategoryFormDialog ref="categoryDialogRef" @success="refreshList" />
  </ZxContentWrap>
</template>

<script setup name="DeviceCategory">
import { listDeviceCategory, delDeviceCategory } from '@/api/device/category';
import { CategoryFormDialog } from '@/components/business/Device';

const { proxy } = getCurrentInstance();

const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref();
const categoryDialogRef = ref();

const data = reactive({});

async function loadCategoryData(params) {
  const response = await listDeviceCategory(params);
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

function handleAdd() {
  categoryDialogRef.value && categoryDialogRef.value.open();
}
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.device_category_id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
function handleUpdate(row) {
  const payload = row?.device_category_id ? { id: row.device_category_id } : { id: ids.value?.[0] };
  categoryDialogRef.value && categoryDialogRef.value.open(payload);
}

function handleDelete(row) {
  const categoryIds = row?.device_category_id || ids.value;
  proxy.$modal
    .confirm('是否确认删除设备分类编号为"' + categoryIds + '"的数据项？')
    .then(function () {
      return delDeviceCategory(categoryIds);
    })
    .then(() => {
      refreshList();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

function refreshList() {
  gridListRef.value && gridListRef.value.refresh();
}
</script>
