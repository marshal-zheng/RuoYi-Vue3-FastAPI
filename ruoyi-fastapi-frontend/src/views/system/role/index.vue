<template>
  <ZxContentWrap fill>
    <ZxGridList
      v-if="queryScope"
      :key="queryScope.key"
      mode="controlled"
      :rows="roleRows"
      :pagination="pagination"
      :status="listStatus"
      @page-change="handlePageChange"
      @refresh="refreshList"
      fill
    >
      <template #form>
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:role:add']"
              >新增</ZxButton
            >
            <ZxButton
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:role:edit']"
              >修改</ZxButton
            >
            <ZxButton
              plain
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:role:remove']"
              :loading="handleDeletePending"
              >删除</ZxButton
            >
            <ZxButton icon="Download" @click="handleExport" v-hasPermi="['system:role:export']"
              >导出</ZxButton
            >
          </template>
          <template #filters>
            <zx-input
              v-model="draft.roleKey"
              placeholder="请输入权限字符"
              clearable
              style="width: 240px"
              @keyup.enter="onSearch"
            />
            <DictSelect
              dict-type="sys_normal_disable"
              v-model="draft.status"
              placeholder="角色状态"
              clearable
              style="width: 160px"
              @change="onSearch"
            />
            <el-date-picker
              v-model="draft.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
              @change="onSearch"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="draft.roleName"
              placeholder="搜索角色名称"
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
          ref="roleTableRef"
          row-key="roleId"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <template #empty>
            <component :is="renderEmpty" />
          </template>
          <el-table-column
            type="selection"
            width="55"
            :selectable="(row) => Number(row.roleId) !== 1"
          />
          <el-table-column label="角色编号" prop="roleId" width="120" />
          <el-table-column
            label="角色名称"
            prop="roleName"
            :show-overflow-tooltip="true"
            width="150"
          />
          <el-table-column
            label="权限字符"
            prop="roleKey"
            :show-overflow-tooltip="true"
            width="150"
          />
          <el-table-column label="显示顺序" prop="roleSort" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-switch
                :model-value="scope.row.status"
                active-value="0"
                inactive-value="1"
                :loading="statusOperations.get(scope.row.roleId)?.pending.value"
                :disabled="!canEditRole(scope.row) || statusOperations.has(scope.row.roleId)"
                @change="(value) => handleStatusChange(value, scope.row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime" min-width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" class-name="small-padding">
            <template #default="scope">
              <div class="op-col__wrap">
                <ZxButton
                  link
                  type="primary"
                  v-if="scope.row.roleId !== 1"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['system:role:edit']"
                  >修改</ZxButton
                >
                <zx-button
                  link
                  type="primary"
                  v-if="scope.row.roleId !== 1"
                  @click="handleAuthUser(scope.row)"
                  v-hasPermi="['system:role:edit']"
                  >分配用户</zx-button
                >
                <ZxMoreAction
                  v-if="scope.row.roleId !== 1 && getRoleMoreActionList().length"
                  :list="getRoleMoreActionList()"
                  @select="handleRoleMoreActionSelect($event, scope.row)"
                />
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <!-- 添加或修改角色抽屉 -->
    <RoleFormDrawer ref="roleFormDrawerRef" @success="handleDrawerSuccess" />

    <!-- 分配角色数据权限抽屉 -->
    <RoleDataScopeDrawer ref="roleDataScopeDrawerRef" @success="handleDrawerSuccess" />
  </ZxContentWrap>
</template>

<script setup name="Role">
import { computed, getCurrentInstance, reactive, ref, shallowReactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import { queryScope } from '@/queries/context';
import {
  captureRoleCommand,
  normalizeRoleFilters,
  roleCommands,
  roleListOptions,
} from '@/queries/system/role';
import { useSystemListNavigation } from '@/store/modules/system-list-navigation';
import { useOperation } from '@/utils/operation';
import { parseTime } from '@/utils/ruoyi';
import { checkPermi } from '@/utils/permission';
import RoleFormDrawer from './components/RoleFormDrawer.vue';
import RoleDataScopeDrawer from './components/RoleDataScopeDrawer.vue';

const router = useRouter();
const { proxy } = getCurrentInstance();
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const roleTableRef = ref(null);
const roleFormDrawerRef = ref(null);
const roleDataScopeDrawerRef = ref(null);
const listNavigation = useSystemListNavigation();
const restored = listNavigation.take('roles');
const submitted = ref(normalizeRoleFilters(restored?.filters));
const draft = reactive({
  ...submitted.value,
  ...(submitted.value.beginTime || submitted.value.endTime
    ? { dateRange: [submitted.value.beginTime, submitted.value.endTime] }
    : {}),
});
const currentPage = ref(restored?.page ?? 1);
const pageSize = ref(restored?.size ?? 10);
const emptyRows = Object.freeze([]);
const roleQuery = useQuery(() =>
  roleListOptions(queryScope.value, {
    ...submitted.value,
    page: currentPage.value,
    pageSize: pageSize.value,
  })
);
const roleRows = computed(() => roleQuery.data.value?.items ?? emptyRows);
const pagination = computed(() => ({
  page: currentPage.value,
  size: pageSize.value,
  total: roleQuery.data.value?.total ?? 0,
}));
const listStatus = computed(() => ({
  loading: roleQuery.isLoading.value,
  refreshing: roleQuery.isFetching.value && roleQuery.data.value !== undefined,
  error: roleQuery.error.value,
  paused: roleQuery.fetchStatus.value === 'paused',
}));
const statusOperations = shallowReactive(new Map());
function clearSelection() {
  roleTableRef.value?.clearSelection();
  handleSelectionChange([]);
}
watch(roleRows, clearSelection);
watch(roleQuery.data, (result) => {
  if (!result) return;
  const lastPage = Math.max(1, Math.ceil(result.total / pageSize.value));
  if (currentPage.value > lastPage) currentPage.value = lastPage;
});
watch(
  queryScope,
  () => {
    Object.keys(draft).forEach((key) => delete draft[key]);
    submitted.value = {};
    currentPage.value = 1;
    pageSize.value = 10;
    statusOperations.clear();
    clearSelection();
  },
  { flush: 'sync' }
);

function onSearch() {
  const next = normalizeRoleFilters(draft);
  const unchanged =
    currentPage.value === 1 &&
    Object.keys(next).length === Object.keys(submitted.value).length &&
    Object.entries(next).every(([key, value]) => submitted.value[key] === value);
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
  if (queryScope.value) void roleQuery.refetch({ cancelRefetch: false });
}
function handleExport() {
  if (!queryScope.value) return;
  proxy.download('system/role/export', { ...submitted.value }, `role_${Date.now()}.xlsx`);
}
function handleSelectionChange(selection) {
  ids.value = selection.filter((item) => Number(item.roleId) !== 1).map((item) => item.roleId);
  single.value = ids.value.length !== 1;
  multiple.value = ids.value.length === 0;
}
function canEditRole(row) {
  return Number(row.roleId) !== 1 && checkPermi(['system:role:edit']);
}
const deleteOperation = useOperation(async (command, message) => {
  try {
    await proxy.$modal.confirm(message);
    await roleCommands.deleteRoles(command);
    if (queryScope.value === command.scope) clearSelection();
  } catch {
    // Confirmation cancellation and HTTP feedback complete this operation.
  }
});
const handleDeletePending = deleteOperation.pending;
function handleDelete(row = {}) {
  const scope = queryScope.value;
  const selected = row.roleId ? [row.roleId] : [...ids.value];
  if (
    !scope ||
    !checkPermi(['system:role:remove']) ||
    !selected.length ||
    selected.some((id) => Number(id) === 1)
  )
    return;
  return deleteOperation.run(
    captureRoleCommand(selected, scope),
    `是否确认删除角色编号为“${selected.join(',')}”的数据项？`
  );
}
function handleStatusChange(status, row) {
  const scope = queryScope.value;
  if (!scope || !canEditRole(row) || status === row.status) return Promise.resolve();
  const existing = statusOperations.get(row.roleId);
  if (existing) return existing.run();
  const command = captureRoleCommand({ roleId: row.roleId, status }, scope);
  const text = status === '0' ? '启用' : '停用';
  const operation = useOperation(async () => {
    try {
      await proxy.$modal.confirm(`确认${text}角色“${row.roleName}”吗？`);
      await roleCommands.changeStatus(command);
    } catch {
      // Query rows remain server-owned on cancellation and failure.
    } finally {
      if (statusOperations.get(row.roleId) === operation) statusOperations.delete(row.roleId);
    }
  });
  statusOperations.set(row.roleId, operation);
  return operation.run();
}
function handleAuthUser(row) {
  if (!canEditRole(row)) return;
  listNavigation.remember('roles', {
    filters: submitted.value,
    page: currentPage.value,
    size: pageSize.value,
  });
  router.push('/system/role-auth/user/' + row.roleId);
}
function handleAdd() {
  return roleFormDrawerRef.value?.open().catch(() => {
    // The editor owns read feedback.
  });
}
function handleUpdate(row = {}) {
  const roleId = row.roleId || ids.value[0];
  if (!roleId || !canEditRole({ roleId })) return;
  return roleFormDrawerRef.value?.open(roleId).catch(() => {
    // The editor owns read feedback.
  });
}
function handleDataScope(row) {
  if (!canEditRole(row)) return;
  return roleDataScopeDrawerRef.value?.open(row.roleId).catch(() => {
    // The editor owns read feedback.
  });
}
function handleDrawerSuccess() {
  clearSelection();
}
function getRoleMoreActionList() {
  const actions = [];
  if (checkPermi(['system:role:edit'])) actions.push({ label: '数据权限', eventTag: 'dataScope' });
  if (checkPermi(['system:role:remove'])) actions.push({ label: '删除', eventTag: 'delete' });
  return actions;
}
function handleRoleMoreActionSelect(item, row) {
  if (item.eventTag === 'dataScope') handleDataScope(row);
  if (item.eventTag === 'authUser') handleAuthUser(row);
  if (item.eventTag === 'delete') handleDelete(row);
}
</script>
