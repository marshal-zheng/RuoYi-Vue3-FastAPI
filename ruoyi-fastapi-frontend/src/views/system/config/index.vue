<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadConfigData"
      :query-transform="queryTransform"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:config:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:config:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:config:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['system:config:export']"
              >导出</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Refresh"
              @click="handleRefreshCache"
              v-hasPermi="['system:config:remove']"
              >刷新缓存</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.configKey"
              placeholder="请输入参数键名"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.configType"
              placeholder="系统内置"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('configType', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_yes_no"
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
              style="width: 240px"
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.configName"
              placeholder="搜索参数名称"
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
          <el-table-column label="参数主键" prop="configId" />
          <el-table-column label="参数名称" prop="configName" :show-overflow-tooltip="true" />
          <el-table-column label="参数键名" prop="configKey" :show-overflow-tooltip="true" />
          <el-table-column label="参数键值" prop="configValue" :show-overflow-tooltip="true" />
          <el-table-column label="系统内置" prop="configType">
            <template #default="scope">
              <dict-tag :options="sys_yes_no" :value="scope.row.configType" />
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="remark" :show-overflow-tooltip="true" />
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                icon="Edit"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:config:edit']"
                >修改</el-button
              >
              <el-button
                link
                type="danger"
                icon="Delete"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:config:remove']"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 添加或修改参数配置对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="configRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="参数名称" prop="configName">
          <el-input v-model="form.configName" placeholder="请输入参数名称" />
        </el-form-item>
        <el-form-item label="参数键名" prop="configKey">
          <el-input v-model="form.configKey" placeholder="请输入参数键名" />
        </el-form-item>
        <el-form-item label="参数键值" prop="configValue">
          <el-input v-model="form.configValue" type="textarea" placeholder="请输入参数键值" />
        </el-form-item>
        <el-form-item label="系统内置" prop="configType">
          <el-radio-group v-model="form.configType">
            <el-radio v-for="dict in sys_yes_no" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" />
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

<script setup name="Config">
import { serializeDateRange } from '@/utils/ruoyi';
import {
  listConfig,
  getConfig,
  delConfig,
  addConfig,
  updateConfig,
  refreshCache,
} from '@/api/system/config';

const { proxy } = getCurrentInstance();
const { sys_yes_no } = proxy.useDict('sys_yes_no');

const open = ref(false);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const title = ref('');
const gridListRef = ref(null);

const data = reactive({
  form: {},
  rules: {
    configName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
    configKey: [{ required: true, message: '参数键名不能为空', trigger: 'blur' }],
    configValue: [{ required: true, message: '参数键值不能为空', trigger: 'blur' }],
  },
});

const { form, rules } = toRefs(data);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 - 不处理参数转换 */
async function loadConfigData(params) {
  try {
    return await listConfig(params);
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

/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
}

/** 表单重置 */
function reset() {
  form.value = {
    configId: undefined,
    configName: undefined,
    configKey: undefined,
    configValue: undefined,
    configType: 'Y',
    remark: undefined,
  };
  proxy.resetForm('configRef');
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.configId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = '添加参数';
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const configId = row.configId || ids.value;
  getConfig(configId).then((response) => {
    form.value = response?.data ?? response;
    open.value = true;
    title.value = '修改参数';
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs['configRef'].validate((valid) => {
    if (valid) {
      if (form.value.configId !== undefined) {
        updateConfig(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      } else {
        addConfig(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const configIds = row.configId || ids.value;
  proxy.$modal
    .confirm('是否确认删除参数编号为"' + configIds + '"的数据项？')
    .then(() => delConfig(configIds))
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

/** 导出按钮操作 */
function handleExport(query) {
  proxy.download('system/config/export', query, `config_${new Date().getTime()}.xlsx`);
}

/** 刷新缓存按钮操作 */
function handleRefreshCache() {
  refreshCache().then(() => {
    proxy.$modal.msgSuccess('刷新缓存成功');
  });
}
</script>
