<template>
  <!-- 授权用户 -->
  <ZxDialog
    dialog-size="lg"
    :draggable="false"
    :show-full-screen="false"
    :destroy-on-close="false"
    :close-on-click-modal="true"
    title="选择用户"
    v-model="visible"
  >
    <DictStatus :types="['sys_normal_disable']" />
    <el-form :model="queryParams" ref="queryRef" :inline="true">
      <el-form-item label="用户名称" prop="userName">
        <zx-input
          v-model="queryParams.userName"
          placeholder="请输入用户名称"
          clearable
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="手机号码" prop="phonenumber">
        <zx-input
          v-model="queryParams.phonenumber"
          placeholder="请输入手机号码"
          clearable
          style="width: 180px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>
    <ZxGridList
      mode="controlled"
      :rows="userList"
      :pagination="pagination"
      :status="listStatus"
      @page-change="handlePageChange"
      @refresh="getList"
    >
      <template #table="{ grid, renderEmpty }">
        <el-table
          @row-click="clickRow"
          ref="refTable"
          :data="grid.list"
          @select="handleSelectionChange"
          @select-all="handleSelectionChange"
          row-key="userId"
          height="260px"
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
        </el-table>
      </template>
    </ZxGridList>
    <p class="text-sm text-zx-text-secondary">
      已选 {{ userIds.length }} 人（跨页和搜索保留，关闭后清空）
    </p>
    <p v-if="writeError" role="alert">{{ writeError }}</p>
    <template #footer>
      <div class="dialog-footer">
        <el-button
          type="primary"
          :disabled="!canEdit || !userIds.length"
          @click="handleSelectUser"
          :loading="handleSelectUserPending"
          >确 定</el-button
        >
        <el-button @click="visible = false">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup name="SelectUser">
import { computed, getCurrentInstance, nextTick, reactive, ref, shallowRef, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { useOperation } from '@/utils/operation';
import { ElMessage } from 'element-plus';
import { captureUserCommand, roleUsersOptions, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { checkPermi } from '@/utils/permission';
import { parseTime } from '@/utils/ruoyi';

const props = defineProps({ roleId: { type: [Number, String] } });
const emit = defineEmits(['ok']);
const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const refTable = ref(null);
const visible = ref(false);
const userIds = ref([]);
const openingScope = shallowRef(null);
const openingRoleId = ref(0);
let opening = 0;
const writeError = ref('');
const queryParams = reactive({ userName: '', phonenumber: '' });
const submitted = ref({});
const currentPage = ref(1);
const pageSize = ref(10);
const canEdit = computed(
  () =>
    visible.value &&
    openingScope.value === queryScope.value &&
    checkPermi(['system:role:edit']) &&
    (openingRoleId.value !== 1 || openingScope.value?.userId === '1')
);
const usersQuery = useQuery(() =>
  roleUsersOptions(
    visible.value && openingScope.value === queryScope.value ? openingScope.value : null,
    openingRoleId.value,
    'unallocated',
    { ...submitted.value, page: currentPage.value, pageSize: pageSize.value }
  )
);
const userList = computed(() => usersQuery.data.value?.items ?? []);
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
watch(
  [queryScope, () => props.roleId],
  () => {
    visible.value = false;
  },
  { flush: 'sync' }
);
watch(
  visible,
  (value) => {
    if (!value) {
      opening++;
      userIds.value = [];
      writeError.value = '';
    }
  },
  { flush: 'sync' }
);
watch(usersQuery.data, (result) => {
  if (result)
    currentPage.value = Math.min(
      currentPage.value,
      Math.max(1, Math.ceil(result.total / pageSize.value))
    );
});
watch(
  userList,
  async () => {
    await nextTick();
    refTable.value?.clearSelection();
    for (const row of userList.value)
      if (userIds.value.includes(row.userId)) refTable.value?.toggleRowSelection(row, true);
  },
  { flush: 'post' }
);
function show() {
  opening++;
  openingScope.value = requireQueryScope();
  openingRoleId.value = Number(props.roleId);
  queryParams.userName = '';
  queryParams.phonenumber = '';
  submitted.value = {};
  currentPage.value = 1;
  pageSize.value = 10;
  userIds.value = [];
  writeError.value = '';
  refTable.value?.clearSelection();
  visible.value = true;
}
function canSelectUser(row) {
  return canEdit.value && Number(row.userId) !== 1;
}
function clickRow(row) {
  if (!canSelectUser(row)) return;
  refTable.value?.toggleRowSelection(row);
  handleSelectionChange(refTable.value?.getSelectionRows() ?? []);
}
// Element Plus select/select-all represent user intent. Data changes and restoration
// emit selection-change as well, so they must never erase off-page selections.
function handleSelectionChange(selection) {
  const currentIds = new Set(userList.value.map((row) => row.userId));
  userIds.value = [
    ...new Set([
      ...userIds.value.filter((id) => !currentIds.has(id)),
      ...selection.filter(canSelectUser).map((row) => row.userId),
    ]),
  ];
}
function getList() {
  if (visible.value && openingScope.value === queryScope.value)
    void usersQuery.refetch({ cancelRefetch: false });
}
function handleQuery() {
  const next = {
    userName: queryParams.userName.trim(),
    phonenumber: queryParams.phonenumber.trim(),
  };
  const unchanged =
    currentPage.value === 1 && JSON.stringify(next) === JSON.stringify(submitted.value);
  submitted.value = next;
  currentPage.value = 1;
  if (unchanged) getList();
}
function resetQuery() {
  queryParams.userName = '';
  queryParams.phonenumber = '';
  handleQuery();
}
function handlePageChange({ page, size }) {
  currentPage.value = size === pageSize.value ? page : 1;
  pageSize.value = size;
}
const { run: handleSelectUser, pending: handleSelectUserPending } = useOperation(async () => {
  if (!canEdit.value) return;
  if (!userIds.value.length) {
    ElMessage.error('请选择要分配的用户');
    return;
  }
  const generation = opening;
  const command = captureUserCommand(
    { roleId: openingRoleId.value, userIds: userIds.value },
    openingScope.value
  );
  writeError.value = '';
  try {
    await userCommands.assignRoleUsers(command);
    if (generation !== opening || command.scope !== queryScope.value) return;
    visible.value = false;
    emit('ok');
  } catch {
    if (generation === opening && command.scope === queryScope.value)
      writeError.value = '分配失败，已保留所选用户，请重试。';
  }
});
defineExpose({ show });
</script>
