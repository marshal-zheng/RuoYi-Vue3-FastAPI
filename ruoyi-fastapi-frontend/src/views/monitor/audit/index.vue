<template>
  <ZxContentWrap fill>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadAuditData"
      :query-transform="queryTransform"
      :show-pagination="true"
      :load-on-mounted="true"
      fill
    >
      <template #form="{ query, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['monitor:audit:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              @click="handleClean"
              v-hasPermi="['monitor:audit:remove']"
              >清空</ZxButton
            >
          </template>
          <template #filters>
            <TableNameSelector
              v-model="query.tableName"
              clearable
              filterable
              style="width: 200px"
              @change="(v) => onFilterChange('tableName', v, { handleRefresh, updateState })"
            />
            <zx-select
              v-model="query.action"
              :options="actionOptions"
              placeholder="动作类型"
              clearable
              style="width: 160px"
              @change="(v) => onFilterChange('action', v, { handleRefresh, updateState })"
            />
            <zx-input
              v-model="query.operatorName"
              placeholder="请输入操作人"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh })"
            />
            <zx-input
              v-model="query.requestId"
              placeholder="请输入请求ID"
              clearable
              style="width: 220px"
              @keyup.enter="() => onSearch({ handleRefresh })"
            />
            <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD HH:mm:ss"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :default-time="[new Date(2000, 1, 1, 0, 0, 0), new Date(2000, 1, 1, 23, 59, 59)]"
              style="width: 308px"
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
      </template>

      <template #table="{ grid, refresh: handleRefresh, updateState }">
        <el-table
          ref="auditRef"
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
          :default-sort="defaultSort"
          @sort-change="(c) => onSortChange(c, { updateState, handleRefresh })"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="审计ID" align="center" prop="auditId" />
          <el-table-column
            label="动作类型"
            align="center"
            prop="action"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          />
          <el-table-column
            label="表名"
            align="center"
            prop="tableName"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="主键" align="center" prop="pk" :show-overflow-tooltip="true" />
          <el-table-column
            label="操作人"
            align="center"
            prop="operatorName"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="操作IP"
            align="center"
            prop="operatorIp"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="请求方法" align="center" prop="requestMethod" />
          <el-table-column
            label="请求路径"
            align="center"
            prop="requestPath"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="时间"
            align="center"
            prop="createTime"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
            width="180"
          >
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>
</template>

<script setup name="AuditLog">
import { serializeDateRange } from '@/utils/ruoyi';
import { list, delAuditLog, cleanAuditLog } from '@/api/monitor/audit';
import TableNameSelector from '@/components/business/Monitor/selector/TableNameSelector.vue';

const { proxy } = getCurrentInstance();
const ids = ref([]);
const multiple = ref(true);
const defaultSort = ref({ prop: 'createTime', order: 'descending' });
const gridListRef = ref(null);

const actionOptions = [
  { label: 'READ', value: 'READ' },
  { label: 'INSERT', value: 'INSERT' },
  { label: 'UPDATE', value: 'UPDATE' },
  { label: 'DELETE', value: 'DELETE' },
];

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 - 不处理参数转换 */
async function loadAuditData(params) {
  try {
    return await list(params);
  } catch {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState(`query.${field}`, value);
  handleRefresh();
}
function onSearch({ handleRefresh }) {
  handleRefresh();
}
function onSortChange(c, { updateState, handleRefresh }) {
  updateState('query.orderByColumn', c.prop);
  updateState('query.isAsc', c.order);
  handleRefresh();
}
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.auditId);
  multiple.value = !selection.length;
}
function handleDelete(row) {
  const auditIds = row?.auditId || ids.value;
  proxy.$modal
    .confirm('是否确认删除审计日志编号为"' + auditIds + '"的数据项?')
    .then(function () {
      return delAuditLog(auditIds);
    })
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}
function handleClean() {
  proxy.$modal
    .confirm('是否确认清空所有审计日志数据项?')
    .then(function () {
      return cleanAuditLog();
    })
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}
</script>
