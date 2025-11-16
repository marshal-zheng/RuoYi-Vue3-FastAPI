<template>
  <div>
    <ZxGridList ref="gridListRef" :load-data="loadOperlogData" class="zx-grid-list--page">
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__filters">
            <slot name="filters" :query="query" :loading="loading" :refresh="handleRefresh" :updateState="updateState">
              <el-input
                v-model="query.title"
                placeholder="系统模块"
                clearable
                style="width: 200px; margin-left: 8px"
                @keyup.enter="() => onSearch({ handleRefresh, updateState })"
              />
              <OperTypeSelector
                v-model="query.businessType"
                placeholder="类型"
                style="width: 160px; margin-left: 8px"
                @change="v => onFilterChange('businessType', v, { handleRefresh, updateState })"
              />
              <OperStatusSelector
                v-model="query.status"
                placeholder="状态"
                style="width: 160px; margin-left: 8px"
                @change="v => onFilterChange('status', v, { handleRefresh, updateState })"
              />
              <el-date-picker
                v-model="query.dateRange"
                value-format="YYYY-MM-DD HH:mm:ss"
                type="daterange"
                range-separator="-"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                :default-time="[new Date(2000, 1, 1, 0, 0, 0), new Date(2000, 1, 1, 23, 59, 59)]"
                style="margin-left: 8px; width: 308px"
                @change="v => onFilterChange('dateRange', v, { handleRefresh, updateState })"
              />
            </slot>
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.operName"
              placeholder="搜索操作人员"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <template #table="{ grid, refresh: handleRefresh, updateState }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="val => onSelectionChange(val)"
          :default-sort="defaultSort"
          @sort-change="c => onSortChange(c, { updateState, handleRefresh })"
        >
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column label="日志编号" align="center" prop="operId" />
          <el-table-column label="系统模块" align="center" prop="title" :show-overflow-tooltip="true" />
          <el-table-column label="操作类型" align="center" prop="businessType">
            <template #default="scope">
              <dict-tag :options="sys_oper_type" :value="scope.row.businessType" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作人员"
            align="center"
            width="110"
            prop="operName"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          />
          <el-table-column
            label="操作地址"
            align="center"
            prop="operIp"
            width="130"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="操作状态" align="center" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_common_status" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column
            label="操作日期"
            align="center"
            prop="operTime"
            width="180"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          >
            <template #default="scope">
              <span>{{ parseTime(scope.row.operTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            label="消耗时间"
            align="center"
            prop="costTime"
            width="110"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          >
            <template #default="scope">
              <span>{{ scope.row.costTime }}毫秒</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                icon="View"
                @click="handleView(scope.row)"
                v-hasPermi="['monitor:operlog:query']"
              >详细</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <el-dialog title="操作日志详细" v-model="open" width="800px" append-to-body>
      <el-form :model="form" label-width="100px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="操作模块：">{{ form.title }} / {{ typeFormat(form) }}</el-form-item>
            <el-form-item label="登录信息：">{{ form.operName }} / {{ form.operIp }} / {{ form.operLocation }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="请求地址：">{{ form.operUrl }}</el-form-item>
            <el-form-item label="请求方式：">{{ form.requestMethod }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="操作方法：">{{ form.method }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="请求参数：">{{ form.operParam }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="返回参数：">{{ form.jsonResult }}</el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="操作状态：">
              <div v-if="form.status === 0">正常</div>
              <div v-else-if="form.status === 1">失败</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="消耗时间：">{{ form.costTime }}毫秒</el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="操作时间：">{{ parseTime(form.operTime) }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="异常信息：" v-if="form.status === 1">{{ form.errorMsg }}</el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="open = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { list, delOperlog, cleanOperlog } from '@/api/monitor/operlog'
import { parseTime } from '@/utils/ruoyi'
import { OperTypeSelector, OperStatusSelector } from './selector'

const { proxy } = getCurrentInstance()
const { sys_oper_type, sys_common_status } = proxy.useDict('sys_oper_type', 'sys_common_status')

const gridListRef = ref()
const ids = ref([])
const open = ref(false)
const defaultSort = ref({ prop: 'operTime', order: 'descending' })
const form = ref({})

async function loadOperlogData(params) {
  const { pageNum, pageSize, dateRange, ...query } = params || {}
  let requestParams = { pageNum, pageSize, ...query }
  if (dateRange && dateRange.length === 2) {
    requestParams = proxy.addDateRange(requestParams, dateRange)
    delete requestParams.dateRange
  }
  try {
    const response = await list(requestParams)
    return { list: response.rows || [], total: response.total || 0 }
  } catch (e) {
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

function onSortChange(column, { updateState, handleRefresh }) {
  updateState({ orderByColumn: column.prop, isAsc: column.order })
  handleRefresh()
}

function onSelectionChange(selection) {
  ids.value = selection.map(item => item.operId)
  emit('selection-change', ids.value)
}

function typeFormat(row) {
  return proxy.selectDictLabel(sys_oper_type.value, row.businessType)
}

function handleView(row) {
  open.value = true
  form.value = row
}

function deleteSelected() {
  const operIds = ids.value
  if (!operIds || operIds.length === 0) return
  proxy.$modal
    .confirm('是否确认删除日志编号为"' + operIds + '"的数据项?')
    .then(function () {
      return delOperlog(operIds)
    })
    .then(() => {
      gridListRef.value && gridListRef.value.refresh()
      proxy.$modal.msgSuccess('删除成功')
    })
    .catch(() => {})
}

function cleanAll() {
  proxy.$modal
    .confirm('是否确认清空所有操作日志数据项?')
    .then(function () {
      return cleanOperlog()
    })
    .then(() => {
      gridListRef.value && gridListRef.value.refresh()
      proxy.$modal.msgSuccess('清空成功')
    })
    .catch(() => {})
}

function exportCurrent() {
  const q = gridListRef.value?.getCurrentQuery?.() || {}
  const query = { ...q }
  if (query.dateRange && query.dateRange.length === 2) {
    const tmp = proxy.addDateRange({}, query.dateRange)
    delete query.dateRange
    Object.assign(query, tmp)
  }
  proxy.download('monitor/operlog/export', query, `operlog_${new Date().getTime()}.xlsx`)
}

function refresh() {
  gridListRef.value && gridListRef.value.refresh()
}

function getCurrentQuery() {
  return gridListRef.value?.getCurrentQuery?.()
}

const emit = defineEmits(['selection-change'])

defineExpose({ refresh, getCurrentQuery, deleteSelected, cleanAll, exportCurrent })
</script>