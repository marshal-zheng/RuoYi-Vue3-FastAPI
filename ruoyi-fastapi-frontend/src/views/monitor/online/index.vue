<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadOnlineData"
      :show-pagination="true"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.ipaddr"
              placeholder="请输入登录地址"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-input
              v-model="query.userName"
              placeholder="请输入用户名称"
              clearable
              style="width: 200px"
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
        <el-table v-loading="grid.loading" :data="grid.list || []" style="width: 100%">
          <el-table-column label="序号" width="50" type="index" align="center" />
          <el-table-column
            label="会话编号"
            align="center"
            prop="tokenId"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="登录名称"
            align="center"
            prop="userName"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="所属部门"
            align="center"
            prop="deptName"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="主机"
            align="center"
            prop="ipaddr"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="登录地点"
            align="center"
            prop="loginLocation"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="操作系统"
            align="center"
            prop="os"
            :show-overflow-tooltip="true"
          />
          <el-table-column
            label="浏览器"
            align="center"
            prop="browser"
            :show-overflow-tooltip="true"
          />
          <el-table-column label="登录时间" align="center" prop="loginTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.loginTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
            <template #default="scope">
              <el-button
                link
                type="primary"
                icon="Delete"
                @click="handleForceLogout(scope.row)"
                v-hasPermi="['monitor:online:forceLogout']"
                >强退</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>
</template>

<script setup name="Online">
import { forceLogout, list as initData } from '@/api/monitor/online';

const { proxy } = getCurrentInstance();

const gridListRef = ref(null);

async function loadOnlineData(params) {
  const query = {
    pageNum: params.page,
    pageSize: params.size,
    ipaddr: params.query?.ipaddr,
    userName: params.query?.userName,
  };
  const response = await initData(query);
  return { data: response.rows || [], total: response.total || 0 };
}
function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}
function onSearch({ handleRefresh }) {
  handleRefresh();
}
/** 强退按钮操作 */
function handleForceLogout(row) {
  proxy.$modal
    .confirm('是否确认强退名称为"' + row.userName + '"的用户?')
    .then(function () {
      return forceLogout(row.tokenId);
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}
</script>
