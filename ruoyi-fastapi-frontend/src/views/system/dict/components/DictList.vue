<template>
  <ZxContentWrap fill>
    <DictStatus :types="['sys_normal_disable']" />
    <el-alert
      v-if="listStatus.error"
      :title="listStatus.hasData ? '字典类型列表刷新失败，保留上次结果' : '字典类型列表加载失败'"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="handleRefresh">重试读取</el-button>
    </el-alert>
    <span v-else-if="listStatus.loading && listStatus.hasData" aria-live="polite"
      >正在刷新字典类型列表…</span
    >
    <template #header-right>
      <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:dict:add']"
        >新增</ZxButton
      >
      <ZxButton
        icon="Edit"
        :disabled="single"
        @click="handleUpdate"
        v-hasPermi="['system:dict:edit']"
        >修改</ZxButton
      >
      <ZxButton
        plain
        type="danger"
        icon="Delete"
        :disabled="multiple"
        @click="handleDelete"
        v-hasPermi="['system:dict:remove']"
        :loading="handleDeletePending"
        >删除</ZxButton
      >
      <ZxButton icon="Download" @click="handleExport" v-hasPermi="['system:dict:export']"
        >导出</ZxButton
      >
      <ZxButton
        icon="Refresh"
        @click="handleRefreshCache"
        v-hasPermi="['system:dict:remove']"
        :loading="handleRefreshCachePending"
        >刷新缓存</ZxButton
      >
    </template>

    <ZxGridList
      :key="queryScope?.key"
      ref="gridListRef"
      :load-data="loadDictData"
      :query-transform="queryTransform"
      fill
    >
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
            <DictSelect
              v-model="query.status"
              dict-type="sys_normal_disable"
              placeholder="字典状态"
              clearable
              style="width: 240px; margin-left: 8px"
              @change="(v: unknown) => onFilterChange('status', v, { handleRefresh, updateState })"
            />
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
          <template #empty>{{ listStatus.error ? '字典类型列表加载失败' : '暂无数据' }}</template>
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
          <el-table-column label="备注" prop="remarkText" :show-overflow-tooltip="true">
            <template #default="scope"
              ><RemarkDisplay :value="scope.row.remark" :text="scope.row.remarkText" summary
            /></template>
          </el-table-column>
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
                :loading="handleDeletePending"
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
import RemarkDisplay from '@/components/ui/Remark/RemarkDisplay.vue';
import { useOperation } from '@/utils/operation';
import type { GridListState, ZxGridListInstance } from '@zxio/zxui';
import type { TypeRecord } from '@/api/system/dict/type';
import type { DictTypePageQueryModel } from '@/api/_generated/types.gen';
type ListQuery = DictTypePageQueryModel & { dateRange?: string[] | null };
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { ref, getCurrentInstance, watch } from 'vue';
import { parseTime, serializeDateRange } from '@/utils/ruoyi';
import { listType } from '@/api/system/dict/type';
import { useDictManagement, useDictManagementList } from '@/queries/system/dict-management';
import DictSelect from '@/components/business/DictSelect/index.vue';
import { queryScope } from '@/queries/context';
import type { RequestOptions } from '@zxio/http';
import DictDlg from './DictDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const dictDlgRef = ref<InstanceType<typeof DictDlg> | null>(null);
const { deleteTypes: delType, refreshCache } = useDictManagement(handleRefresh);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query: ListQuery) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 */
const { loadData: loadDictData, status: listStatus } = useDictManagementList(
  async (params: ListLoadParams, options: RequestOptions) => {
    return await listType(
      {
        ...params.query,
        page: params.pager?.page,
        pageSize: params.pager?.size,
      },
      options
    );
  }
);

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
  return gridListRef.value?.refresh();
}

/** 多选框选中数据 */
function handleSelectionChange(selection: TypeRecord[]) {
  ids.value = selection.map((item) => item.dictId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  return dictDlgRef.value?.open().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 修改按钮操作 */
function handleUpdate(row?: TypeRecord) {
  const id = row?.dictId || ids.value[0];
  if (!id) return;
  return dictDlgRef.value?.open(id).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 删除按钮操作 */
const { run: handleDelete, pending: handleDeletePending } = useOperation(
  async (row?: TypeRecord) => {
    const scope = queryScope.value;
    const dictIds = row?.dictId || ids.value.join(',');
    await proxy.$modal
      .confirm('是否确认删除字典编号为"' + dictIds + '"的数据项？')
      .then(() => (scope === queryScope.value ? delType(dictIds) : undefined))

      .catch(() => {});
  }
);

/** 导出按钮操作 */
function handleExport() {
  const snapshot = gridListRef.value?.getStateSnapshot();
  if (!snapshot) return;
  proxy.download(
    'system/dict/type/export',
    queryTransform(snapshot.query as ListQuery),
    `dict_${new Date().getTime()}.xlsx`
  );
}

watch(
  queryScope,
  () => {
    gridListRef.value?.updateState('list', []);
    ids.value = [];
    single.value = true;
    multiple.value = true;
  },
  { flush: 'sync' }
);

/** 刷新缓存按钮操作 */
const { run: handleRefreshCache, pending: handleRefreshCachePending } = useOperation(async () => {
  await refreshCache();
});
</script>
