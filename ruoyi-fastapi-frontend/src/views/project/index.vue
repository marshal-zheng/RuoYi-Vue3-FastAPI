<template>
  <ZxContentWrap title="工程管理">
    <ZxGridList
      ref="gridListRef"
      :load-data="loadProjectData"
      class="project-grid zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAdd"
              v-hasPermi="['project:project:add']"
            >新增</ZxButton>
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['project:project:remove']"
            >删除</ZxButton>
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
              @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.projectName"
              placeholder="搜索工程名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <template #table="{ grid, refresh: handleRefresh }">
        <div v-loading="grid.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-5">
          <div
            v-for="project in grid.list"
            :key="project.projectId"
            class="group relative bg-white rounded-sm border border-[#e5e6eb] hover:border-[#0052d9] transition-all duration-300 overflow-hidden"
            :class="{
              'border-[#0052d9] shadow-[0_0_0_2px_rgba(0,82,217,0.1)]': ids.includes(project.projectId),
              'hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)]': !ids.includes(project.projectId)
            }"
          >
            <div
              v-if="ids.includes(project.projectId)"
              class="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#0052d9] to-[#3370ff]"
            />
            <div class="px-5 py-4 border-b border-[#f0f1f5] bg-gradient-to-b from-[#fafbfc] to-white">
              <div class="flex items-start justify-between gap-3">
                <div class="flex items-start gap-3 flex-1 min-w-0">
                  <el-checkbox
                    :model-value="ids.includes(project.projectId)"
                    @change="toggleSelection(project)"
                    @click.stop
                    class="mt-0.5 flex-shrink-0"
                  />
                  <div class="flex-1 min-w-0">
                    <h3 class="text-base font-semibold text-[#1d2129] truncate mb-1 leading-tight">
                      <router-link
                        :to="'/project/project-detail/index/' + project.projectId"
                        class="hover:text-[#0052d9] transition-colors no-underline"
                        @click.stop
                      >
                        {{ project.projectName }}
                      </router-link>
                    </h3>
                    <p class="text-xs text-[#86909c] flex items-center gap-1">
                      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/>
                      </svg>
                      <span>编号: {{ project.projectId }}</span>
                    </p>
                  </div>
                </div>
                <el-dropdown @click.stop trigger="click" class="flex-shrink-0">
                  <button class="w-7 h-7 rounded-sm flex items-center justify-center text-[#86909c] hover:text-[#0052d9] hover:bg-[#f2f5fc] transition-all">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <circle cx="12" cy="5" r="2"/>
                      <circle cx="12" cy="12" r="2"/>
                      <circle cx="12" cy="19" r="2"/>
                    </svg>
                  </button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item icon="Document" @click="handleDetail(project)" v-hasPermi="['project:project:query']">查看详情</el-dropdown-item>
                      <el-dropdown-item icon="Edit" @click="handleUpdate(project)" v-hasPermi="['project:project:edit']">编辑工程</el-dropdown-item>
                      <el-dropdown-item icon="Delete" @click="handleDelete(project)" v-hasPermi="['project:project:remove']" divided>删除工程</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <div class="px-5 py-4">
              <div class="mb-4">
                <div class="text-[#4e5969] text-[13px] leading-relaxed line-clamp-2 min-h-[40px]">
                  {{ project.projectDesc || '暂无工程描述信息' }}
                </div>
              </div>

              <div class="space-y-2.5 mb-4">
                <div class="flex items-center text-xs">
                  <div class="flex items-center gap-1.5 text-[#86909c] w-[72px] flex-shrink-0">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    <span>创建人</span>
                  </div>
                  <span class="text-[#1d2129] font-medium">{{ project.createBy || '-' }}</span>
                </div>
                <div class="flex items-center text-xs">
                  <div class="flex items-center gap-1.5 text-[#86909c] w-[72px] flex-shrink-0">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>创建时间</span>
                  </div>
                  <span class="text-[#4e5969]">{{ parseTime(project.createTime, '{y}-{m}-{d}') || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="px-5 py-3 border-t border-[#f0f1f5] bg-[#fafbfc] flex items-center justify-between gap-2">
              <div class="flex items-center gap-1.5 flex-1">
                <button
                  @click.stop="handleDetail(project)"
                  v-hasPermi="['project:project:query']"
                  class="flex-1 h-8 px-3 text-xs font-medium text-[#4e5969] bg-white border border-[#e5e6eb] rounded-sm hover:text-[#0052d9] hover:border-[#0052d9] hover:bg-[#f2f5fc] transition-all flex items-center justify-center gap-1"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  <span>详情</span>
                </button>
                <button
                  @click.stop="handleUpdate(project)"
                  v-hasPermi="['project:project:edit']"
                  class="flex-1 h-8 px-3 text-xs font-medium text-white bg-[#0052d9] border border-[#0052d9] rounded-sm hover:bg-[#003ba8] hover:border-[#003ba8] transition-all flex items-center justify-center gap-1"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                  <span>编辑</span>
                </button>
              </div>
              <button
                @click.stop="handleDelete(project)"
                v-hasPermi="['project:project:remove']"
                class="w-8 h-8 flex items-center justify-center text-[#86909c] hover:text-[#f56c6c] hover:bg-[#fef0f0] border border-[#e5e6eb] hover:border-[#f56c6c] rounded-sm transition-all"
                title="删除"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-if="!grid.loading && grid.list.length === 0" class="text-center py-16 px-4">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-[#f7f8fa] mb-4">
            <svg class="w-10 h-10 text-[#c9cdd4]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-[#1d2129] mb-2">暂无工程</h3>
          <p class="text-sm text-[#86909c] mb-6 max-w-md mx-auto">还没有创建任何工程，点击下方按钮开始创建您的第一个工程</p>
          <el-button type="primary" size="default" @click="handleAdd" v-hasPermi="['project:project:add']">
            <template #icon>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
            </template>
            创建工程
          </el-button>
        </div>
      </template>
    </ZxGridList>
  </ZxContentWrap>

  <el-dialog :title="title" v-model="open" width="600px" append-to-body>
    <el-form ref="projectRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="工程名称" prop="projectName">
        <el-input v-model="form.projectName" placeholder="请输入工程名称" />
      </el-form-item>
      <el-form-item label="工程编码" prop="projectCode">
        <el-input v-model="form.projectCode" placeholder="自动生成" disabled />
      </el-form-item>
      <el-form-item label="工程描述" prop="projectDesc">
        <el-input v-model="form.projectDesc" type="textarea" :rows="4" placeholder="请输入工程描述" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup name="Project">
import { listProject, getProject, delProject, addProject, updateProject } from '@/api/project/project'

const { proxy } = getCurrentInstance()

const gridListRef = ref()
const ids = ref([])
const single = ref(true)
const multiple = ref(true)

const open = ref(false)
const title = ref('')

const data = reactive({
  form: {},
  rules: {
    projectName: [{ required: true, message: '工程名称不能为空', trigger: 'blur' }]
  }
})

const { form, rules } = toRefs(data)

async function loadProjectData(params) {
  try {
    const { pageNum, pageSize, ...query } = params
    let requestParams = { pageNum, pageSize, ...query }
    if (query.dateRange && query.dateRange.length === 2) {
      requestParams = proxy.addDateRange(requestParams, query.dateRange)
      delete requestParams.dateRange
    }
    const response = await listProject(requestParams)
    return {
      list: response.rows || [],
      total: response.total || 0
    }
  } catch (error) {
    return { list: [], total: 0 }
  }
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value })
  handleRefresh()
}

function onSearch({ handleRefresh }) {
  handleRefresh()
}

function refreshList() {
  gridListRef.value && gridListRef.value.refresh()
}

function reset() {
  form.value = {
    projectId: null,
    projectName: null,
    projectCode: null,
    projectDesc: null
  }
  proxy.resetForm('projectRef')
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '添加工程'
}

function toggleSelection(project) {
  const index = ids.value.indexOf(project.projectId)
  if (index > -1) ids.value.splice(index, 1)
  else ids.value.push(project.projectId)
  single.value = ids.value.length != 1
  multiple.value = !ids.value.length
}

function handleDetail(row) {
  const projectId = row.projectId
  proxy.$router.push('/project/project-detail/index/' + projectId)
}

function handleUpdate(row) {
  reset()
  const projectId = row.projectId
  getProject(projectId).then(response => {
    form.value = response.data
    open.value = true
    title.value = '修改工程'
  })
}

function submitForm() {
  proxy.$refs['projectRef'].validate(valid => {
    if (valid) {
      if (form.value.projectId != null) {
        updateProject(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          refreshList()
        })
      } else {
        addProject(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功')
          open.value = false
          refreshList()
        })
      }
    }
  })
}

function handleDelete(row) {
  const projectIds = row.projectId || ids.value
  proxy.$modal
    .confirm('是否确认删除工程编号为"' + projectIds + '"的数据项？')
    .then(function () {
      return delProject(projectIds)
    })
    .then(() => {
      refreshList()
      proxy.$modal.msgSuccess('删除成功')
    })
}
</script>
