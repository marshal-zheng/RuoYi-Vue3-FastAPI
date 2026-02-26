<template>
  <ZxContentWrap>
    <template #header-right>
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
        @click="handleExport"
        v-hasPermi="['system:dict:export']"
        >导出</ZxButton
      >
      <ZxButton
        type="danger"
        icon="Refresh"
        @click="handleRefreshCache"
        v-hasPermi="['system:dict:remove']"
        >刷新缓存</ZxButton
      >
    </template>

    <ZxGridList
      ref="gridListRef"
      :load-data="loadDictData"
      :query-transform="queryTransform"
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
              @change="(v: any) => onFilterChange('status', v, { handleRefresh, updateState })"
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
              @change="(v: any) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
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

      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column label="字典编号" prop="dictId" />
          <el-table-column label="字典名称" prop="dictName" :show-overflow-tooltip="true" />
          <el-table-column label="字典类型" :show-overflow-tooltip="true">
            <template #default="scope">
              <router-link :to="'/system/dict-data/index/' + scope.row.dictId" class="link-type">
                <span>{{ scope.row.dictType }}</span>
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="remark" :show-overflow-tooltip="true" />
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:dict:edit']"
                >修改</el-button
              >
              <el-button
                link
                type="danger"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:dict:remove']"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <DictDlg ref="dictDlgRef" @confirm="handleRefresh" />
  </ZxContentWrap>
</template>

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue';
import { parseTime, serializeDateRange } from '@/utils/ruoyi';
import { listType, getType, delType, refreshCache } from '@/api/system/dict/type';
import useDictStore from '@/store/modules/dict';
import DictDlg from './DictDlg.vue';

const { proxy } = getCurrentInstance()!;
const { sys_normal_disable } = (proxy as any).useDict('sys_normal_disable');

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<any>(null);
const dictDlgRef = ref<any>(null);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query: Record<string, any>) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
async function loadDictData(params: Record<string, any>) {
  try {
    return await listType(params);
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(key: string, value: any, { handleRefresh, updateState }: any) {
  updateState({ [key]: value });
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
  ids.value = selection.map((item) => item.dictId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  dictDlgRef.value?.open();
}

/** 修改按钮操作 */
async function handleUpdate(row?: any) {
  const dictId = row?.dictId || ids.value;
  const response = await getType(dictId);
  const data = response;
  dictDlgRef.value?.open(data);
}

/** 删除按钮操作 */
function handleDelete(row?: any) {
  const dictIds = row?.dictId || ids.value;
  (proxy as any).$modal
    .confirm('是否确认删除字典编号为"' + dictIds + '"的数据项？')
    .then(() => delType(dictIds))
    .then(() => {
      handleRefresh();
      (proxy as any).$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

/** 导出按钮操作 */
function handleExport() {
  const q = gridListRef.value?.getCurrentQuery?.() || {};
  (proxy as any).download('system/dict/type/export', q, `dict_${new Date().getTime()}.xlsx`);
}

/** 刷新缓存按钮操作 */
function handleRefreshCache() {
  refreshCache().then(() => {
    (proxy as any).$modal.msgSuccess('刷新成功');
    useDictStore().cleanDict();
  });
}
</script>
