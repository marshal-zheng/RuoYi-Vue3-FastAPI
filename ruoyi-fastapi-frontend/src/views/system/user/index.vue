<template>
  <ZxContentWrap title="用户管理" contentPadding="0px 20px 20px 0" fill>
    <template #header-right>
      <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:user:add']"
        >新增用户</ZxButton
      >
      <ZxButton
        type="success"
        icon="Edit"
        :disabled="single"
        @click="handleUpdate"
        v-hasPermi="['system:user:edit']"
        >修改</ZxButton
      >
      <ZxButton
        type="danger"
        icon="Delete"
        :disabled="multiple"
        @click="handleDelete"
        v-hasPermi="['system:user:remove']"
        :loading="handleDeletePending"
        >删除</ZxButton
      >
      <ZxButton type="info" icon="Upload" @click="handleImport" v-hasPermi="['system:user:import']"
        >导入</ZxButton
      >
      <ZxButton
        type="warning"
        icon="Download"
        @click="handleExport"
        v-hasPermi="['system:user:export']"
        >导出</ZxButton
      >
    </template>
    <div data-zx-fill>
      <zx-split-box
        :direction="appStore.device === 'mobile' ? 'vertical' : 'horizontal'"
        size="220px"
      >
        <!-- 部门数据 -->
        <template #first>
          <div class="h-full flex flex-col p-3 space-y-3">
            <div>
              <zx-input
                v-model="deptName"
                placeholder="请输入部门名称"
                clearable
                prefix-icon="Search"
                class="w-full"
              />
            </div>
            <div class="flex-1 overflow-auto" v-loading="deptStatus.loading">
              <div v-if="deptStatus.error" role="alert">
                部门读取失败
                <ZxButton type="text" @click="refreshDepartments">重试</ZxButton>
              </div>
              <div v-else-if="deptStatus.paused" role="status">部门等待网络连接</div>
              <el-tree
                :data="deptOptions"
                :props="{ label: 'label', children: 'children' }"
                :expand-on-click-node="false"
                :filter-node-method="filterNode"
                ref="deptTreeRef"
                node-key="id"
                highlight-current
                default-expand-all
                @node-click="handleNodeClick"
              />
            </div>
          </div>
        </template>

        <!-- 用户数据 -->
        <template #second>
          <div data-zx-fill>
            <ZxGridList
              v-if="queryScope"
              :key="queryScope.key"
              mode="controlled"
              :rows="userRows"
              :pagination="pagination"
              :status="listStatus"
              fill
              @page-change="handlePageChange"
              @refresh="refreshList"
            >
              <template #form>
                <ZxListToolbar aria-label="列表操作与筛选">
                  <template #filters>
                    <zx-input
                      v-model="draft.userName"
                      placeholder="请输入用户名称"
                      clearable
                      style="width: 240px"
                      @change="onSearch"
                    />
                    <zx-input
                      v-model="draft.phonenumber"
                      placeholder="请输入手机号码"
                      clearable
                      style="width: 240px"
                      @change="onSearch"
                    />
                    <DictSelect
                      dict-type="sys_normal_disable"
                      v-model="draft.status"
                      placeholder="用户状态"
                      clearable
                      style="width: 240px"
                      @change="onSearch"
                    />
                    <el-date-picker
                      v-model="draft.dateRange"
                      value-format="YYYY-MM-DD"
                      type="daterange"
                      range-separator="-"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      style="width: 308px"
                      @change="onSearch"
                    />
                  </template>
                  <template #search>
                    <ZxSearch
                      v-model="draft.userName"
                      placeholder="搜索用户名称"
                      :loading="listStatus.loading"
                      search-mode="click"
                      @search="onSearch"
                      @clear="onSearch"
                    />
                  </template>
                </ZxListToolbar>
              </template>

              <template #table="{ grid, renderEmpty }">
                <el-table
                  ref="userTableRef"
                  :data="grid.list || []"
                  @selection-change="handleSelectionChange"
                >
                  <template #empty>
                    <component :is="renderEmpty" />
                  </template>
                  <el-table-column type="selection" width="50" />
                  <el-table-column
                    label="用户编号"
                    key="userId"
                    prop="userId"
                    v-if="columns[0].visible"
                  />
                  <el-table-column
                    label="用户名称"
                    key="userName"
                    prop="userName"
                    v-if="columns[1].visible"
                    :show-overflow-tooltip="true"
                  />
                  <el-table-column
                    label="用户昵称"
                    key="nickName"
                    prop="nickName"
                    v-if="columns[2].visible"
                    :show-overflow-tooltip="true"
                  />
                  <el-table-column
                    label="部门"
                    key="deptName"
                    prop="dept.deptName"
                    v-if="columns[3].visible"
                    :show-overflow-tooltip="true"
                  />
                  <el-table-column
                    label="手机号码"
                    key="phonenumber"
                    prop="phonenumber"
                    v-if="columns[4].visible"
                    width="120"
                  />
                  <el-table-column label="状态" key="status" v-if="columns[5].visible">
                    <template #default="scope">
                      <el-switch
                        :model-value="scope.row.status"
                        active-value="0"
                        inactive-value="1"
                        :loading="statusOperations.get(scope.row.userId)?.pending.value"
                        :disabled="statusOperations.has(scope.row.userId)"
                        @change="(value) => handleStatusChange(value, scope.row)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column
                    label="创建时间"
                    prop="createTime"
                    v-if="columns[6].visible"
                    width="160"
                  >
                    <template #default="scope">
                      <span>{{ parseTime(scope.row.createTime) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
                    <template #default="scope">
                      <div class="op-col__wrap">
                        <ZxButton
                          v-if="scope.row.userId !== 1"
                          type="text"
                          @click="handleUpdate(scope.row)"
                          v-hasPermi="['system:user:edit']"
                          >修改</ZxButton
                        >
                        <ZxButton
                          v-if="scope.row.userId !== 1"
                          type="text"
                          @click="handleAuthRole(scope.row)"
                          v-hasPermi="['system:user:edit']"
                          >分配角色</ZxButton
                        >
                        <ZxMoreAction
                          v-if="scope.row.userId !== 1 && getUserMoreActionList().length"
                          :list="getUserMoreActionList()"
                          @select="handleMoreActionSelect($event, scope.row)"
                        />
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
            </ZxGridList>
          </div>
        </template>
      </zx-split-box>
    </div>

    <!-- 添加或修改用户配置对话框 -->
    <UserFormDialog ref="userFormDialogRef" @success="handleDialogSuccess" />

    <!-- 用户导入对话框 -->
    <UserImportDialog ref="userImportDialogRef" @success="handleDialogSuccess" />
  </ZxContentWrap>
</template>

<script setup name="User">
import { computed, getCurrentInstance, reactive, ref, shallowReactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { queryScope } from '@/queries/context';
import {
  captureUserCommand,
  normalizeUserFilters,
  userCommands,
  userListOptions,
} from '@/queries/system/user';
import { copyUserDeptTree, userDeptTreeOptions } from '@/queries/system/dept';
import { useOperation } from '@/utils/operation';
import useAppStore from '@/store/modules/app';
import { checkPermi } from '@/utils/permission';
import UserFormDialog from './components/UserFormDialog.vue';
import UserImportDialog from './components/UserImportDialog.vue';

const router = useRouter();
const appStore = useAppStore();
const { proxy } = getCurrentInstance();
const userTableRef = ref();
const deptTreeRef = ref();
const userFormDialogRef = ref();
const userImportDialogRef = ref();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const deptName = ref('');
const draft = reactive({});
const submitted = ref(normalizeUserFilters({}));
const currentPage = ref(1);
const pageSize = ref(10);
const emptyRows = Object.freeze([]);

const userQuery = useQuery(() =>
  userListOptions(queryScope.value, {
    ...submitted.value,
    page: currentPage.value,
    pageSize: pageSize.value,
  })
);
const departmentQuery = useQuery(() => userDeptTreeOptions(queryScope.value));
const userRows = computed(() => userQuery.data.value?.items ?? emptyRows);
const pagination = computed(() => ({
  page: currentPage.value,
  size: pageSize.value,
  total: userQuery.data.value?.total ?? 0,
}));
const listStatus = computed(() => ({
  loading: userQuery.isLoading.value,
  refreshing: userQuery.isFetching.value && userQuery.data.value !== undefined,
  error: userQuery.error.value,
  paused: userQuery.fetchStatus.value === 'paused',
}));
const deptOptions = computed(() => copyUserDeptTree(departmentQuery.data.value ?? emptyRows));
const deptStatus = computed(() => ({
  loading: departmentQuery.isLoading.value,
  error: departmentQuery.error.value,
  paused: departmentQuery.fetchStatus.value === 'paused',
}));
const columns = ref([
  { key: 0, label: '用户编号', visible: true },
  { key: 1, label: '用户名称', visible: true },
  { key: 2, label: '用户昵称', visible: true },
  { key: 3, label: '部门', visible: true },
  { key: 4, label: '手机号码', visible: true },
  { key: 5, label: '状态', visible: true },
  { key: 6, label: '创建时间', visible: true },
]);
const filterNode = (value, data) => !value || data.label.includes(value);
watch(deptName, (value) => deptTreeRef.value?.filter(value));
function clearSelection() {
  userTableRef.value?.clearSelection();
  handleSelectionChange([]);
}
watch(userRows, clearSelection);
// A delete may remove the last row on the last page. Wait for that page's result
// before correcting the page; pending keys must not be clamped using an old total.
watch(userQuery.data, (result) => {
  if (!result) return;
  const lastPage = Math.max(1, Math.ceil(result.total / pageSize.value));
  if (currentPage.value > lastPage) currentPage.value = lastPage;
});
const statusOperations = shallowReactive(new Map());
watch(
  queryScope,
  () => {
    Object.keys(draft).forEach((key) => delete draft[key]);
    submitted.value = normalizeUserFilters({});
    currentPage.value = 1;
    pageSize.value = 10;
    deptName.value = '';
    deptTreeRef.value?.setCurrentKey(null);
    statusOperations.clear();
    clearSelection();
  },
  { flush: 'sync' }
);
function handleNodeClick(data) {
  draft.deptId = data.id;
  onSearch();
}
function onSearch() {
  const nextFilters = normalizeUserFilters(draft);
  const unchanged =
    currentPage.value === 1 &&
    Object.keys(nextFilters).length === Object.keys(submitted.value).length &&
    Object.entries(nextFilters).every(([key, value]) => submitted.value[key] === value);
  submitted.value = nextFilters;
  currentPage.value = 1;
  clearSelection();
  if (unchanged) refreshList();
}
function handlePageChange({ page, size }) {
  currentPage.value = size === pageSize.value ? page : 1;
  pageSize.value = size;
  clearSelection();
}
function refreshList() {
  if (queryScope.value) void userQuery.refetch({ cancelRefetch: false });
}
function refreshDepartments() {
  if (queryScope.value) void departmentQuery.refetch({ cancelRefetch: false });
}
function handleExport() {
  if (!queryScope.value) return;
  proxy.download('system/user/export', { ...submitted.value }, `user_${Date.now()}.xlsx`);
}

const deleteOperation = useOperation(async (command, message) => {
  try {
    await proxy.$modal.confirm(message, '删除用户', {
      confirmButtonText: '删除',
      autofocus: false,
      closeOnClickModal: false,
    });
    await userCommands.deleteUsers(command);
    if (queryScope.value?.key === command.scope.key) clearSelection();
  } catch {
    // Confirmation cancellation or the public command's HTTP feedback completes this flow.
  }
});
const handleDeletePending = deleteOperation.pending;
function handleDelete(row = {}) {
  const scope = queryScope.value;
  const selected = row.userId ? [row.userId] : [...ids.value];
  if (!scope || !selected.length) return Promise.resolve();
  const message = row.userId
    ? `确认删除用户“${row.userName || `编号 ${row.userId}`}”吗？`
    : `确认删除选中的 ${selected.length} 位用户吗？`;
  return deleteOperation.run(captureUserCommand(selected, scope), message);
}
function handleStatusChange(status, row) {
  const scope = queryScope.value;
  if (!scope || status === row.status) return Promise.resolve();
  const existing = statusOperations.get(row.userId);
  if (existing) return existing.run();
  const command = captureUserCommand({ userId: row.userId, status }, scope);
  const text = status === '0' ? '启用' : '停用';
  const operation = useOperation(async () => {
    try {
      await proxy.$modal.confirm(`确认${text}用户“${row.userName}”吗？`, `${text}用户`, {
        confirmButtonText: text,
        autofocus: status === '1' ? false : undefined,
      });
      await userCommands.changeStatus(command);
    } catch {
      // Rows remain server-owned on cancellation and failure; no rollback mutation is needed.
    } finally {
      if (statusOperations.get(row.userId) === operation) statusOperations.delete(row.userId);
    }
  });
  statusOperations.set(row.userId, operation);
  return operation.run();
}
function handleAuthRole(row) {
  router.push('/system/user-auth/role/' + row.userId);
}
const resetPasswordOperation = useOperation(async (scope, userId, userName) => {
  try {
    const { value } = await proxy.$prompt('请输入"' + userName + '"的新密码', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      closeOnClickModal: false,
      inputPattern: /^.{5,20}$/,
      inputErrorMessage: '用户密码长度必须介于 5 和 20 之间',
      inputValidator: (value) => {
        if (/<|>|"|'|\||\\/.test(value)) return '不能包含非法字符';
      },
    });
    await userCommands.resetPassword(captureUserCommand({ userId, password: value }, scope));
    if (queryScope.value?.key === scope.key)
      proxy.$modal.alertSuccess('修改成功，新密码是：' + value);
  } catch {
    // The command rejects expired scopes before sending and owns write feedback.
  }
});
function handleResetPwd(row) {
  const scope = queryScope.value;
  if (scope) return resetPasswordOperation.run(scope, row.userId, row.userName);
}
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.userId);
  single.value = selection.length !== 1;
  multiple.value = selection.length === 0;
}
function handleImport() {
  userImportDialogRef.value?.open();
}
function handleAdd() {
  return userFormDialogRef.value?.open().catch(() => {
    // The dialog owns current-read feedback and ignores expired opens.
  });
}
function handleUpdate(row = {}) {
  const userId = row.userId || ids.value[0];
  return userFormDialogRef.value?.open(userId).catch(() => {
    // The dialog owns current-read feedback and ignores expired opens.
  });
}
function handleDialogSuccess() {
  clearSelection();
}
function getUserMoreActionList() {
  const actions = [];
  if (checkPermi(['system:user:resetPwd']))
    actions.push({ label: '重置密码', eventTag: 'resetPwd' });
  if (checkPermi(['system:user:remove'])) actions.push({ label: '删除', eventTag: 'delete' });
  return actions;
}
function handleMoreActionSelect(item, row) {
  switch (item.eventTag) {
    case 'resetPwd':
      handleResetPwd(row);
      break;
    case 'authRole':
      handleAuthRole(row);
      break;
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
