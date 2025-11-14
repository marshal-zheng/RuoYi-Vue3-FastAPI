<template>
  <div class="version-list">
    <ZxGridList
      ref="versionGridListRef"
      :load-data="loadVersionData"
      :show-pagination="true"
      :page-sizes="[10, 20, 50, 100]"
      :default-page-size="10"
      :load-on-mounted="true"
      :clear-selection-on-load="true"
      class="version-grid zx-grid-list--page"
    >
      <!-- 工具栏：左-操作 | 中-筛选 | 右-搜索 -->
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <!-- <ZxButton
              type="primary"
              icon="Plus"
              @click="handleAddVersion"
              v-hasPermi="['project:version:add']"
            >新增版本</ZxButton>
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDeleteVersion"
              v-hasPermi="['project:version:remove']"
            >删除</ZxButton>
            <ZxButton
              icon="Download"
              @click="handleExportVersion"
              v-hasPermi="['project:version:export']"
            >导出</ZxButton> -->
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
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </div>
          
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.versionName"
              placeholder="搜索版本名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <!-- 表格内容 -->
      <template #table="{ grid, refresh: handleRefresh }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="版本号" prop="versionNumber" width="120" />
          <el-table-column label="版本名称" prop="versionName" min-width="150" />
          <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
          <el-table-column label="创建人" prop="createBy" width="120" />
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="{ row }">
              {{ parseTime(row.createTime) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="status" align="center">
            <template #default="{ row }">
              <div class="flex items-center justify-center gap-2">
                <el-tag :type="row.status === '1' ? 'success' : 'info'">
                  {{ row.status === '1' ? '启用' : '停用' }}
                </el-tag>
                <el-tag v-if="row.isLocked" type="warning" size="small">
                  <el-icon class="mr-1"><Lock /></el-icon>
                  固化
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="200"
            class-name="op-col"
            label-class-name="op-col__header"
          >
            <template #default="{ row }">
              <div class="op-col__wrap">
                <ZxButton link type="primary" @click="handleViewVersion(row)">查看</ZxButton>
                <ZxButton link type="primary" @click="handleEditVersion(row)">编辑</ZxButton>
                <ZxMoreAction
                  :list="getMoreActionList(row)"
                  @select="handleMoreActionSelect($event, row, handleRefresh)"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <div v-if="!grid.loading && grid.list.length === 0" class="text-center py-12">
          <div class="text-gray-400 text-6xl mb-4">📦</div>
          <h3 class="text-lg font-medium text-gray-600 mb-2">暂无版本</h3>
          <p class="text-gray-500 mb-4">还没有创建任何版本，点击新增版本按钮开始创建吧</p>
          <el-button 
            type="primary" 
            icon="Plus" 
            @click="handleAddVersion"
            v-hasPermi="['project:version:add']"
          >创建版本</el-button>
        </div>
      </template>
    </ZxGridList>

    <!-- 编辑版本对话框 -->
    <el-dialog
      v-model="editVersionDialog"
      title="编辑版本"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="editVersionForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="版本号" required>
          <el-input
            v-model="editVersionForm.versionNumber"
            placeholder="请输入版本号，如：v1.0.0"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item label="版本名称" required>
          <el-input
            v-model="editVersionForm.versionName"
            placeholder="请输入版本名称"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="版本描述">
          <el-input
            v-model="editVersionForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入版本描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="editVersionForm.status">
            <el-radio value="1">启用</el-radio>
            <el-radio value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editVersionDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveEditVersion">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 克隆版本对话框 -->
    <el-dialog
      v-model="cloneVersionDialog"
      title="克隆版本"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="mb-4 p-3 bg-gray-50 rounded">
        <div class="text-sm text-gray-600 mb-1">源版本：</div>
        <div class="font-medium">{{ cloneVersionForm.sourceVersionName }}</div>
      </div>
      <el-form
        :model="cloneVersionForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="版本号" required>
          <el-input
            v-model="cloneVersionForm.versionNumber"
            placeholder="请输入新版本号，如：v1.0.1"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item label="版本名称" required>
          <el-input
            v-model="cloneVersionForm.versionName"
            placeholder="请输入新版本名称"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="版本描述">
          <el-input
            v-model="cloneVersionForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入版本描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cloneVersionDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveCloneVersion">克隆</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="VersionList">
import { ref, reactive } from 'vue'
import { View, Edit, Delete, Lock, CopyDocument } from '@element-plus/icons-vue'

const { proxy } = getCurrentInstance()

defineProps({
  projectId: {
    type: [String, Number],
    default: null
  }
})

const versionGridListRef = ref(null)
const ids = ref([])
const single = ref(true)
const multiple = ref(true)

// 编辑版本对话框
const editVersionDialog = ref(false)
const editVersionForm = reactive({
  versionId: null,
  versionNumber: '',
  versionName: '',
  description: '',
  status: '1'
})

// 克隆版本对话框
const cloneVersionDialog = ref(false)
const cloneVersionForm = reactive({
  sourceVersionId: null,
  sourceVersionName: '',
  versionNumber: '',
  versionName: '',
  description: ''
})

/** Mock 版本数据 */
const mockVersions = ref([
  {
    versionId: 1,
    versionNumber: 'v1.0.0',
    versionName: '初始版本',
    description: '项目初始版本，包含基础功能模块',
    createBy: 'admin',
    createTime: '2024-01-15 10:30:00',
    updateTime: '2024-01-15 10:30:00',
    status: '1',
    isLocked: false
  },
  {
    versionId: 2,
    versionNumber: 'v1.1.0',
    versionName: '功能增强版',
    description: '新增用户管理模块，优化系统性能',
    createBy: 'admin',
    createTime: '2024-02-20 14:20:00',
    updateTime: '2024-02-20 14:20:00',
    status: '1',
    isLocked: false
  },
  {
    versionId: 3,
    versionNumber: 'v2.0.0',
    versionName: '重大更新版',
    description: '架构重构，新增多租户支持，UI全面升级',
    createBy: 'admin',
    createTime: '2024-03-10 09:15:00',
    updateTime: '2024-03-10 09:15:00',
    status: '1',
    isLocked: true
  }
])

/** ZxGridList 版本数据加载函数 - Mock */
async function loadVersionData(params) {
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 300))
  
  const { pageNum = 1, pageSize = 10, versionName, dateRange } = params
  
  // 过滤数据
  let filteredList = [...mockVersions.value]
  
  // 按版本名称筛选
  if (versionName) {
    filteredList = filteredList.filter(item => 
      item.versionName.includes(versionName) || 
      item.versionNumber.includes(versionName)
    )
  }
  
  // 按日期范围筛选
  if (dateRange && dateRange.length === 2) {
    const [startDate, endDate] = dateRange
    filteredList = filteredList.filter(item => {
      const createDate = item.createTime.split(' ')[0]
      return createDate >= startDate && createDate <= endDate
    })
  }
  
  // 分页
  const start = (pageNum - 1) * pageSize
  const end = start + pageSize
  const pageList = filteredList.slice(start, end)
  
  return {
    list: pageList,
    total: filteredList.length
  }
}

/** 筛选变化处理 */
function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value })
  handleRefresh()
}

/** 搜索处理 */
function onSearch({ handleRefresh, updateState }) {
  handleRefresh()
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.versionId)
  single.value = selection.length != 1
  multiple.value = !selection.length
}

// 获取更多操作列表
const getMoreActionList = (row) => {
  const actions = []
  
  // 固化版本/解除固化
  if (row.isLocked) {
    actions.push({
      label: '解除固化',
      eventTag: 'unlock',
      icon: Lock,
      type: 'warning'
    })
  } else {
    actions.push({
      label: '固化版本',
      eventTag: 'lock',
      icon: Lock,
      type: 'primary'
    })
  }
  
  // 克隆版本
  actions.push({
    label: '克隆版本',
    eventTag: 'clone',
    icon: CopyDocument,
    type: 'primary'
  })
  
  // 删除版本（固化版本不能删除）
  if (!row.isLocked) {
    actions.push({
      label: '删除',
      eventTag: 'delete',
      icon: Delete,
      danger: true
    })
  }
  
  return actions
}

// 处理更多操作选择
const handleMoreActionSelect = async (item, row, handleRefresh) => {
  switch (item.eventTag) {
    case 'lock':
      handleLockVersion(row, handleRefresh)
      break
    case 'unlock':
      handleUnlockVersion(row, handleRefresh)
      break
    case 'clone':
      handleCloneVersion(row)
      break
    case 'delete':
      handleDeleteVersion(row, handleRefresh)
      break
    default:
      break
  }
}

/** 新增版本 */
function handleAddVersion() {
  proxy.$modal.msgInfo('新增版本功能待开发')
}

/** 删除版本 */
function handleDeleteVersion(row, handleRefresh) {
  const versionIds = row?.versionId || ids.value
  let confirmMessage = ''
  
  if (row?.versionId) {
    confirmMessage = `是否确认删除版本"${row.versionName}"？`
  } else {
    confirmMessage = `是否确认删除选中的 ${ids.value.length} 个版本？`
  }
  
  proxy.$modal.confirm(confirmMessage).then(() => {
    proxy.$modal.msgSuccess('删除成功')
    if (handleRefresh) {
      handleRefresh()
    } else if (versionGridListRef.value) {
      versionGridListRef.value.refresh()
    }
  }).catch(() => {})
}

/** 查看版本 */
function handleViewVersion(row) {
  proxy.$modal.msgInfo(`查看版本：${row.versionName}`)
}

/** 编辑版本 */
function handleEditVersion(row) {
  if (row.isLocked) {
    proxy.$modal.msgWarning('固化版本不允许编辑')
    return
  }
  
  // 填充编辑表单
  editVersionForm.versionId = row.versionId
  editVersionForm.versionNumber = row.versionNumber
  editVersionForm.versionName = row.versionName
  editVersionForm.description = row.description
  editVersionForm.status = row.status
  
  editVersionDialog.value = true
}

/** 保存编辑版本 */
function handleSaveEditVersion() {
  // 验证表单
  if (!editVersionForm.versionNumber || !editVersionForm.versionName) {
    proxy.$modal.msgError('版本号和版本名称不能为空')
    return
  }
  
  // 检查版本号是否重复
  const existingVersion = mockVersions.value.find(v => 
    v.versionNumber === editVersionForm.versionNumber && 
    v.versionId !== editVersionForm.versionId
  )
  
  if (existingVersion) {
    proxy.$modal.msgError('版本号已存在')
    return
  }
  
  // 更新版本数据
  const versionIndex = mockVersions.value.findIndex(v => v.versionId === editVersionForm.versionId)
  if (versionIndex !== -1) {
    mockVersions.value[versionIndex] = {
      ...mockVersions.value[versionIndex],
      versionNumber: editVersionForm.versionNumber,
      versionName: editVersionForm.versionName,
      description: editVersionForm.description,
      status: editVersionForm.status,
      updateTime: new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).replace(/\//g, '-')
    }
  }
  
  editVersionDialog.value = false
  proxy.$modal.msgSuccess('版本编辑成功')
  
  // 刷新列表
  if (versionGridListRef.value) {
    versionGridListRef.value.refresh()
  }
}

/** 固化版本 */
function handleLockVersion(row, handleRefresh) {
  proxy.$modal.confirm(`确定要固化版本"${row.versionName}"吗？固化后将无法编辑和删除。`).then(() => {
    const versionIndex = mockVersions.value.findIndex(v => v.versionId === row.versionId)
    if (versionIndex !== -1) {
      mockVersions.value[versionIndex].isLocked = true
      mockVersions.value[versionIndex].updateTime = new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).replace(/\//g, '-')
    }
    
    proxy.$modal.msgSuccess('版本固化成功')
    if (handleRefresh) {
      handleRefresh()
    } else if (versionGridListRef.value) {
      versionGridListRef.value.refresh()
    }
  }).catch(() => {})
}

/** 解除固化版本 */
function handleUnlockVersion(row, handleRefresh) {
  proxy.$modal.confirm(`确定要解除版本"${row.versionName}"的固化状态吗？`).then(() => {
    const versionIndex = mockVersions.value.findIndex(v => v.versionId === row.versionId)
    if (versionIndex !== -1) {
      mockVersions.value[versionIndex].isLocked = false
      mockVersions.value[versionIndex].updateTime = new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).replace(/\//g, '-')
    }
    
    proxy.$modal.msgSuccess('解除固化成功')
    if (handleRefresh) {
      handleRefresh()
    } else if (versionGridListRef.value) {
      versionGridListRef.value.refresh()
    }
  }).catch(() => {})
}

/** 克隆版本 */
function handleCloneVersion(row) {
  // 填充克隆表单
  cloneVersionForm.sourceVersionId = row.versionId
  cloneVersionForm.sourceVersionName = row.versionName
  cloneVersionForm.versionNumber = ''
  cloneVersionForm.versionName = `${row.versionName}_副本`
  cloneVersionForm.description = row.description
  
  cloneVersionDialog.value = true
}

/** 保存克隆版本 */
function handleSaveCloneVersion() {
  // 验证表单
  if (!cloneVersionForm.versionNumber || !cloneVersionForm.versionName) {
    proxy.$modal.msgError('版本号和版本名称不能为空')
    return
  }
  
  // 检查版本号是否重复
  const existingVersion = mockVersions.value.find(v => 
    v.versionNumber === cloneVersionForm.versionNumber
  )
  
  if (existingVersion) {
    proxy.$modal.msgError('版本号已存在')
    return
  }
  
  // 生成新的版本ID
  const newVersionId = Math.max(...mockVersions.value.map(v => v.versionId)) + 1
  
  // 创建新版本
  const newVersion = {
    versionId: newVersionId,
    versionNumber: cloneVersionForm.versionNumber,
    versionName: cloneVersionForm.versionName,
    description: cloneVersionForm.description,
    createBy: 'admin',
    createTime: new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-'),
    updateTime: new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-'),
    status: '1',
    isLocked: false
  }
  
  mockVersions.value.unshift(newVersion)
  
  cloneVersionDialog.value = false
  proxy.$modal.msgSuccess('版本克隆成功')
  
  // 刷新列表
  if (versionGridListRef.value) {
    versionGridListRef.value.refresh()
  }
}

/** 导出版本 */
function handleExportVersion() {
  proxy.$modal.msgInfo('导出版本功能待开发')
}
</script>

<style scoped lang="scss">
.version-list {
  padding: 0;
}
</style>





