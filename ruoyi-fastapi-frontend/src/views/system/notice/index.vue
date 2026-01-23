<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadNoticeData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:notice:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:notice:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:notice:remove']"
              >删除</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
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
              @change="(v) => onFilterChange('noticeType', v, { handleRefresh, updateState })"
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
                icon="Edit"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:notice:edit']"
                >修改</el-button
              >
              <el-button
                link
                type="danger"
                icon="Delete"
                @click="handleDelete(scope.row)"
                v-hasPermi="['system:notice:remove']"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 添加或修改公告对话框 -->
    <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
      <el-form ref="formRef" :model="state.data" :rules="formRules" label-width="80px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="公告标题" prop="noticeTitle">
              <el-input v-model="state.data.noticeTitle" placeholder="请输入公告标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公告类型" prop="noticeType">
              <el-select v-model="state.data.noticeType" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="dict in sys_notice_type"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="状态">
              <el-radio-group v-model="state.data.status">
                <el-radio v-for="dict in sys_notice_status" :key="dict.value" :value="dict.value">
                  {{ dict.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="内容">
              <editor v-model="state.data.noticeContent" :min-height="192" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </ZxDialog>
  </ZxContentWrap>
</template>

<script setup name="Notice">
import { listNotice, getNotice, delNotice, addNotice, updateNotice } from '@/api/system/notice';
import { useDialog } from '@zxio/zxui';
import { ElMessage } from 'element-plus';

const { proxy } = getCurrentInstance();
const { sys_notice_status, sys_notice_type } = proxy.useDict(
  'sys_notice_status',
  'sys_notice_type'
);

const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref(null);
const formRef = ref(null);

const formRules = {
  noticeTitle: [{ required: true, message: '公告标题不能为空', trigger: 'blur' }],
  noticeType: [{ required: true, message: '公告类型不能为空', trigger: 'change' }],
};

const { state, dialogProps, dialogEvents, open: openDialog, setLoading } = useDialog({
  title: (data) => (data?.noticeId ? '修改公告' : '添加公告'),
  width: '780px',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    noticeId: undefined,
    noticeTitle: undefined,
    noticeType: undefined,
    noticeContent: undefined,
    status: '0',
  }),
  onConfirm: async (data) => {
    if (data.noticeId !== undefined) {
      await updateNotice(data);
      ElMessage.success('修改成功');
    } else {
      await addNotice(data);
      ElMessage.success('新增成功');
    }
    gridListRef.value?.refresh();
  },
  onConfirmError: (e) => {
    ElMessage.error(e?.message || '提交失败，请重试');
  },
});

async function loadNoticeData(params) {
  const queryData = {
    pageNum: params.page,
    pageSize: params.size,
    noticeTitle: params.query?.noticeTitle,
    createBy: params.query?.createBy,
    noticeType: params.query?.noticeType,
  };
  try {
    const response = await listNotice(queryData);
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


/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.noticeId);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  openDialog();
}

/** 修改按钮操作 */
async function handleUpdate(row) {
  const noticeId = row?.noticeId || ids.value[0];
  if (!noticeId) {
    return;
  }
  setLoading(true);
  try {
    const response = await getNotice(noticeId);
    openDialog(response.data);
  } finally {
    setLoading(false);
  }
}

/** 删除按钮操作 */
function handleDelete(row) {
  const noticeIds = row.noticeId || ids.value;
  proxy.$modal
    .confirm('是否确认删除公告编号为"' + noticeIds + '"的数据项？')
    .then(() => delNotice(noticeIds))
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
</script>
