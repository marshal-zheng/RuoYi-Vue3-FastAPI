<template>
  <ZxContentWrap
    :show-footer="true"
    :footer-fixed="true"
    :buttons="footerButtons"
    fill
    @save="handleSave"
    @cancel="handleCancel"
  >
    <template #title>
      <div class="flex items-center gap-6">
        <span class="text-lg font-semibold">角色授权</span>
        <span class="text-sm text-zx-text-secondary">用户昵称：{{ form.nickName }}</span>
        <span class="text-sm text-zx-text-secondary">登录账号：{{ form.userName }}</span>
      </div>
    </template>

    <ZxGridList
      ref="gridListRef"
      mode="controlled"
      :rows="roleRows"
      :pagination="pagination"
      :status="listStatus"
      @page-change="handlePageChange"
      @refresh="refreshRoles"
      fill
    >
      <template #table="{ grid, renderEmpty }">
        <el-table
          v-loading="grid.loading"
          :row-key="getRowKey"
          @row-click="clickRow"
          ref="roleRef"
          @select="handleSelectionChange"
          @select-all="handleSelectionChange"
          :data="grid.list || []"
        >
          <template #empty><component :is="renderEmpty" /></template>
          <el-table-column label="序号" width="55" type="index" />
          <el-table-column type="selection" :selectable="canSelectRole" width="55" />
          <el-table-column label="角色编号" prop="roleId" />
          <el-table-column label="角色名称" prop="roleName" :show-overflow-tooltip="true" />
          <el-table-column label="权限字符" prop="roleKey" :show-overflow-tooltip="true" />
          <el-table-column label="状态" width="100">
            <template #default="scope">{{ scope.row.status === '1' ? '已停用' : '正常' }}</template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
    <p v-if="protectedRoles" role="status">该用户包含管理员角色，需要管理员调整授权。</p>
    <p v-if="writeError" role="alert">{{ writeError }}</p>
  </ZxContentWrap>
</template>

<script setup name="AuthRole">
import { computed, getCurrentInstance, nextTick, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { useOperation } from '@/utils/operation';
import { captureUserCommand, userAuthRoleOptions, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { checkPermi } from '@/utils/permission';
import { parseTime } from '@/utils/ruoyi';

const route = useRoute();
const { proxy } = getCurrentInstance();
const pageScope = requireQueryScope();
const userId = computed(() => Number(route.params.userId));
const roleIds = ref([]);
const form = ref({});
const rolesAll = ref([]);
const initialized = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const gridListRef = ref(null);
const roleRef = ref(null);
const writeError = ref('');
const rolesQuery = useQuery(() =>
  userAuthRoleOptions(pageScope === queryScope.value ? pageScope : null, userId.value)
);
const protectedRoles = computed(
  () => pageScope.userId !== '1' && rolesAll.value.some((row) => row.roleId === 1 && row.flag)
);
const canEdit = computed(
  () =>
    pageScope === queryScope.value &&
    userId.value !== 1 &&
    checkPermi(['system:user:edit']) &&
    !protectedRoles.value
);
const roleRows = computed(() =>
  rolesAll.value.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
);
const pagination = computed(() => ({
  page: currentPage.value,
  size: pageSize.value,
  total: rolesAll.value.length,
}));
const listStatus = computed(() => ({
  loading: rolesQuery.isLoading.value,
  refreshing: rolesQuery.isFetching.value && rolesQuery.data.value !== undefined,
  error: rolesQuery.error.value,
  paused: rolesQuery.fetchStatus.value === 'paused',
}));
// Each route owns one editable snapshot. A background refresh may update the
// resource cache but cannot replace selections that the user is editing.
watch(
  [rolesQuery.data, rolesQuery.isFetching, rolesQuery.isError],
  ([response, fetching, error]) => {
    if (
      initialized.value ||
      fetching ||
      error ||
      !response ||
      Number(response.user?.userId) !== userId.value ||
      pageScope !== queryScope.value
    )
      return;
    form.value = { ...response.user };
    rolesAll.value = (response.roles ?? []).map((row) => ({ ...row }));
    roleIds.value = rolesAll.value.filter((row) => row.flag).map((row) => row.roleId);
    initialized.value = true;
  },
  { immediate: true }
);
watch(
  [queryScope, userId],
  () => {
    roleIds.value = [];
    form.value = {};
    rolesAll.value = [];
    initialized.value = false;
    currentPage.value = 1;
    pageSize.value = 10;
    writeError.value = '';
  },
  { flush: 'sync' }
);
watch(
  roleRows,
  async () => {
    await nextTick();
    roleRef.value?.clearSelection();
    for (const row of roleRows.value)
      if (roleIds.value.includes(row.roleId)) roleRef.value?.toggleRowSelection(row, true);
  },
  { flush: 'post' }
);
function canSelectRole(row) {
  return (
    initialized.value &&
    canEdit.value &&
    (row.roleId !== 1 || pageScope.userId === '1') &&
    (row.status !== '1' || row.flag)
  );
}
function clickRow(row) {
  if (!canSelectRole(row)) return;
  roleRef.value?.toggleRowSelection(row);
  handleSelectionChange(roleRef.value?.getSelectionRows() ?? []);
}
function handleSelectionChange(selection) {
  const currentIds = new Set(roleRows.value.map((row) => row.roleId));
  roleIds.value = [
    ...new Set([
      ...roleIds.value.filter((id) => !currentIds.has(id)),
      ...selection.map((row) => row.roleId),
    ]),
  ];
}
function getRowKey(row) {
  return row.roleId;
}
function handlePageChange({ page, size }) {
  currentPage.value = size === pageSize.value ? page : 1;
  pageSize.value = size;
}
function refreshRoles() {
  if (pageScope === queryScope.value) void rolesQuery.refetch({ cancelRefetch: false });
}
function close() {
  proxy.$tab.closeOpenPage({ path: '/system/user' });
}
const { run: submitForm, pending: submitPending } = useOperation(async () => {
  if (!initialized.value || !canEdit.value) return;
  const command = captureUserCommand(
    { userId: form.value.userId, roleIds: roleIds.value },
    pageScope
  );
  writeError.value = '';
  try {
    await userCommands.assignRoles(command);
    if (command.scope === queryScope.value && command.input.userId === userId.value) close();
  } catch {
    if (command.scope === queryScope.value && command.input.userId === userId.value)
      writeError.value = '保存失败，已保留角色选择，请重试。';
  }
});
const footerButtons = computed(() => [
  { key: 'cancel', text: '关闭', variant: 'default' },
  {
    key: 'save',
    type: 'primary',
    text: '保存',
    disabled: !initialized.value || !canEdit.value,
    loading: submitPending.value,
  },
]);
function handleSave() {
  return submitForm();
}
function handleCancel() {
  close();
}
</script>
