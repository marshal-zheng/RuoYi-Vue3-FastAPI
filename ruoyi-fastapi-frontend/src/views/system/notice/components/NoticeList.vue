<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadNoticeData"
    :show-pagination="true"
    :load-on-mounted="true"
    fill
  >
    <template #form="listForm">
      <template v-if="listForm.mode === 'request'">
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
              v-model="listForm.draft.createBy"
              placeholder="请输入操作人员"
              clearable
              style="width: 200px"
              @keyup.enter="() => listForm.search()"
            />
            <DictSelect
              dict-type="sys_notice_type"
              :model-value="
                typeof listForm.draft.noticeType === 'string'
                  ? listForm.draft.noticeType
                  : undefined
              "
              @update:model-value="listForm.draft.noticeType = $event"
              placeholder="公告类型"
              clearable
              style="width: 200px"
              @change="() => listForm.search()"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="listForm.draft.noticeTitle"
              placeholder="搜索公告标题"
              :loading="listForm.loading"
              search-mode="click"
              @search="() => listForm.search()"
              @clear="() => listForm.search()"
            />
          </template>
        </ZxListToolbar>
      </template>
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

  <NoticeDlg ref="noticeDlgRef" @success="gridListRef?.reload()" />
</template>

<script setup lang="ts" name="NoticeList">
import { ZxGridList } from '@zxio/zxui/grid-list';
import { useOperation } from '@/utils/operation';
import { getCurrentInstance, ref } from 'vue';
import type { GridListPagerState, GridListSortItem, ZxGridListRequestInstance } from '@zxio/zxui';
import type { NoticeRecord } from '@/api/system/notice';
import type { GetSystemNoticeListSystemNoticeListGetData } from '@/api/_generated/types.gen';
type ListQuery = NonNullable<GetSystemNoticeListSystemNoticeListGetData['query']> & {
  dateRange?: string[] | null;
};
type ListLoadParams = {
  query?: ListQuery;
  pager?: GridListPagerState;
  sort?: readonly GridListSortItem[];
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
const gridListRef = ref<ZxGridListRequestInstance | null>(null);
const noticeDlgRef = ref<InstanceType<typeof NoticeDlg> | null>(null);

async function loadNoticeData(params: ListLoadParams) {
  const query = {
    ...params.query,
    page: params.pager?.page,
    pageSize: params.pager?.size,
    sort: params.sort,
  };
  return listNotice(query);
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
        gridListRef.value?.reload();
      })
      .catch(() => {});
  }
);
</script>
