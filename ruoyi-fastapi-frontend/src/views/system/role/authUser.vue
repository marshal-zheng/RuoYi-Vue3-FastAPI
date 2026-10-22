<template>
  <ZxContentWrap fill>
    <template #header-right>
      <ZxButton icon="Close" @click="handleClose">关闭</ZxButton>
    </template>

    <ZxGridList
      ref="gridListRef"
      mode="controlled"
      :rows="userRows"
      :pagination="pagination"
      :status="listStatus"
      @page-change="handlePageChange"
      @refresh="refreshList"
      fill
    >
      <template #form="{ loading }">
        <DictStatus :types="['sys_normal_disable']" />
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton
              type="primary"
              icon="Plus"
              :disabled="!canEdit"
              @click="openSelectUser"
              v-hasPermi="['system:role:edit']"
              >添加用户</ZxButton
            >
            <ZxButton
              plain
              type="danger"
              icon="CircleClose"
              :disabled="multiple || !canEdit"
              @click="cancelAuthUserAll"
              v-hasPermi="['system:role:edit']"
              :loading="cancelAuthUserAllPending"
              >批量取消授权</ZxButton
            >
          </template>
          <template #filters>
            <zx-input
              v-model="draft.userName"
              placeholder="请输入用户名称"
              clearable
              style="width: 240px"
              @keyup.enter="onSearch"
            />
            <zx-input
              v-model="draft.phonenumber"
              placeholder="请输入手机号码"
              clearable
              style="width: 240px"
              @keyup.enter="onSearch"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="draft.userName"
              placeholder="搜索用户名称"
              :loading="loading"
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
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <template #empty><component :is="renderEmpty" /></template>
          <el-table-column type="selection" :selectable="canSelectUser" width="55" />
          <el-table-column label="用户名称" prop="userName" :show-overflow-tooltip="true" />
          <el-table-column label="用户昵称" prop="nickName" :show-overflow-tooltip="true" />
          <el-table-column label="邮箱" prop="email" :show-overflow-tooltip="true" />
          <el-table-column label="手机" prop="phonenumber" :show-overflow-tooltip="true" />
          <el-table-column label="状态" prop="status">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" class-name="small-padding fixed-width">
            <template #default="scope">
              <div class="op-col__wrap">
                <ZxButton
                  type="danger"
                  link
                  :disabled="!canSelectUser(scope.row)"
                  @click="cancelAuthUser(scope.row)"
                  v-hasPermi="['system:role:edit']"
                  :loading="cancelAuthUserPending"
                  >取消授权</ZxButton
                >
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <p v-if="writeError" role="alert">{{ writeError }}</p>
    <select-user ref="selectRef" :roleId="roleId" />
  </ZxContentWrap>
</template>

<script setup name="AuthUser">
import { computed, getCurrentInstance, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { useOperation } from '@/utils/operation';
import selectUser from './selectUser.vue';
import { captureUserCommand, roleUsersOptions, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { checkPermi } from '@/utils/permission';
import { parseTime } from '@/utils/ruoyi';

const route = useRoute();
const { proxy } = getCurrentInstance();
const pageScope = requireQueryScope();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const roleId = computed(() => Number(route.params.roleId));
const canEdit = computed(
  () =>
    pageScope === queryScope.value &&
    checkPermi(['system:role:edit']) &&
    (roleId.value !== 1 || pageScope.userId === '1')
);
const gridListRef = ref(null);
const userTableRef = ref(null);
const selectRef = ref(null);
const userIds = ref([]);
const multiple = computed(() => userIds.value.length === 0);
const draft = reactive({ userName: '', phonenumber: '' });
const submitted = ref({});
const currentPage = ref(1);
const pageSize = ref(10);
const writeError = ref('');
const usersQuery = useQuery(() =>
  roleUsersOptions(pageScope === queryScope.value ? pageScope : null, roleId.value, 'allocated', {
    ...submitted.value,
    page: currentPage.value,
    pageSize: pageSize.value,
  })
);
const userRows = computed(() => usersQuery.data.value?.items ?? []);
const pagination = computed(() => ({
  page: currentPage.value,
  size: pageSize.value,
  total: usersQuery.data.value?.total ?? 0,
}));
const listStatus = computed(() => ({
  loading: usersQuery.isLoading.value,
  refreshing: usersQuery.isFetching.value && usersQuery.data.value !== undefined,
  error: usersQuery.error.value,
  paused: usersQuery.fetchStatus.value === 'paused',
}));
function clearSelection() {
  userIds.value = [];
  userTableRef.value?.clearSelection();
}
watch(userRows, clearSelection);
watch(usersQuery.data, (result) => {
  if (result)
    currentPage.value = Math.min(
      currentPage.value,
      Math.max(1, Math.ceil(result.total / pageSize.value))
    );
});
watch(
  [queryScope, roleId],
  () => {
    draft.userName = '';
    draft.phonenumber = '';
    submitted.value = {};
    currentPage.value = 1;
    pageSize.value = 10;
    writeError.value = '';
    clearSelection();
  },
  { flush: 'sync' }
);
function onSearch() {
  const next = {
    userName: draft.userName.trim(),
    phonenumber: draft.phonenumber.trim(),
  };
  const unchanged =
    currentPage.value === 1 && JSON.stringify(next) === JSON.stringify(submitted.value);
  submitted.value = next;
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
  if (pageScope === queryScope.value) void usersQuery.refetch({ cancelRefetch: false });
}
function canSelectUser(row) {
  return canEdit.value && Number(row.userId) !== 1;
}
function handleSelectionChange(selection) {
  userIds.value = selection.filter(canSelectUser).map((item) => item.userId);
}
function openSelectUser() {
  if (canEdit.value) selectRef.value?.show();
}
function handleClose() {
  proxy.$tab.closeOpenPage({ path: '/system/role' });
}
const { run: cancelAuthUser, pending: cancelAuthUserPending } = useOperation(async (row) => {
  if (!canSelectUser(row)) return;
  const command = captureUserCommand({ userId: row.userId, roleId: roleId.value }, pageScope);
  try {
    await proxy.$modal.confirm('确认要取消该用户"' + row.userName + '"角色吗？');
  } catch {
    return;
  }
  writeError.value = '';
  try {
    await userCommands.unassignRoleUser(command);
  } catch {
    if (command.scope === queryScope.value && command.input.roleId === roleId.value)
      writeError.value = '取消授权失败，请重试。';
  }
});
const { run: cancelAuthUserAll, pending: cancelAuthUserAllPending } = useOperation(async () => {
  if (!canEdit.value || multiple.value) return;
  const command = captureUserCommand({ roleId: roleId.value, userIds: userIds.value }, pageScope);
  try {
    await proxy.$modal.confirm('是否取消选中用户授权数据项?');
  } catch {
    return;
  }
  writeError.value = '';
  try {
    await userCommands.unassignRoleUsers(command);
  } catch {
    if (command.scope === queryScope.value && command.input.roleId === roleId.value)
      writeError.value = '取消授权失败，请重试。';
  }
});
</script>
