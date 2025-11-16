<template>
  <ZxContentWrap title="字典类型">
    <template #header-right>
      <ZxButton
        type="primary"
        icon="Plus"
        @click="handleAdd"
        v-hasPermi="['system:dict:add']"
      >新增</ZxButton>
      <ZxButton
        type="success"
        icon="Edit"
        :disabled="single"
        @click="handleUpdate"
        v-hasPermi="['system:dict:edit']"
      >修改</ZxButton>
      <ZxButton
        type="danger"
        icon="Delete"
        :disabled="multiple"
        @click="handleDelete"
        v-hasPermi="['system:dict:remove']"
      >删除</ZxButton>
      <ZxButton
        type="warning"
        icon="Download"
        @click="handleExport"
        v-hasPermi="['system:dict:export']"
      >导出</ZxButton>
      <ZxButton
        type="danger"
        icon="Refresh"
        @click="handleRefreshCache"
        v-hasPermi="['system:dict:remove']"
      >刷新缓存</ZxButton>
    </template>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadDictData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.dictType"
              placeholder="字典类型"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.status"
              placeholder="字典状态"
              clearable
              style="width: 240px; margin-left: 8px"
              @change="v => onFilterChange('status', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_normal_disable"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
            <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 308px; margin-left: 8px"
              @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.dictName"
              placeholder="搜索字典名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <template #table="{ grid, refresh: handleRefresh }">
        <el-table v-loading="grid.loading" :data="grid.list || []" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="字典编号" align="center" prop="dictId" />
          <el-table-column label="字典名称" align="center" prop="dictName" :show-overflow-tooltip="true" />
          <el-table-column label="字典类型" align="center" :show-overflow-tooltip="true">
            <template #default="scope">
              <router-link :to="'/system/dict-data/index/' + scope.row.dictId" class="link-type">
                <span>{{ scope.row.dictType }}</span>
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="状态" align="center" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="备注" align="center" prop="remark" :show-overflow-tooltip="true" />
          <el-table-column label="创建时间" align="center" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" width="160" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                icon="Edit"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:dict:edit']"
              >修改</el-button>
              <el-button
                link
                type="primary"
                icon="Delete"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:dict:remove']"
              >删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="dictRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="字典名称" prop="dictName">
          <el-input v-model="form.dictName" placeholder="请输入字典名称" />
        </el-form-item>
        <el-form-item label="字典类型" prop="dictType">
          <el-input v-model="form.dictType" placeholder="请输入字典类型" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">{{ dict.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </ZxContentWrap>
</template>

<script setup name="Dict">
import useDictStore from '@/store/modules/dict';
import {
  listType,
  getType,
  delType,
  addType,
  updateType,
  refreshCache,
} from '@/api/system/dict/type';

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const open = ref(false);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const title = ref('');
const gridListRef = ref();

const data = reactive({
  form: {},
  rules: {
    dictName: [{ required: true, message: '字典名称不能为空', trigger: 'blur' }],
    dictType: [{ required: true, message: '字典类型不能为空', trigger: 'blur' }],
  },
});

const { form, rules } = toRefs(data);

async function loadDictData(params) {
  try {
    const { pageNum, pageSize, ...query } = params || {};
    let requestParams = { pageNum, pageSize, ...query };
    if (query.dateRange && query.dateRange.length === 2) {
      requestParams = proxy.addDateRange(requestParams, query.dateRange);
      delete requestParams.dateRange;
    }
    const response = await listType(requestParams);
    return { list: response.rows || [], total: response.total || 0 };
  } catch (e) {
    return { list: [], total: 0 };
  }
}
function cancel() {
  open.value = false;
  reset();
}
function reset() {
  form.value = {
    dictId: undefined,
    dictName: undefined,
    dictType: undefined,
    status: '0',
    remark: undefined,
  };
  proxy.resetForm('dictRef');
}
function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  handleRefresh();
}
function onSearch({ handleRefresh }) {
  handleRefresh();
}
function handleAdd() {
  reset();
  open.value = true;
  title.value = '添加字典类型';
}
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.dictId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
function handleUpdate(row) {
  reset();
  const dictId = row?.dictId || ids.value;
  getType(dictId).then(response => {
    form.value = response.data;
    open.value = true;
    title.value = '修改字典类型';
  });
}
function submitForm() {
  proxy.$refs['dictRef'].validate(valid => {
    if (valid) {
      if (form.value.dictId != undefined) {
        updateType(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功');
          open.value = false;
          gridListRef.value && gridListRef.value.refresh();
        });
      } else {
        addType(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功');
          open.value = false;
          gridListRef.value && gridListRef.value.refresh();
        });
      }
    }
  });
}
function handleDelete(row) {
  const dictIds = row?.dictId || ids.value;
  proxy.$modal
    .confirm('是否确认删除字典编号为"' + dictIds + '"的数据项？')
    .then(function () {
      return delType(dictIds);
    })
    .then(() => {
      gridListRef.value && gridListRef.value.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
function handleExport() {
  const q = gridListRef.value?.getCurrentQuery?.() || {};
  const query = { ...q };
  if (query.dateRange && query.dateRange.length === 2) {
    const tmp = proxy.addDateRange({}, query.dateRange);
    delete query.dateRange;
    Object.assign(query, tmp);
  }
  proxy.download('system/dict/type/export', query, `dict_${new Date().getTime()}.xlsx`);
}
function handleRefreshCache() {
  refreshCache().then(() => {
    proxy.$modal.msgSuccess('刷新成功');
    useDictStore().cleanDict();
  });
}
</script>
