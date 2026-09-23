<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadNoticeData"
    :show-pagination="true"
    :load-on-mounted="true"
    fill
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <div class="zx-grid-form-bar">
        <div class="zx-grid-form-bar__left">
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:notice:add']"
            >新增</ZxButton
          >
          <ZxButton
            type="success"
            :disabled="single"
            @click="handleUpdate"
            v-hasPermi="['system:notice:edit']"
            >修改</ZxButton
          >
          <ZxButton
            type="danger"
            :disabled="multiple"
            @click="handleDelete"
            v-hasPermi="['system:notice:remove']"
            >删除</ZxButton
          >
        </div>
        <div class="zx-grid-form-bar__filters">
          <zx-input
            v-model="query.createBy"
            placeholder="请输入操作人员"
            clearable
            style="width: 200px"
            @keyup.enter="() => onSearch({ handleRefresh, updateState })"
          />
          <el-select
            v-model="query.noticeType"
            placeholder="公告类型"
            clearable
            style="width: 200px"
            @change="(v: any) => onFilterChange('noticeType', v, { handleRefresh, updateState })"
          >
            <el-option
              v-for="dict in sys_notice_type"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </div>
        <div class="zx-grid-form-bar__right">
          <ZxSearch
            v-model="query.noticeTitle"
            placeholder="搜索公告标题"
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
import { listNotice, getNotice, delNotice } from '@/api/system/notice';
import { parseTime } from '@/utils/ruoyi';
import NoticeDlg from './NoticeDlg.vue';

const proxy = getCurrentInstance()?.proxy as any;
const { sys_notice_status, sys_notice_type } = proxy.useDict(
  'sys_notice_status',
  'sys_notice_type'
);

const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref<any>(null);
const noticeDlgRef = ref<any>(null);

async function loadNoticeData(params: any) {
  try {
    return await listNotice(params);
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

function handleSelectionChange(selection: any[]) {
  ids.value = selection.map((item) => item.noticeId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

function handleAdd() {
  noticeDlgRef.value?.open();
}

async function handleUpdate(row?: any) {
  const noticeId = row?.noticeId || ids.value[0];
  if (!noticeId) return;

  const response = await getNotice(noticeId).catch(() => null);
  if (!response) return;
  noticeDlgRef.value?.open(response);
}

function handleDelete(row?: any) {
  const noticeIds = row?.noticeId || ids.value;
  proxy.$modal
    .confirm('是否确认删除公告编号为"' + noticeIds + '"的数据项？')
    .then(() => delNotice(noticeIds))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}
</script>
