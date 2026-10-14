<template>
  <ZxContentWrap fill>
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

    <ZxGridList ref="gridListRef" :load-data="loadDictData" :query-transform="queryTransform" fill>
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #filters>
            <zx-input
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
              @change="(v: unknown) => onFilterChange('status', v, { handleRefresh, updateState })"
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
              @change="
                (v: unknown) => onFilterChange('dateRange', v, { handleRefresh, updateState })
              "
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="query.dictName"
              placeholder="搜索字典名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
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
import type { GridListState, ZxGridListInstance } from '@zxio/zxui';
import type { TypeRecord } from '@/api/system/dict/type';
import type { DictTypePageQueryModel } from '@/api/_generated/types.gen';
type ListQuery = DictTypePageQueryModel & { dateRange?: string[] | null };
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { ref, getCurrentInstance } from 'vue';
import { parseTime, serializeDateRange } from '@/utils/ruoyi';
import { listType, getType, delType, refreshCache } from '@/api/system/dict/type';
import useDictStore from '@/store/modules/dict';
import DictDlg from './DictDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const dictDlgRef = ref<InstanceType<typeof DictDlg> | null>(null);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query: ListQuery) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
async function loadDictData(params: ListLoadParams) {
  try {
    return await listType({
      ...params.query,
      page: params.pager?.page,
      pageSize: params.pager?.size,
    });
  } catch {
    return { items: [], total: 0 };
  }
}

function onFilterChange(key: string, value: unknown, { handleRefresh, updateState }: ListActions) {
  updateState(`query.${key}`, value);
  handleRefresh();
}

function onSearch({
  handleRefresh,
}: {
  handleRefresh: ListActions['handleRefresh'];
  updateState?: ListActions['updateState'];
}) {
  handleRefresh();
}

/** 刷新列表 */
function handleRefresh() {
  gridListRef.value?.refresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection: TypeRecord[]) {
  ids.value = selection.map((item) => item.dictId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  dictDlgRef.value?.open();
}

/** 修改按钮操作 */
async function handleUpdate(row?: TypeRecord) {
  const dictId = row?.dictId || ids.value[0];
  if (!dictId) return;
  const response = await getType(dictId);
  const data = response;
  dictDlgRef.value?.open({
    dictId: data.dictId ?? undefined,
    dictName: data.dictName ?? undefined,
    dictType: data.dictType ?? undefined,
    status: data.status ?? undefined,
    remark: data.remark ?? undefined,
  });
}

/** 删除按钮操作 */
function handleDelete(row?: TypeRecord) {
  const dictIds = row?.dictId || ids.value.join(',');
  proxy.$modal
    .confirm('是否确认删除字典编号为"' + dictIds + '"的数据项？')
    .then(() => delType(dictIds))
    .then(() => {
      handleRefresh();
    })
    .catch(() => {});
}

/** 导出按钮操作 */
function handleExport() {
  const q = gridListRef.value?.getStateSnapshot().query || {};
  proxy.download('system/dict/type/export', q, `dict_${new Date().getTime()}.xlsx`);
}

/** 刷新缓存按钮操作 */
function handleRefreshCache() {
  refreshCache().then(() => {
    useDictStore().cleanDict();
  });
}
</script>
