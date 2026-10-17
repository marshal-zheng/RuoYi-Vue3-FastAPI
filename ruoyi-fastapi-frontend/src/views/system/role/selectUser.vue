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
    <el-row>
      <el-table
        @row-click="clickRow"
        ref="refTable"
        :data="userList"
        @selection-change="handleSelectionChange"
        height="260px"
      >
        <el-table-column type="selection" width="55"></el-table-column>
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
      <pagination
        v-show="total > 0"
        :total="total"
        v-model:page="queryParams.page"
        v-model:limit="queryParams.pageSize"
        @pagination="getList"
      />
    </el-row>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="handleSelectUser" :loading="handleSelectUserPending"
          >确 定</el-button
        >
        <el-button @click="visible = false">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup name="SelectUser">
import { useOperation } from '@/utils/operation';
import { ElMessage } from 'element-plus';
import { unallocatedUserList } from '@/api/system/role';
import { captureUserCommand, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { watch } from 'vue';

const props = defineProps({
  roleId: {
    type: [Number, String],
  },
});

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const userList = ref([]);
const visible = ref(false);
const total = ref(0);
const userIds = ref([]);
let openingScope;
watch(
  queryScope,
  () => {
    visible.value = false;
  },
  { flush: 'sync' }
);

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  roleId: undefined,
  userName: undefined,
  phonenumber: undefined,
});

// 显示弹框
function show() {
  openingScope = requireQueryScope();
  queryParams.roleId = props.roleId;
  getList();
  visible.value = true;
}
/**选择行 */
function clickRow(row) {
  proxy.$refs['refTable'].toggleRowSelection(row);
}
// 多选框选中数据
function handleSelectionChange(selection) {
  userIds.value = selection.map((item) => item.userId);
}
// 查询表数据
function getList() {
  const scope = openingScope;
  unallocatedUserList({ ...queryParams }).then((res) => {
    if (!visible.value || scope !== queryScope.value || scope !== openingScope) return;
    userList.value = res.items;
    total.value = res.total;
  });
}
/** 搜索按钮操作 */
function handleQuery() {
  queryParams.page = 1;
  getList();
}
/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm('queryRef');
  handleQuery();
}
const emit = defineEmits(['ok']);
/** 选择授权用户操作 */
const { run: handleSelectUser, pending: handleSelectUserPending } = useOperation(async () => {
  if (!visible.value || openingScope !== queryScope.value) return;
  const roleId = Number(queryParams.roleId);
  const uIds = [...userIds.value];
  if (uIds.length === 0) {
    ElMessage.error('请选择要分配的用户');
    return;
  }
  const command = captureUserCommand({ roleId, userIds: uIds }, openingScope);
  await userCommands.assignRoleUsers(command).then(() => {
    if (command.scope !== queryScope.value) return;
    visible.value = false;
    emit('ok');
  });
});

defineExpose({
  show,
});
</script>
