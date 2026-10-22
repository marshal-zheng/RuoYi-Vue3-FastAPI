<template>
  <ZxContentWrap fill>
    <ZxGridList ref="gridListRef" :load-data="loadPostData" :load-on-mounted="true" fill>
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <DictStatus :types="['sys_normal_disable']" />
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:post:add']"
              >新增</ZxButton
            >
            <ZxButton
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:post:edit']"
              >修改</ZxButton
            >
            <ZxButton
              plain
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:post:remove']"
              :loading="handleDeletePending"
              >删除</ZxButton
            >
            <ZxButton
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['system:post:export']"
              >导出</ZxButton
            >
          </template>
          <template #filters>
            <zx-input
              v-model="query.postCode"
              placeholder="请输入岗位编码"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <DictSelect
              dict-type="sys_normal_disable"
              v-model="query.status"
              placeholder="岗位状态"
              clearable
              style="width: 200px"
              @change="(v: unknown) => onFilterChange('status', v, { handleRefresh, updateState })"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="query.postName"
              placeholder="搜索岗位名称"
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
          <el-table-column label="岗位编号" prop="postId" />
          <el-table-column label="岗位编码" prop="postCode" />
          <el-table-column label="岗位名称" prop="postName" />
          <el-table-column label="岗位排序" prop="postSort" />
          <el-table-column label="状态" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:post:edit']"
                >修改</el-button
              >
              <el-button
                link
                type="danger"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:post:remove']"
                :loading="handleDeletePending"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <PostDlg ref="postDlgRef" @confirm="handleRefresh" />
  </ZxContentWrap>
</template>

<script setup lang="ts">
import { useOperation } from '@/utils/operation';
import { getCurrentInstance, ref } from 'vue';
import type { GridListState, ZxGridListInstance } from '@zxio/zxui';
import type { PostRecord } from '@/api/system/post';
import type { PostPageQueryModel } from '@/api/_generated/types.gen';
type ListQuery = PostPageQueryModel & { dateRange?: string[] | null };
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { parseTime } from '@/utils/ruoyi';
import { listPost, delPost } from '@/api/system/post';
import PostDlg from './PostDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const postDlgRef = ref<InstanceType<typeof PostDlg> | null>(null);

async function loadPostData(params: ListLoadParams) {
  try {
    return await listPost({
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

function handleRefresh() {
  gridListRef.value?.refresh();
}

function handleSelectionChange(selection: PostRecord[]) {
  ids.value = selection.map((item) => item.postId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

function handleAdd() {
  return postDlgRef.value?.open().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

function handleUpdate(row?: PostRecord) {
  const id = row?.postId || ids.value[0];
  if (!id) return;
  return postDlgRef.value?.open(id).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

const { run: handleDelete, pending: handleDeletePending } = useOperation(
  async (row?: PostRecord) => {
    const postIds = row?.postId || ids.value.join(',');
    await proxy.$modal
      .confirm('是否确认删除岗位编号为"' + postIds + '"的数据项？')
      .then(() => delPost(postIds))
      .then(() => {
        handleRefresh();
      })
      .catch(() => {});
  }
);

function handleExport(query: ListQuery) {
  proxy.download('system/post/export', query, `post_${new Date().getTime()}.xlsx`);
}
</script>
