<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadJobData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['monitor:job:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['monitor:job:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['monitor:job:remove']"
              >删除</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="() => handleExport(query)"
              v-hasPermi="['monitor:job:export']"
              >导出</ZxButton
            >
            <ZxButton
              type="info"
              icon="Operation"
              @click="handleJobLog"
              v-hasPermi="['monitor:job:query']"
              >日志</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-select
              v-model="query.jobGroup"
              placeholder="请选择任务组名"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('jobGroup', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_job_group"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
            <el-select
              v-model="query.status"
              placeholder="请选择任务状态"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_job_status"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.jobName"
              placeholder="搜索任务名称"
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
          <el-table-column label="任务编号" width="100" prop="jobId" />
          <el-table-column label="任务名称" prop="jobName" :show-overflow-tooltip="true" />
          <el-table-column label="任务组名" prop="jobGroup">
            <template #default="scope">
              <dict-tag :options="sys_job_group" :value="scope.row.jobGroup" />
            </template>
          </el-table-column>
          <el-table-column
            label="调用目标字符串"
            prop="invokeTarget"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="cron执行表达式"
            prop="cronExpression"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="状态">
            <template #default="scope">
              <el-switch
                v-model="scope.row.status"
                active-value="0"
                inactive-value="1"
                @change="handleStatusChange(scope.row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-tooltip content="修改" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Edit"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['monitor:job:edit']"
                />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button
                  link
                  type="danger"
                  icon="Delete"
                  @click="handleDelete(scope.row)"
                  v-hasPermi="['monitor:job:remove']"
                />
              </el-tooltip>
              <el-tooltip content="执行一次" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="CaretRight"
                  @click="handleRun(scope.row)"
                  v-hasPermi="['monitor:job:changeStatus']"
                />
              </el-tooltip>
              <el-tooltip content="任务详细" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="View"
                  @click="handleView(scope.row)"
                  v-hasPermi="['monitor:job:query']"
                />
              </el-tooltip>
              <el-tooltip content="调度日志" placement="top">
                <el-button
                  link
                  type="primary"
                  icon="Operation"
                  @click="handleJobLog(scope.row)"
                  v-hasPermi="['monitor:job:query']"
                />
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 添加或修改定时任务对话框 -->
    <el-dialog :title="title" v-model="open" width="820px" append-to-body>
      <el-form ref="jobRef" :model="form" :rules="rules" label-width="120px">
        <el-row>
          <el-col :span="24">
            <el-form-item label="任务名称" prop="jobName">
              <el-input v-model="form.jobName" placeholder="请输入任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务分组" prop="jobGroup">
              <el-select v-model="form.jobGroup" placeholder="请选择">
                <el-option
                  v-for="dict in sys_job_group"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item prop="jobGroup">
              <template #label>
                <span>
                  任务执行器
                  <el-tooltip placement="top">
                    <template #content>
                      <div>调用方法为异步函数时此选项无效</div>
                    </template>
                    <el-icon><question-filled /></el-icon>
                  </el-tooltip>
                </span>
              </template>
              <el-select v-model="form.jobExecutor" placeholder="请选择任务执行器">
                <el-option
                  v-for="dict in sys_job_executor"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item prop="invokeTarget">
              <template #label>
                <span>
                  调用方法
                  <el-tooltip placement="top">
                    <template #content>
                      <div>调用示例：module_task.scheduler_test.job</div>
                    </template>
                    <el-icon><question-filled /></el-icon>
                  </el-tooltip>
                </span>
              </template>
              <el-input v-model="form.invokeTarget" placeholder="请输入调用目标字符串" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="位置参数" prop="jobArgs">
              <el-input v-model="form.jobArgs" placeholder="请输入位置参数" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="关键字参数" prop="jobKwargs">
              <el-input v-model="form.jobKwargs" placeholder="请输入关键字参数" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="cron表达式" prop="cronExpression">
              <el-input v-model="form.cronExpression" placeholder="请输入cron执行表达式">
                <template #append>
                  <el-button type="primary" @click="handleShowCron">
                    生成表达式
                    <i class="el-icon-time el-icon--right" />
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="form.jobId !== undefined">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio v-for="dict in sys_job_status" :key="dict.value" :value="dict.value">
                  {{ dict.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行策略" prop="misfirePolicy">
              <el-radio-group v-model="form.misfirePolicy">
                <el-radio-button value="1">立即执行</el-radio-button>
                <el-radio-button value="2">执行一次</el-radio-button>
                <el-radio-button value="3">放弃执行</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否并发" prop="concurrent">
              <el-radio-group v-model="form.concurrent">
                <el-radio-button value="0">允许</el-radio-button>
                <el-radio-button value="1">禁止</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
      <crontab
        ref="crontabRef"
        @hide="openCron = false"
        @fill="crontabFill"
        :expression="expression"
      />
    </el-dialog>

    <!-- 任务日志详细 -->
    <el-dialog title="任务详细" v-model="openView" width="700px" append-to-body>
      <el-form :model="form" label-width="120px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="任务编号：">{{ form.jobId }}</el-form-item>
            <el-form-item label="任务名称：">{{ form.jobName }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务分组：">{{ jobGroupFormat(form) }}</el-form-item>
            <el-form-item label="创建时间：">{{ parseTime(form.createTime) }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="cron表达式：">{{ form.cronExpression }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="下次执行时间：">{{ parseTime(form.nextValidTime) }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务执行器：">{{ jobExecutorFormat(form) }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="调用目标方法：">{{ form.invokeTarget }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="位置参数：">{{ form.jobArgs }}</el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="关键字参数：">{{ form.jobKwargs }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务状态：">
              <div v-if="form.status == 0">正常</div>
              <div v-else-if="form.status == 1">暂停</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否并发：">
              <div v-if="form.concurrent == 0">允许</div>
              <div v-else-if="form.concurrent == 1">禁止</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行策略：">
              <div v-if="form.misfirePolicy == '0'">默认策略</div>
              <div v-else-if="form.misfirePolicy == '1'">立即执行</div>
              <div v-else-if="form.misfirePolicy == '2'">执行一次</div>
              <div v-else-if="form.misfirePolicy == '3'">放弃执行</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="openView = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </ZxContentWrap>
</template>

<script setup name="Job">
import {
  listJob,
  getJob,
  delJob,
  addJob,
  updateJob,
  runJob,
  changeJobStatus,
} from '@/api/monitor/job';
import Crontab from '@/components/Crontab';

const router = useRouter();
const { proxy } = getCurrentInstance();
const { sys_job_group, sys_job_status, sys_job_executor } = proxy.useDict(
  'sys_job_group',
  'sys_job_status',
  'sys_job_executor'
);

const open = ref(false);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const title = ref('');
const openView = ref(false);
const openCron = ref(false);
const expression = ref('');
const gridListRef = ref(null);

const data = reactive({
  form: {},
  rules: {
    jobName: [{ required: true, message: '任务名称不能为空', trigger: 'blur' }],
    invokeTarget: [{ required: true, message: '调用目标字符串不能为空', trigger: 'blur' }],
    cronExpression: [{ required: true, message: 'cron执行表达式不能为空', trigger: 'change' }],
  },
});

const { form, rules } = toRefs(data);

async function loadJobData(params) {
  const queryData = {
    pageNum: params.page,
    pageSize: params.size,
    jobName: params.query?.jobName,
    jobGroup: params.query?.jobGroup,
    status: params.query?.status,
  };
  try {
    const response = await listJob(queryData);
    return { data: response.rows || [], total: response.total || 0 };
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}

/** 任务组名字典翻译 */
function jobGroupFormat(row) {
  return proxy.selectDictLabel(sys_job_group.value, row.jobGroup);
}

/** 任务执行器名字典翻译 */
function jobExecutorFormat(row) {
  return proxy.selectDictLabel(sys_job_executor.value, row.jobExecutor);
}

/** 取消按钮 */
function cancel() {
  open.value = false;
  reset();
}

/** 表单重置 */
function reset() {
  form.value = {
    jobId: undefined,
    jobName: undefined,
    jobGroup: undefined,
    invokeTarget: undefined,
    cronExpression: undefined,
    misfirePolicy: '1',
    concurrent: '1',
    status: '1',
  };
  proxy.resetForm('jobRef');
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.jobId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 任务状态修改 */
function handleStatusChange(row) {
  let text = row.status === '0' ? '启用' : '停用';
  proxy.$modal
    .confirm('确认要"' + text + '""' + row.jobName + '"任务吗?')
    .then(() => changeJobStatus(row.jobId, row.status))
    .then(() => {
      proxy.$modal.msgSuccess(text + '成功');
    })
    .catch(() => {
      row.status = row.status === '0' ? '1' : '0';
    });
}

/** 立即执行一次 */
function handleRun(row) {
  proxy.$modal
    .confirm('确认要立即执行一次"' + row.jobName + '"任务吗?')
    .then(() => runJob(row.jobId, row.jobGroup))
    .then(() => {
      proxy.$modal.msgSuccess('执行成功');
    })
    .catch(() => {});
}

/** 任务详细信息 */
function handleView(row) {
  getJob(row.jobId).then((response) => {
    form.value = response.data;
    openView.value = true;
  });
}

/** cron表达式按钮操作 */
function handleShowCron() {
  expression.value = form.value.cronExpression;
  openCron.value = true;
}

/** 确定后回传值 */
function crontabFill(value) {
  form.value.cronExpression = value;
}

/** 任务日志列表查询 */
function handleJobLog(row) {
  const jobId = row?.jobId || 0;
  router.push('/monitor/job-log/index/' + jobId);
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = '添加任务';
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const jobId = row.jobId || ids.value;
  getJob(jobId).then((response) => {
    form.value = response.data;
    open.value = true;
    title.value = '修改任务';
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs['jobRef'].validate((valid) => {
    if (valid) {
      if (form.value.jobId !== undefined) {
        updateJob(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      } else {
        addJob(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const jobIds = row.jobId || ids.value;
  proxy.$modal
    .confirm('是否确认删除定时任务编号为"' + jobIds + '"的数据项?')
    .then(() => delJob(jobIds))
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

/** 导出按钮操作 */
function handleExport(query) {
  const params = {
    jobName: query?.jobName,
    jobGroup: query?.jobGroup,
    status: query?.status,
  };
  proxy.download('monitor/job/export', params, `job_${new Date().getTime()}.xlsx`);
}
</script>
