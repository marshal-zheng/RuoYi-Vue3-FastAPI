<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadNoticeData"
    :show-pagination="true"
    :load-on-mounted="true"
    fill
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <DictStatus :types="['sys_notice_status', 'sys_notice_type']" />
      <ZxListToolbar aria-label="列表操作与筛选">
        <template #actions>
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:notice:add']"
            >新增</ZxButton
          >
          <ZxButton :disabled="single" @click="handleUpdate" v-hasPermi="['system:notice:edit']"
            >修改</ZxButton
          >
          <ZxButton
            plain
            type="danger"
            :disabled="multiple"
            @click="handleDelete"
            v-hasPermi="['system:notice:remove']"
            :loading="handleDeletePending"
            >删除</ZxButton
          >
        </template>
        <template #filters>
          <zx-input
            v-model="query.createBy"
            placeholder="请输入操作人员"
            clearable
            style="width: 200px"
            @keyup.enter="() => onSearch({ handleRefresh, updateState })"
          />
          <DictSelect
            dict-type="sys_notice_type"
            v-model="query.noticeType"
            placeholder="公告类型"
            clearable
            style="width: 200px"
            @change="
              (v: unknown) => onFilterChange('noticeType', v, { handleRefresh, updateState })
            "
          />
        </template>
        <template #search>
          <ZxSearch
            v-model="query.noticeTitle"
            placeholder="搜索公告标题"
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
        <el-table-column label="序号" prop="noticeId" width="100" />
        <el-table-column label="公告标题" prop="noticeTitle" :show-overflow-tooltip="true" />
        <el-table-column label="公告类型" prop="noticeType" width="100">
          <template #default="scope">
            <dict-tag :options="sys_notice_type" :value="scope.row.noticeType" />
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="status" width="100">
          <template #default="scope">
            <dict-tag :options="sys_notice_status" :value="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column label="创建者" prop="createBy" width="100" />
        <el-table-column label="创建时间" prop="createTime" width="180">
          <template #default="scope">
            <span>{{ parseTime(scope.row.createTime, '{y}-{m}-{d}') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-button
              link
              type="primary"
              @click="handleUpdate(scope.row)"
              v-hasPermi="['system:notice:edit']"
              >修改</el-button
            >
            <el-button
              link
              type="danger"
              @click="handleDelete(scope.row)"
              v-hasPermi="['system:notice:remove']"
              :loading="handleDeletePending"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </template>
  </ZxGridList>

  <NoticeDlg ref="noticeDlgRef" @success="gridListRef?.refresh()" />
</template>

<script setup lang="ts" name="NoticeList">
import { useOperation } from '@/utils/operation';
import { getCurrentInstance, ref } from 'vue';
import type { GridListState, ZxGridListInstance } from '@zxio/zxui';
import type { NoticeRecord } from '@/api/system/notice';
import type { GetSystemNoticeListSystemNoticeListGetData } from '@/api/_generated/types.gen';
type ListQuery = NonNullable<GetSystemNoticeListSystemNoticeListGetData['query']> & {
  dateRange?: string[] | null;
};
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { listNotice, delNotice } from '@/api/system/notice';
import { parseTime } from '@/utils/ruoyi';
import NoticeDlg from './NoticeDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_notice_status, sys_notice_type } = proxy.useDict(
  'sys_notice_status',
  'sys_notice_type'
);

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const noticeDlgRef = ref<InstanceType<typeof NoticeDlg> | null>(null);

async function loadNoticeData(params: ListLoadParams) {
  try {
    return await listNotice({
      ...params.query,
      page: params.pager?.page,
      pageSize: params.pager?.size,
    });
  } catch {
    return { data: [], total: 0 };
  }
}

function onFilterChange(
  field: string,
  value: unknown,
  { handleRefresh, updateState }: ListActions
) {
  updateState(`query.${field}`, value);
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

function handleSelectionChange(selection: NoticeRecord[]) {
  ids.value = selection.map((item) => item.noticeId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

function handleAdd() {
  return noticeDlgRef.value?.open().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

function handleUpdate(row?: NoticeRecord) {
  const id = row?.noticeId || ids.value[0];
  if (!id) return;
  return noticeDlgRef.value?.open(id).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

const { run: handleDelete, pending: handleDeletePending } = useOperation(
  async (row?: NoticeRecord) => {
    const noticeIds = row?.noticeId || ids.value.join(',');
    await proxy.$modal
      .confirm('是否确认删除公告编号为"' + noticeIds + '"的数据项？')
      .then(() => delNotice(noticeIds))
      .then(() => {
        gridListRef.value?.refresh();
      })
      .catch(() => {});
  }
);
</script>
