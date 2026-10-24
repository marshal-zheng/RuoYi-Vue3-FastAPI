<template>
  <div class="app-container">
    <DictStatus :types="['sys_common_status', 'sys_job_group', 'sys_job_executor']" />
    <el-form
      :model="queryParams"
      ref="queryRef"
      :inline="true"
      v-show="showSearch"
      label-width="68px"
    >
      <el-form-item label="任务名称" prop="jobName">
        <zx-input
          v-model="queryParams.jobName"
          placeholder="请输入任务名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="任务组名" prop="jobGroup">
        <DictSelect
          dict-type="sys_job_group"
          v-model="queryParams.jobGroup"
          placeholder="请选择任务组名"
          clearable
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item label="执行状态" prop="status">
        <DictSelect
          dict-type="sys_common_status"
          v-model="queryParams.status"
          placeholder="请选择执行状态"
          clearable
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item label="执行时间" style="width: 308px">
        <el-date-picker
          v-model="dateRange"
          value-format="YYYY-MM-DD"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        ></el-date-picker>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['monitor:job:remove']"
          :loading="handleDeletePending"
          >删除</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          @click="handleClean"
          v-hasPermi="['monitor:job:remove']"
          :loading="handleCleanPending"
          >清空</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="Download"
          @click="handleExport"
          v-hasPermi="['monitor:job:export']"
          >导出</el-button
        >
      </el-col>
      <el-col :span="1.5">
        <el-button type="warning" plain icon="Close" @click="handleClose">关闭</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="jobLogList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="日志编号" width="80" align="center" prop="jobLogId" />
      <el-table-column
        label="任务名称"
        align="center"
        prop="jobName"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="任务组名"
        align="center"
        prop="jobGroup"
        :show-overflow-tooltip="true"
      >
        <template #default="scope">
          <dict-tag :options="sys_job_group" :value="scope.row.jobGroup" />
        </template>
      </el-table-column>
      <el-table-column
        label="调用目标字符串"
        align="center"
        prop="invokeTarget"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="日志信息"
        align="center"
        prop="jobMessage"
        :show-overflow-tooltip="true"
      />
      <el-table-column label="执行状态" align="center" prop="status">
        <template #default="scope">
          <dict-tag :options="sys_common_status" :value="scope.row.status" />
        </template>
      </el-table-column>
      <el-table-column label="执行时间" align="center" prop="createTime" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button
            link
            type="primary"
            icon="View"
            @click="handleView(scope.row)"
            v-hasPermi="['monitor:job:query']"
            >详细</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.page"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 调度日志详细 -->
    <ZxDialog
      dialog-size="lg"
      :draggable="false"
      :show-full-screen="false"
      :destroy-on-close="false"
      :close-on-click-modal="true"
      title="调度日志详细"
      v-model="open"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="日志序号：">{{ form.jobLogId }}</el-descriptions-item>
        <el-descriptions-item label="任务名称：">{{ form.jobName }}</el-descriptions-item>

        <el-descriptions-item label="任务分组：">{{ jobGroupFormat(form) }}</el-descriptions-item>
        <el-descriptions-item label="执行时间：">{{
          parseTime(form.createTime)
        }}</el-descriptions-item>

        <el-descriptions-item label="任务执行器：">{{
          jobExecutorFormat(form)
        }}</el-descriptions-item>

        <el-descriptions-item label="任务触发器：">{{ form.jobTrigger }}</el-descriptions-item>

        <el-descriptions-item label="调用方法：">{{ form.invokeTarget }}</el-descriptions-item>

        <el-descriptions-item label="位置参数：">{{ form.jobArgs }}</el-descriptions-item>

        <el-descriptions-item label="关键字参数：">{{ form.jobKwargs }}</el-descriptions-item>

        <el-descriptions-item label="日志信息：">{{ form.jobMessage }}</el-descriptions-item>

        <el-descriptions-item label="执行状态：">
          <div v-if="form.status == 0">正常</div>
          <div v-else-if="form.status == 1">失败</div>
        </el-descriptions-item>

        <el-descriptions-item label="异常信息：" v-if="form.status == 1">{{
          form.exceptionInfo
        }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="open = false">关 闭</el-button>
        </div>
      </template>
    </ZxDialog>
  </div>
</template>

<script setup name="JobLog">
import { useOperation } from '@/utils/operation';
import { getJob } from '@/api/monitor/job';
import { listJobLog, delJobLog, cleanJobLog } from '@/api/monitor/jobLog';

const { proxy } = getCurrentInstance();
const { sys_common_status, sys_job_group, sys_job_executor } = proxy.useDict(
  'sys_common_status',
  'sys_job_group',
  'sys_job_executor'
);

const jobLogList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const multiple = ref(true);
const total = ref(0);
const dateRange = ref([]);
const route = useRoute();

const data = reactive({
  form: {},
  queryParams: {
    page: 1,
    pageSize: 10,
    dictName: undefined,
    dictType: undefined,
    status: undefined,
  },
});

const { queryParams, form } = toRefs(data);

/** 查询调度日志列表 */
function getList() {
  loading.value = true;
  listJobLog(proxy.addDateRange(queryParams.value, dateRange.value)).then((response) => {
    jobLogList.value = response.items;
    total.value = response.total;
    loading.value = false;
  });
}
/** 任务组名字典翻译 */
function jobGroupFormat(row) {
  return proxy.selectDictLabel(sys_job_group.value, row.jobGroup);
}
/** 任务组名字典翻译 */
function jobExecutorFormat(row) {
  return proxy.selectDictLabel(sys_job_executor.value, row.jobExecutor);
}
// 返回按钮
function handleClose() {
  const obj = { path: '/monitor/job' };
  proxy.$tab.closeOpenPage(obj);
}
/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.page = 1;
  getList();
}
/** 重置按钮操作 */
function resetQuery() {
  dateRange.value = [];
  proxy.resetForm('queryRef');
  handleQuery();
}
// 多选框选中数据
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.jobLogId);
  multiple.value = !selection.length;
}
/** 详细按钮操作 */
function handleView(row) {
  open.value = true;
  form.value = row;
}
/** 删除按钮操作 */
const { run: handleDelete, pending: handleDeletePending } = useOperation(async () => {
  await proxy.$modal
    .confirm('是否确认删除调度日志编号为"' + ids.value + '"的数据项?')
    .then(function () {
      return delJobLog(ids.value);
    })
    .then(() => {
      getList();
    })
    .catch(() => {});
});
/** 清空按钮操作 */
const { run: handleClean, pending: handleCleanPending } = useOperation(async () => {
  await proxy.$modal
    .confirm('是否确认清空所有调度日志数据项?')
    .then(function () {
      return cleanJobLog();
    })
    .then(() => {
      getList();
    })
    .catch(() => {});
});
/** 导出按钮操作 */
function handleExport() {
  proxy.download(
    'monitor/jobLog/export',
    {
      ...queryParams.value,
    },
    `job_log_${new Date().getTime()}.xlsx`
  );
}

(() => {
  const jobId = route.params && route.params.jobId;
  if (jobId !== undefined && jobId != 0) {
    getJob(jobId).then((response) => {
      const data = response;
      queryParams.value.jobName = data.jobName;
      queryParams.value.jobGroup = data.jobGroup;
      getList();
    });
  } else {
    getList();
  }
})();
</script>
