<template>
  <ZxContentWrap>
    <template #header-right>
      <ZxButton type="warning" plain icon="Close" @click="handleClose">关闭</ZxButton>
    </template>

    <ZxGridList
      ref="gridListRef"
      :load-data="loadAuthUserData"
      :show-pagination="true"
      :load-on-mounted="true"
      :clear-selection-on-load="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton
              type="primary"
              icon="Plus"
              @click="openSelectUser"
              v-hasPermi="['system:role:add']"
              >添加用户</ZxButton
            >
            <ZxButton
              type="danger"
              icon="CircleClose"
              :disabled="multiple"
              @click="cancelAuthUserAll"
              v-hasPermi="['system:role:remove']"
              >批量取消授权</ZxButton
            >
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.userName"
              placeholder="请输入用户名称"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-input
              v-model="query.phonenumber"
              placeholder="请输入手机号码"
              clearable
              style="width: 240px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
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
                  link
                  type="primary"
                  @click="cancelAuthUser(scope.row)"
                  v-hasPermi="['system:role:remove']"
                  >取消授权</ZxButton
                >
              </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <select-user
      ref="selectRef"
      :roleId="route.params.roleId"
      @ok="() => gridListRef?.value?.refresh?.() || gridListRef?.refresh?.()"
    />
  </ZxContentWrap>
</template>

<script setup name="AuthUser">
import selectUser from './selectUser';
import { allocatedUserList, authUserCancel, authUserCancelAll } from '@/api/system/role';
import { parseTime } from '@/utils/ruoyi';

const route = useRoute();
const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const gridListRef = ref(null);
const selectRef = ref(null);
const multiple = ref(true);
const userIds = ref([]);

async function loadAuthUserData(params) {
  const query = {
    pageNum: params.page,
    pageSize: params.size,
    roleId: route.params.roleId,
    userName: params.query?.userName,
    phonenumber: params.query?.phonenumber,
  };
  const response = await allocatedUserList(query);
  return { data: response.rows || [], total: response.total || 0 };
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  updateState('pager.page', 1);
  handleRefresh();
}

function onSearch({ handleRefresh, updateState }) {
  updateState('pager.page', 1);
  handleRefresh();
}

function handleSelectionChange(selection) {
  userIds.value = selection.map((item) => item.userId);
  multiple.value = !selection.length;
}

function openSelectUser() {
  proxy.$refs['selectRef'].show();
}

function handleClose() {
  const obj = { path: '/system/role' };
  proxy.$tab.closeOpenPage(obj);
}

function cancelAuthUser(row) {
  proxy.$modal
    .confirm('确认要取消该用户"' + row.userName + '"角色吗？')
    .then(function () {
      return authUserCancel({ userId: row.userId, roleId: route.params.roleId });
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('取消授权成功');
    })
    .catch(() => {});
}

function cancelAuthUserAll() {
  const roleId = route.params.roleId;
  const uIds = userIds.value.join(',');
  proxy.$modal
    .confirm('是否取消选中用户授权数据项?')
    .then(function () {
      return authUserCancelAll({ roleId: roleId, userIds: uIds });
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('取消授权成功');
    })
    .catch(() => {});
}
</script>
