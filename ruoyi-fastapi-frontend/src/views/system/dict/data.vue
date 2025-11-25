<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadDictData"
      :initial-state="initialState"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:dict:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:dict:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:dict:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['system:dict:export']"
              >导出</ZxButton
            >
            <ZxButton type="warning" icon="Close" @click="handleClose">关闭</ZxButton>
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-select
              v-model="query.dictType"
              placeholder="字典名称"
              style="width: 200px"
              @change="(v) => onFilterChange('dictType', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="item in typeOptions"
                :key="item.dictId"
                :label="item.dictName"
                :value="item.dictType"
              />
            </el-select>
            <el-select
              v-model="query.status"
              placeholder="数据状态"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_normal_disable"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.dictLabel"
              placeholder="搜索字典标签"
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
          <el-table-column label="字典编码" align="center" prop="dictCode" />
          <el-table-column label="字典标签" align="center" prop="dictLabel">
            <template #default="scope">
              <span
                v-if="
                  (scope.row.listClass == '' || scope.row.listClass == 'default') &&
                  (scope.row.cssClass == '' || scope.row.cssClass == null)
                "
                >{{ scope.row.dictLabel }}</span
              >
              <el-tag
                v-else
                :type="scope.row.listClass == 'primary' ? '' : scope.row.listClass"
                :class="scope.row.cssClass"
                >{{ scope.row.dictLabel }}</el-tag
              >
            </template>
          </el-table-column>
          <el-table-column label="字典键值" align="center" prop="dictValue" />
          <el-table-column label="字典排序" align="center" prop="dictSort" />
          <el-table-column label="状态" align="center" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="备注"
            align="center"
            prop="remark"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="创建时间" align="center" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            align="center"
            width="160"
            class-name="small-padding fixed-width"
          >
            <template #default="scope">
              <ZxButton
                type="text"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:dict:edit']"
                >修改</ZxButton
              >
              <ZxButton
                type="text"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:dict:remove']"
                >删除</ZxButton
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>

  <!-- 添加或修改参数配置对话框 -->
  <el-dialog :title="title" v-model="open" width="500px" append-to-body>
    <el-form ref="dataRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="字典类型">
        <el-input v-model="form.dictType" :disabled="true" />
      </el-form-item>
      <el-form-item label="数据标签" prop="dictLabel">
        <el-input v-model="form.dictLabel" placeholder="请输入数据标签" />
      </el-form-item>
      <el-form-item label="数据键值" prop="dictValue">
        <el-input v-model="form.dictValue" placeholder="请输入数据键值" />
      </el-form-item>
      <el-form-item label="样式属性" prop="cssClass">
        <el-input v-model="form.cssClass" placeholder="请输入样式属性" />
      </el-form-item>
      <el-form-item label="显示排序" prop="dictSort">
        <el-input-number v-model="form.dictSort" controls-position="right" :min="0" />
      </el-form-item>
      <el-form-item label="回显样式" prop="listClass">
        <el-select v-model="form.listClass">
          <el-option
            v-for="item in listClassOptions"
            :key="item.value"
            :label="item.label + '(' + item.value + ')'"
            :value="item.value"
          ></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="form.status">
          <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">{{
            dict.label
          }}</el-radio>
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
</template>

<script setup name="Data">
import useDictStore from '@/store/modules/dict';
import { optionselect as getDictOptionselect, getType } from '@/api/system/dict/type';
import { listData, getData, delData, addData, updateData } from '@/api/system/dict/data';

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const gridListRef = ref();
const initialState = ref({ query: {} });
const open = ref(false);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const title = ref('');
const defaultDictType = ref('');
const typeOptions = ref([]);
const route = useRoute();
// 数据标签回显样式
const listClassOptions = ref([
  { value: 'default', label: '默认' },
  { value: 'primary', label: '主要' },
  { value: 'success', label: '成功' },
  { value: 'info', label: '信息' },
  { value: 'warning', label: '警告' },
  { value: 'danger', label: '危险' },
]);

const data = reactive({
  form: {},
  rules: {
    dictLabel: [{ required: true, message: '数据标签不能为空', trigger: 'blur' }],
    dictValue: [{ required: true, message: '数据键值不能为空', trigger: 'blur' }],
    dictSort: [{ required: true, message: '数据顺序不能为空', trigger: 'blur' }],
  },
});

const { form, rules } = toRefs(data);

/** GridList 数据加载 */
async function loadDictData(params) {
  console.log('params', params);
  const response = await listData(params);
  return response;
}

/** 查询字典类型详细 */
function getTypes(dictId) {
  getType(dictId).then((response) => {
    defaultDictType.value = response.data.dictType;
    initialState.value = {
      ...initialState.value,
      query: {
        ...initialState.value.query,
        dictType: defaultDictType.value,
      },
    };
    gridListRef.value?.updateState('query.dictType', defaultDictType.value);
    refreshList();
  });
}

/** 查询字典类型列表 */
function getTypeList() {
  getDictOptionselect().then((response) => {
    typeOptions.value = response.data;
  });
}
/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
}
/** 表单重置 */
function reset() {
  form.value = {
    dictCode: undefined,
    dictLabel: undefined,
    dictValue: undefined,
    cssClass: undefined,
    listClass: 'default',
    dictSort: 0,
    status: '0',
    remark: undefined,
  };
  proxy.resetForm('dataRef');
}
/** 刷新列表 */
function refreshList() {
  gridListRef.value && gridListRef.value.refresh && gridListRef.value.refresh();
}

/** 筛选变化 */
function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  handleRefresh();
}

/** 搜索 */
function onSearch({ handleRefresh }) {
  handleRefresh();
}

/** 返回按钮操作 */
function handleClose() {
  const obj = { path: '/system/dict' };
  proxy.$tab.closeOpenPage(obj);
}
/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = '添加字典数据';
  form.value.dictType = defaultDictType.value;
}
/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.dictCode);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const dictCode = row.dictCode || ids.value;
  getData(dictCode).then((response) => {
    form.value = response.data;
    open.value = true;
    title.value = '修改字典数据';
  });
}
/** 提交按钮 */
function submitForm() {
  proxy.$refs['dataRef'].validate((valid) => {
    if (valid) {
      if (form.value.dictCode != undefined) {
        updateData(form.value).then((response) => {
          useDictStore().removeDict(defaultDictType.value);
          proxy.$modal.msgSuccess('修改成功');
          open.value = false;
          refreshList();
        });
      } else {
        addData(form.value).then((response) => {
          useDictStore().removeDict(defaultDictType.value);
          proxy.$modal.msgSuccess('新增成功');
          open.value = false;
          refreshList();
        });
      }
    }
  });
}
/** 删除按钮操作 */
function handleDelete(row) {
  const dictCodes = row.dictCode || ids.value;
  proxy.$modal
    .confirm('是否确认删除字典编码为"' + dictCodes + '"的数据项？')
    .then(function () {
      return delData(dictCodes);
    })
    .then(() => {
      refreshList();
      proxy.$modal.msgSuccess('删除成功');
      useDictStore().removeDict(defaultDictType.value);
    })
    .catch(() => {});
}
/** 导出按钮操作 */
function handleExport(query) {
  proxy.download(
    'system/dict/data/export',
    {
      dictType: query?.dictType || defaultDictType.value,
      dictLabel: query?.dictLabel,
      status: query?.status,
    },
    `dict_data_${new Date().getTime()}.xlsx`
  );
}

getTypes(route.params && route.params.dictId);
getTypeList();
</script>
