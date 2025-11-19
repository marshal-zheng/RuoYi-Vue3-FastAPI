<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadLogininforData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['monitor:logininfor:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              @click="handleClean"
              v-hasPermi="['monitor:logininfor:remove']"
              >清空</ZxButton
            >
            <ZxButton
              type="primary"
              icon="Unlock"
              :disabled="single"
              @click="handleUnlock"
              v-hasPermi="['monitor:logininfor:unlock']"
              >解锁</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['monitor:logininfor:export']"
              >导出</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.ipaddr"
              placeholder="请输入登录地址"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-input
              v-model="query.userName"
              placeholder="请输入用户名称"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.status"
              placeholder="登录状态"
              clearable
              style="width: 240px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_common_status"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
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
          </div>
        </div>
      </template>

      <template #table="{ grid, refresh: handleRefresh, updateState }">
        <el-table
          ref="logininforRef"
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
          :default-sort="defaultSort"
          @sort-change="(c) => onSortChange(c, { updateState, handleRefresh })"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column label="访问编号" align="center" prop="infoId" />
          <el-table-column
            label="用户名称"
            align="center"
            prop="userName"
            :show-overflow-tooltip="true"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
          />
          <el-table-column
            label="地址"
            align="center"
            prop="ipaddr"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="登录地点"
            align="center"
            prop="loginLocation"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="操作系统"
            align="center"
            prop="os"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="浏览器"
            align="center"
            prop="browser"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="登录状态" align="center" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_common_status" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="描述" align="center" prop="msg" :show-overflow-tooltip="true" />
          <el-table-column
            label="访问时间"
            align="center"
            prop="loginTime"
            sortable="custom"
            :sort-orders="['descending', 'ascending']"
            width="180"
          >
            <template #default="scope">
              <span>{{ parseTime(scope.row.loginTime) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>
</template>

<script setup name="Logininfor">
import { list, delLogininfor, cleanLogininfor, unlockLogininfor } from '@/api/monitor/logininfor';

const { proxy } = getCurrentInstance();
const { sys_common_status } = proxy.useDict('sys_common_status');

const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const selectName = ref('');
const defaultSort = ref({ prop: 'loginTime', order: 'descending' });
const gridListRef = ref(null);

async function loadLogininforData(params) {
  const queryData = {
    pageNum: params.page,
    pageSize: params.size,
    ipaddr: params.query?.ipaddr,
    userName: params.query?.userName,
    status: params.query?.status,
    orderByColumn: params.query?.orderByColumn,
    isAsc: params.query?.isAsc,
  };
  const finalParams = proxy.addDateRange(queryData, params.query?.dateRange || []);
  const response = await list(finalParams);
  return { data: response.rows || [], total: response.total || 0 };
}
function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}
function onSearch({ handleRefresh }) {
  handleRefresh();
}
function onSortChange(c, { updateState, handleRefresh }) {
  updateState({ orderByColumn: c.prop, isAsc: c.order });
  handleRefresh();
}
/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.infoId);
  multiple.value = !selection.length;
  single.value = selection.length != 1;
  selectName.value = selection.map((item) => item.userName);
}
/** 删除按钮操作 */
function handleDelete(row) {
  const infoIds = row.infoId || ids.value;
  proxy.$modal
    .confirm('是否确认删除访问编号为"' + infoIds + '"的数据项?')
    .then(function () {
      return delLogininfor(infoIds);
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
/** 清空按钮操作 */
function handleClean() {
  proxy.$modal
    .confirm('是否确认清空所有登录日志数据项?')
    .then(function () {
      return cleanLogininfor();
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('清空成功');
    })
    .catch(() => {});
}
/** 解锁按钮操作 */
function handleUnlock() {
  const username = selectName.value;
  proxy.$modal
    .confirm('是否确认解锁用户"' + username + '"数据项?')
    .then(function () {
      return unlockLogininfor(username);
    })
    .then(() => {
      proxy.$modal.msgSuccess('用户' + username + '解锁成功');
    })
    .catch(() => {});
}
function handleExport(query) {
  const params = proxy.addDateRange(
    {
      ipaddr: query?.ipaddr,
      userName: query?.userName,
      status: query?.status,
      orderByColumn: query?.orderByColumn,
      isAsc: query?.isAsc,
    },
    query?.dateRange || []
  );
  proxy.download('monitor/logininfor/export', params, `logininfor_${new Date().getTime()}.xlsx`);
}
</script>
