<template>
  <ZxContentWrap title="用户管理" contentPadding="0px 20px 20px 0">
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
        >删除</ZxButton
      >
      <ZxButton type="info" icon="Upload" @click="handleImport" v-hasPermi="['system:user:import']"
        >导入</ZxButton
      >
      <ZxButton
        type="warning"
        icon="Download"
        @click="() => onExport({ query })"
        v-hasPermi="['system:user:export']"
        >导出</ZxButton
      >
    </template>
    <div class="h-full">
      <zx-split-box
        :direction="appStore.device === 'mobile' ? 'vertical' : 'horizontal'"
        size="220px"
      >
        <!-- 部门数据 -->
        <template #first>
          <div class="h-full flex flex-col p-3 space-y-3">
            <div>
              <el-input
                v-model="deptName"
                placeholder="请输入部门名称"
                clearable
                prefix-icon="Search"
                class="w-full"
              />
            </div>
            <div class="flex-1 overflow-auto">
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
          <div class="h-full">
            <ZxGridList
              ref="gridListRef"
              :load-data="loadUserData"
              class="zx-grid-list--page"
              :pageViewportOffset="10"
            >
              <template #form="{ query, loading, refresh: handleRefresh, updateState }">
                <div class="zx-grid-form-bar">
                  <div class="zx-grid-form-bar__left"></div>
                  <div class="zx-grid-form-bar__filters">
                    <el-input
                      v-model="query.userName"
                      placeholder="请输入用户名称"
                      clearable
                      style="width: 240px"
                      @change="(v) => onFilterChange('userName', v, { handleRefresh, updateState })"
                    />
                    <el-input
                      v-model="query.phonenumber"
                      placeholder="请输入手机号码"
                      clearable
                      style="width: 240px"
                      @change="
                        (v) => onFilterChange('phonenumber', v, { handleRefresh, updateState })
                      "
                    />
                    <el-select
                      v-model="query.status"
                      placeholder="用户状态"
                      clearable
                      style="width: 240px"
                      @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
                    >
                      <el-option
                        v-for="dict in sys_normal_disable"
                        :key="dict.value"
                        :label="dict.label"
                        :value="dict.value"
                      />
                    </el-select>
                    <el-date-picker
                      v-model="query.dateRange"
                      value-format="YYYY-MM-DD"
                      type="daterange"
                      range-separator="-"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      style="width: 308px"
                      @change="
                        (v) => onFilterChange('dateRange', v, { handleRefresh, updateState })
                      "
                    />
                  </div>
                  <div class="zx-grid-form-bar__right">
                    <ZxSearch
                      v-model="query.userName"
                      placeholder="搜索用户名称"
                      :loading="loading"
                      search-mode="click"
                      @search="() => onSearch({ handleRefresh, updateState })"
                      @clear="() => onSearch({ handleRefresh, updateState })"
                    />
                    <!-- <right-toolbar
                      v-model:showSearch="showSearch"
                      @queryTable="handleRefresh"
                      :columns="columns"
                    /> -->
                  </div>
                </div>
              </template>

              <template #table="{ grid }">
                <el-table
                  v-loading="grid.loading"
                  :data="grid.list || []"
                  @selection-change="handleSelectionChange"
                >
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
                        v-model="scope.row.status"
                        active-value="0"
                        inactive-value="1"
                        @change="handleStatusChange(scope.row)"
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
                          v-if="scope.row.userId !== 1 && getUserMoreActionList(scope.row).length"
                          :list="getUserMoreActionList(scope.row)"
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
    <UserFormDialog
      ref="userFormDialogRef"
      :dept-options="enabledDeptOptions"
      :status-options="sys_normal_disable"
      :sex-options="sys_user_sex"
      @success="handleDialogSuccess"
    />

    <!-- 用户导入对话框 -->
    <UserImportDialog ref="userImportDialogRef" @success="handleDialogSuccess" />
  </ZxContentWrap>
</template>

<script setup name="User">
import useAppStore from '@/store/modules/app';
import { checkPermi } from '@/utils/permission';
import { serializeDateRange } from '@/utils/ruoyi';
import {
  changeUserStatus,
  listUser,
  resetUserPwd,
  delUser,
  deptTreeSelect,
} from '@/api/system/user';
import UserFormDialog from './components/UserFormDialog.vue';
import UserImportDialog from './components/UserImportDialog.vue';

const router = useRouter();
const appStore = useAppStore();
const { proxy } = getCurrentInstance();
const { sys_normal_disable, sys_user_sex } = proxy.useDict('sys_normal_disable', 'sys_user_sex');

const gridListRef = ref();
const userFormDialogRef = ref();
const userImportDialogRef = ref();
const currentQuery = ref({});
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const dateRange = ref([]);
const deptSelectedId = ref();
const deptName = ref('');
const deptOptions = ref(undefined);
const enabledDeptOptions = ref(undefined);
// 列显隐信息
const columns = ref([
  { key: 0, label: `用户编号`, visible: true },
  { key: 1, label: `用户名称`, visible: true },
  { key: 2, label: `用户昵称`, visible: true },
  { key: 3, label: `部门`, visible: true },
  { key: 4, label: `手机号码`, visible: true },
  { key: 5, label: `状态`, visible: true },
  { key: 6, label: `创建时间`, visible: true },
]);

/** 通过条件过滤节点  */
const filterNode = (value, data) => {
  if (!value) return true;
  return data.label.indexOf(value) !== -1;
};
/** 根据名称筛选部门树 */
watch(deptName, (val) => {
  proxy.$refs['deptTreeRef'].filter(val);
});
/** GridList 数据加载 */
function queryTransform(query) {
  return serializeDateRange(query);
}

async function loadUserData(params) {
  const query = queryTransform({ ...(params?.query || {}), deptId: deptSelectedId.value });
  const res = await listUser({ ...params, query });
  currentQuery.value = query;
  return res;
}
/** 查询部门下拉树结构 */
function getDeptTree() {
  deptTreeSelect().then((response) => {
    // 全局 http 工具已自动解包 response.data，直接使用 response
    const data = response ?? [];
    deptOptions.value = data;
    enabledDeptOptions.value = filterDisabledDept(JSON.parse(JSON.stringify(data)));
  });
}
/** 过滤禁用的部门 */
function filterDisabledDept(deptList) {
  return deptList.filter((dept) => {
    if (dept.disabled) {
      return false;
    }
    if (dept.children && dept.children.length) {
      dept.children = filterDisabledDept(dept.children);
    }
    return true;
  });
}
/** 节点单击事件 */
function handleNodeClick(data) {
  deptSelectedId.value = data.id;
  refreshList();
}
/** 搜索按钮操作 */
function handleQuery() {
  refreshList();
}
/** 重置按钮操作 */
function resetQuery() {
  dateRange.value = [];
  deptSelectedId.value = undefined;
  proxy.$refs.deptTreeRef.setCurrentKey(null);
  refreshList();
}
/** 删除按钮操作 */
function handleDelete(row) {
  const userIds = row.userId || ids.value;
  proxy.$modal
    .confirm('是否确认删除用户编号为"' + userIds + '"的数据项？')
    .then(function () {
      return delUser(userIds);
    })
    .then(() => {
      refreshList();
    })
    .catch(() => {});
}
/** 导出按钮操作 */
function handleExport() {
  proxy.download(
    'system/user/export',
    { ...(currentQuery.value || {}) },
    `user_${new Date().getTime()}.xlsx`
  );
}
/** 用户状态修改  */
function handleStatusChange(row) {
  let text = row.status === '0' ? '启用' : '停用';
  proxy.$modal
    .confirm('确认要"' + text + '""' + row.userName + '"用户吗?')
    .then(() => changeUserStatus(row.userId, row.status))
    .catch(() => {
      row.status = row.status === '0' ? '1' : '0';
    });
}
/** 更多操作 */
function handleCommand(command, row) {
  switch (command) {
    case 'handleResetPwd':
      handleResetPwd(row);
      break;
    case 'handleAuthRole':
      handleAuthRole(row);
      break;
    default:
      break;
  }
}
/** 跳转角色分配 */
function handleAuthRole(row) {
  const userId = row.userId;
  router.push('/system/user-auth/role/' + userId);
}
/** 重置密码按钮操作 */
function handleResetPwd(row) {
  proxy
    .$prompt('请输入"' + row.userName + '"的新密码', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      closeOnClickModal: false,
      inputPattern: /^.{5,20}$/,
      inputErrorMessage: '用户密码长度必须介于 5 和 20 之间',
      inputValidator: (value) => {
        if (/<|>|"|'|\||\\/.test(value)) {
          return '不能包含非法字符：< > " \' \\\ |';
        }
      },
    })
    .then(({ value }) => {
      resetUserPwd(row.userId, value).then(() => {
        proxy.$modal.alertSuccess('修改成功，新密码是：' + value);
      });
    })
    .catch(() => {});
}
/** 选择条数  */
function handleSelectionChange(selection) {
  ids.value = selection.map((item) => item.userId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 导入按钮操作 */
function handleImport() {
  userImportDialogRef.value?.open();
}
/** 新增按钮操作 */
function handleAdd() {
  userFormDialogRef.value?.open();
}

/** 修改按钮操作 */
function handleUpdate(row) {
  const userId = row.userId || ids.value[0];
  userFormDialogRef.value?.open(userId);
}

/** 对话框成功回调 */
function handleDialogSuccess() {
  refreshList();
}

function refreshList() {
  gridListRef.value && gridListRef.value.refresh && gridListRef.value.refresh();
}

function onFilterChange(key, value, { handleRefresh, updateState }) {
  updateState({ [key]: value });
  updateState('pager.page', 1);
  handleRefresh();
}

function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}

function onExport({ query }) {
  currentQuery.value = { ...(query || {}) };
  handleExport();
}

getDeptTree();

function getUserMoreActionList(row) {
  const actions = [];
  if (checkPermi(['system:user:resetPwd'])) {
    actions.push({ label: '重置密码', eventTag: 'resetPwd' });
  }
  if (checkPermi(['system:user:remove'])) {
    actions.push({ label: '删除', eventTag: 'delete' });
  }
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
