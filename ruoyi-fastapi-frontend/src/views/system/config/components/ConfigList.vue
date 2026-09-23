<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadConfigData"
    :query-transform="queryTransform"
    :show-pagination="true"
    :load-on-mounted="true"
    fill
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
          <zx-input
            v-model="query.configKey"
            placeholder="请输入参数键名"
            clearable
            style="width: 200px"
            @keyup.enter="() => onSearch({ handleRefresh, updateState })"
          />
          <DictSelect
            v-model="query.configType"
            dict-type="sys_yes_no"
            placeholder="系统内置"
            clearable
            style="width: 200px"
            @change="(v: any) => onFilterChange('configType', v, { handleRefresh, updateState })"
          />
          <el-date-picker
            v-model="query.dateRange"
            value-format="YYYY-MM-DD"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
            @change="(v: any) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
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
              @click="handleUpdate(scope.row)"
              v-hasPermi="['system:config:edit']"
              >修改</el-button
            >
            <el-button
              link
              type="danger"
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
  <ConfigDlg ref="configDlgRef" @confirm="handleRefresh" />
</template>

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue';
import { parseTime } from '@/utils/ruoyi';
import { serializeDateRange } from '@/utils/ruoyi';
import { listConfig, getConfig, delConfig, refreshCache } from '@/api/system/config';
import ConfigDlg from './ConfigDlg.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';

const { proxy } = getCurrentInstance()!;
const { sys_yes_no } = (proxy as any).useDict('sys_yes_no');

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<any>(null);
const configDlgRef = ref<any>(null);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query: Record<string, any>) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
async function loadConfigData(params: Record<string, any>) {
  try {
    return await listConfig(params);
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

/** 刷新列表 */
function handleRefresh() {
  gridListRef.value?.refresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection: any[]) {
  ids.value = selection.map((item) => item.configId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  configDlgRef.value?.open();
}

/** 修改按钮操作 */
async function handleUpdate(row?: any) {
  const configId = row?.configId || ids.value;
  const response = await getConfig(configId);
  const data = response;
  configDlgRef.value?.open(data);
}

/** 删除按钮操作 */
function handleDelete(row?: any) {
  const configIds = row?.configId || ids.value.join(',');
  (proxy as any).$modal
    .confirm('是否确认删除参数编号为"' + configIds + '"的数据项？')
    .then(() => delConfig(configIds))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}

/** 导出按钮操作 */
function handleExport(query: Record<string, any>) {
  (proxy as any).download('system/config/export', query, `config_${new Date().getTime()}.xlsx`);
}

/** 刷新缓存按钮操作 */
async function handleRefreshCache() {
  await refreshCache();
}
</script>
