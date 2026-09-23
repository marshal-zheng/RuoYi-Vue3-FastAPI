<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    title="分配数据权限"
    placement="right"
    :loading="drawerLoading"
  >
    <el-form :model="drawer.state.data" label-position="top" class="role-form">
      <el-form-item label="角色名称">
        <zx-input v-model="drawer.state.data.roleName" disabled />
      </el-form-item>
      <el-form-item label="权限字符">
        <zx-input v-model="drawer.state.data.roleKey" disabled />
      </el-form-item>
      <el-form-item label="权限范围">
        <el-select
          v-model="drawer.state.data.dataScope"
          style="width: 100%"
          @change="dataScopeSelectChange"
        >
          <el-option
            v-for="item in dataScopeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="数据权限" v-show="drawer.state.data.dataScope === '2'">
        <div class="tree-toolbar">
          <el-checkbox v-model="deptExpand" @change="handleCheckedTreeExpand"
            >展开/折叠</el-checkbox
          >
          <el-checkbox v-model="deptNodeAll" @change="handleCheckedTreeNodeAll"
            >全选/全不选</el-checkbox
          >
          <el-checkbox v-model="drawer.state.data.deptCheckStrictly">父子联动</el-checkbox>
        </div>
        <el-tree
          class="tree-border"
          :data="deptOptions"
          show-checkbox
          default-expand-all
          ref="deptRef"
          node-key="id"
          :check-strictly="!drawer.state.data.deptCheckStrictly"
          empty-text="加载中，请稍候"
          :props="{ label: 'label', children: 'children' }"
        />
      </el-form-item>
    </el-form>
  </ZxDrawer>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useDrawer } from '@zxio/zxui';
import { getRole, dataScope, deptTreeSelect } from '@/api/system/role';

const emit = defineEmits(['success']);

const deptRef = ref();
const deptOptions = ref([]);
const deptExpand = ref(true);
const deptNodeAll = ref(false);
const drawerLoading = ref(false);

/** 数据范围选项 */
const dataScopeOptions = [
  { value: '1', label: '全部数据权限' },
  { value: '2', label: '自定数据权限' },
  { value: '3', label: '本部门数据权限' },
  { value: '4', label: '本部门及以下数据权限' },
  { value: '5', label: '仅本人数据权限' },
];

const drawer = useDrawer({
  placement: 'right',
  okText: '确定',
  defaultData: () => ({
    roleId: undefined,
    roleName: '',
    roleKey: '',
    dataScope: '1',
    deptCheckStrictly: true,
    deptIds: [],
  }),
  async onConfirm() {
    const submitData = { ...drawer.state.data, deptIds: getDeptAllCheckedKeys() };
    await dataScope(submitData);
    emit('success');
    return true;
  },
});

/** 获取所有选中的部门节点 */
function getDeptAllCheckedKeys() {
  const checkedKeys = deptRef.value?.getCheckedKeys() || [];
  const halfCheckedKeys = deptRef.value?.getHalfCheckedKeys() || [];
  return [...halfCheckedKeys, ...checkedKeys];
}

/** 选择角色权限范围触发 */
function dataScopeSelectChange(value) {
  if (value !== '2') {
    deptRef.value?.setCheckedKeys([]);
  }
}

/** 树权限（展开/折叠）*/
function handleCheckedTreeExpand(value) {
  const treeList = deptOptions.value;
  for (let i = 0; i < treeList.length; i++) {
    if (deptRef.value?.store?.nodesMap[treeList[i].id]) {
      deptRef.value.store.nodesMap[treeList[i].id].expanded = value;
    }
  }
}

/** 树权限（全选/全不选） */
function handleCheckedTreeNodeAll(value) {
  deptRef.value?.setCheckedNodes(value ? deptOptions.value : []);
}

/** 重置部门树状态 */
function resetDeptTree() {
  deptRef.value?.setCheckedKeys([]);
  deptExpand.value = true;
  deptNodeAll.value = false;
}

/** 打开抽屉 */
async function openDrawer(roleId) {
  resetDeptTree();
  drawer.open();
  drawerLoading.value = true;

  try {
    const [roleRes, deptRes] = await Promise.all([getRole(roleId), deptTreeSelect(roleId)]);

    deptOptions.value = deptRes.depts || [];
    const roleData = roleRes || {};

    drawer.state.data = {
      roleId: roleData.roleId,
      roleName: roleData.roleName,
      roleKey: roleData.roleKey,
      dataScope: roleData.dataScope || '1',
      deptCheckStrictly: roleData.deptCheckStrictly,
    };

    nextTick(() => {
      nextTick(() => {
        deptRef.value?.setCheckedKeys(deptRes.checkedKeys || []);
      });
    });
  } finally {
    drawerLoading.value = false;
  }
}

defineExpose({ open: openDrawer, close: drawer.close });
</script>

<style scoped lang="less">
.role-form {
  padding: 0 4px;
}

.tree-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.tree-border {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 8px;
  max-height: 280px;
  overflow-y: auto;
  width: 100%;
}
</style>
