<template>
  <ZxContentWrap fill>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadRoleData"
      :query-transform="queryTransform"
      :show-pagination="true"
      :load-on-mounted="true"
      fill
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:role:add']"
              >新增</ZxButton
            >
            <ZxButton
              type="success"
              icon="Edit"
              :disabled="single"
              @click="handleUpdate"
              v-hasPermi="['system:role:edit']"
              >修改</ZxButton
            >
            <ZxButton
              type="danger"
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete"
              v-hasPermi="['system:role:remove']"
              :loading="handleDeletePending"
              >删除</ZxButton
            >
            <ZxButton
              type="warning"
              icon="Download"
              @click="handleExport"
              v-hasPermi="['system:role:export']"
              >导出</ZxButton
            >
          </template>
          <template #filters>
            <zx-input
              v-model="query.roleKey"
              placeholder="请输入权限字符"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <DictSelect
              dict-type="sys_normal_disable"
              v-model="query.status"
              placeholder="角色状态"
              clearable
              style="width: 160px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            />
            <el-date-picker
              v-model="query.dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
              @change="(v) => onFilterChange('dateRange', v, { handleRefresh, updateState })"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="query.roleName"
              placeholder="搜索角色名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </template>
        </ZxListToolbar>
      </template>
      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :data="grid.list || []"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
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
                v-model="scope.row.status"
                active-value="0"
                inactive-value="1"
                :disabled="statusOperations.get(scope.row)?.pending.value"
                @change="handleStatusChange(scope.row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" class-name="small-padding">
            <template #default="scope">
              <div class="op-col__wrap">
                <ZxButton
                  v-if="scope.row.roleId !== 1"
                  type="text"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['system:role:edit']"
                  >修改</ZxButton
                >
                <zx-button
                  v-if="scope.row.roleId !== 1"
                  type="text"
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
import { shallowReactive } from 'vue';

import { useOperation } from '@/utils/operation';
import { serializeDateRange } from '@/utils/ruoyi';
import { changeRoleStatus, delRole, listRole } from '@/api/system/role';
import { checkPermi } from '@/utils/permission';
import RoleFormDrawer from './components/RoleFormDrawer.vue';
import RoleDataScopeDrawer from './components/RoleDataScopeDrawer.vue';

const router = useRouter();
const { proxy } = getCurrentInstance();

const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const gridListRef = ref(null);
const roleFormDrawerRef = ref(null);
const roleDataScopeDrawerRef = ref(null);

/** 使用 GridList 的 queryTransform 处理日期范围 */
function queryTransform(query) {
  return serializeDateRange(query);
}

/** GridList 数据加载函数 - 不处理参数转换 */
async function loadRoleData(params) {
  try {
    return await listRole({
      ...params.query,
      page: params.pager?.page,
      pageSize: params.pager?.size,
    });
  } catch {
    return { items: [], total: 0 };
  }
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState(`query.${field}`, value);
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}
/** 删除按钮操作 */
const { run: handleDelete, pending: handleDeletePending } = useOperation(async (row) => {
  const roleIds = row.roleId || ids.value;
  await proxy.$modal
    .confirm('是否确认删除角色编号为"' + roleIds + '"的数据项?')
    .then(function () {
      return delRole(roleIds);
    })
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
});
function handleExport() {
  const snapshot = gridListRef.value?.getStateSnapshot();
  if (!snapshot) return;
  proxy.download(
    'system/role/export',
    queryTransform(snapshot.query),
    `role_${new Date().getTime()}.xlsx`
  );
}

/** 多选框选中数据 */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.roleId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 角色状态修改 */
const statusOperations = shallowReactive(new WeakMap());
function handleStatusChange(row) {
  let operation = statusOperations.get(row);
  if (!operation) {
    operation = useOperation(async () => {
      let text = row.status === '0' ? '启用' : '停用';
      await proxy.$modal
        .confirm('确认要"' + text + '""' + row.roleName + '"角色吗?')
        .then(function () {
          return changeRoleStatus(row.roleId, row.status);
        })
        .then(() => {})
        .catch(function () {
          row.status = row.status === '0' ? '1' : '0';
        });
    });
    statusOperations.set(row, operation);
  }
  return operation.run();
}

/** 分配用户 */
function handleAuthUser(row) {
  router.push('/system/role-auth/user/' + row.roleId);
}

/** 添加角色 */
function handleAdd() {
  return roleFormDrawerRef.value?.open().catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 修改角色 */
function handleUpdate(row) {
  const roleId = row?.roleId || ids.value[0];
  if (!roleId) return;
  return roleFormDrawerRef.value?.open(roleId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 分配数据权限操作 */
function handleDataScope(row) {
  return roleDataScopeDrawerRef.value?.open(row.roleId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 抽屉成功回调 */
function handleDrawerSuccess() {
  gridListRef.value?.refresh();
}

function getRoleMoreActionList() {
  const actions = [];
  if (checkPermi(['system:role:edit'])) {
    actions.push({ label: '数据权限', eventTag: 'dataScope' });
  }
  if (checkPermi(['system:role:remove'])) {
    actions.push({ label: '删除', eventTag: 'delete' });
  }
  return actions;
}

function handleRoleMoreActionSelect(item, row) {
  switch (item.eventTag) {
    case 'dataScope':
      handleDataScope(row);
      break;
    case 'authUser':
      handleAuthUser(row);
      break;
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
