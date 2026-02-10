<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadPostData"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:post:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:post:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:post:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['system:post:export']"
              >导出</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.postCode"
              placeholder="请输入岗位编码"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.status"
              placeholder="岗位状态"
              clearable
              style="width: 200px"
              @change="(v: any) => onFilterChange('status', v, { handleRefresh, updateState })"
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
              v-model="query.postName"
              placeholder="搜索岗位名称"
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
import { ref, getCurrentInstance } from 'vue'
import { parseTime } from '@/utils/ruoyi'
import { listPost, getPost, delPost } from '@/api/system/post'
import PostDlg from './PostDlg.vue'

const { proxy } = getCurrentInstance()!
const { sys_normal_disable } = (proxy as any).useDict('sys_normal_disable')

const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)
const gridListRef = ref<any>(null)
const postDlgRef = ref<any>(null)

async function loadPostData(params: Record<string, any>) {
  try {
    return await listPost(params)
  } catch (e) {
    return { data: [], total: 0 }
  }
}

function onFilterChange(field: string, value: any, { handleRefresh, updateState }: any) {
  updateState({ [field]: value })
  handleRefresh()
}

function onSearch({ handleRefresh }: any) {
  handleRefresh()
}

function handleRefresh() {
  gridListRef.value?.refresh()
}

function handleSelectionChange(selection: any[]) {
  ids.value = selection.map((item) => item.postId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

function handleAdd() {
  postDlgRef.value?.open()
}

async function handleUpdate(row?: any) {
  const postId = row?.postId || ids.value
  const response = await getPost(postId)
  const data = response
  postDlgRef.value?.open(data)
}

function handleDelete(row?: any) {
  const postIds = row?.postId || ids.value
  ;(proxy as any).$modal
    .confirm('是否确认删除岗位编号为"' + postIds + '"的数据项？')
    .then(() => delPost(postIds))
    .then(() => {
      handleRefresh()
    })
    .catch(() => {})
}

function handleExport(query: Record<string, any>) {
  ;(proxy as any).download('system/post/export', query, `post_${new Date().getTime()}.xlsx`)
}
</script>
