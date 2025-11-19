<template>
  <ZxContentWrap
    :show-footer="true"
    :footer-fixed="true"
    @save="handleSave"
    @cancel="handleCancel"
  >
    <template #title>
      <div class="flex items-center gap-6">
        <span class="text-lg font-semibold">角色授权</span>
        <span class="text-sm text-gray-500">用户昵称：{{ form.nickName }}</span>
        <span class="text-sm text-gray-500">登录账号：{{ form.userName }}</span>
      </div>
    </template>

    <ZxGridList
      ref="gridListRef"
      :load-data="loadRolesData"
      :show-pagination="true"
      :load-on-mounted="true"
      :pageViewportOffset="63"
      class="zx-grid-list--page"
    >
      <template #table="{ grid }">
        <el-table
          v-loading="grid.loading"
          :row-key="getRowKey"
          @row-click="clickRow"
          ref="roleRef"
          @selection-change="handleSelectionChange"
          :data="grid.list || []"
        >
          <el-table-column label="序号" width="55" type="index" />
          <el-table-column type="selection" :reserve-selection="true" width="55" />
          <el-table-column label="角色编号" prop="roleId" />
          <el-table-column label="角色名称" prop="roleName" />
          <el-table-column label="权限字符" prop="roleKey" />
          <el-table-column label="创建时间" prop="createTime" width="180">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>
  </ZxContentWrap>
</template>

<script setup name="AuthRole">
import { getAuthRole, updateAuthRole } from '@/api/system/user';
import { onMounted } from 'vue';
import { parseTime } from '@/utils/ruoyi';

const route = useRoute();
const { proxy } = getCurrentInstance();

const roleIds = ref([]);
const form = ref({
  nickName: undefined,
  userName: undefined,
  userId: undefined,
});
const rolesAll = ref([]);
const gridListRef = ref(null);
const roleRef = ref(null);
// 标记是否已加载角色数据，避免列表先于数据加载触发导致空列表
const rolesLoaded = ref(false);

/** 单击选中行数据 */
function clickRow(row) {
  // 优先使用模板 ref
  roleRef.value?.toggleRowSelection(row);
}
/** 多选框选中数据 */
function handleSelectionChange(selection) {
  roleIds.value = selection.map((item) => item.roleId);
}
/** 保存选中的数据编号 */
function getRowKey(row) {
  return row.roleId;
}
/** 关闭按钮 */
function close() {
  const obj = { path: '/system/user' };
  proxy.$tab.closeOpenPage(obj);
}
/** 提交按钮 */
function submitForm() {
  const userId = form.value.userId;
  const rIds = roleIds.value.join(',');
  updateAuthRole({ userId: userId, roleIds: rIds }).then((response) => {
    proxy.$modal.msgSuccess('授权成功');
    close();
  });
}

function handleSave() {
  submitForm();
}

function handleCancel() {
  close();
}

async function loadRolesData(params) {
  // 若首次进入时数据尚未拉取，这里兜底请求一次
  if (!rolesLoaded.value) {
    const userId = route.params && route.params.userId;
    if (userId) {
      try {
        const resp = await getAuthRole(userId);
        form.value = resp.user || {};
        rolesAll.value = resp.roles || [];
      } catch (e) {
        console.error('获取角色数据失败:', e);
      } finally {
        rolesLoaded.value = true;
      }
    }
  }

  const page = Number(params?.page ?? 1);
  const size = Number(params?.size ?? 10);
  const start = (page - 1) * size;
  const end = start + size;
  const pageList = rolesAll.value.slice(start, end);

  await nextTick();
  pageList.forEach((row) => {
    if (row.flag) {
      roleRef.value?.toggleRowSelection(row, true);
    }
  });

  return { list: pageList, total: rolesAll.value.length };
}

onMounted(async () => {
  const userId = route.params && route.params.userId;
  if (userId) {
    try {
      const response = await getAuthRole(userId);
      form.value = response.user || {};
      rolesAll.value = response.roles || [];
      rolesLoaded.value = true;
      // 数据加载完成后，让 gridList 刷新显示数据
      nextTick(() => {
        gridListRef.value?.refresh();
      });
    } catch (e) {
      console.error('获取角色数据失败:', e);
    }
  }
});
</script>
