<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :title="isEdit ? '修改角色' : '添加角色'"
    placement="right"
    :loading="drawerLoading"
    :ok-disabled="drawerLoading || menuLoadFailed || drawer.state.disabled"
  >
    <el-form
      ref="formRef"
      :model="drawer.state.data"
      :rules="formRules"
      label-position="top"
      class="role-form"
    >
      <el-form-item label="角色名称" prop="roleName">
        <zx-input v-model="drawer.state.data.roleName" placeholder="请输入角色名称" />
      </el-form-item>
      <el-form-item prop="roleKey">
        <template #label>
          <span class="flex items-center gap-1">
            <el-tooltip
              content="控制器中定义的权限字符，如：@PreAuthorize(`@ss.hasRole('admin')`)"
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            权限字符
          </span>
        </template>
        <zx-input v-model="drawer.state.data.roleKey" placeholder="请输入权限字符" />
      </el-form-item>
      <el-form-item label="角色顺序" prop="roleSort">
        <el-input-number
          v-model="drawer.state.data.roleSort"
          controls-position="right"
          :min="0"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-radio-group v-model="drawer.state.data.status">
          <el-radio v-for="dict in statusOptions" :key="dict.value" :value="dict.value">
            {{ dict.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="菜单权限">
        <div class="tree-toolbar">
          <el-checkbox v-model="menuExpand" @change="handleCheckedTreeExpand"
            >展开/折叠</el-checkbox
          >
          <el-checkbox v-model="menuNodeAll" @change="handleCheckedTreeNodeAll"
            >全选/全不选</el-checkbox
          >
          <el-checkbox v-model="drawer.state.data.menuCheckStrictly">父子联动</el-checkbox>
        </div>
        <el-tree
          class="tree-border"
          :data="menuOptions"
          show-checkbox
          ref="menuRef"
          node-key="id"
          :check-strictly="!drawer.state.data.menuCheckStrictly"
          :empty-text="menuEmptyText"
          :props="{ label: 'label', children: 'children' }"
        />
      </el-form-item>
      <el-form-item label="备注">
        <zx-input
          v-model="drawer.state.data.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入内容"
        />
      </el-form-item>
    </el-form>
  </ZxDrawer>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { useDrawer } from '@zxio/zxui';
import { addRole, getRole, updateRole } from '@/api/system/role';
import { roleMenuTreeselect, treeselect as menuTreeselect } from '@/api/system/menu';

defineProps({
  statusOptions: { type: Array, default: () => [] },
});

const emit = defineEmits(['success']);

const formRef = ref();
const menuRef = ref();
const menuOptions = ref([]);
const menuExpand = ref(false);
const menuNodeAll = ref(false);
const drawerLoading = ref(false);
const menuLoadFailed = ref(false);
const menuEmptyText = computed(() => {
  if (drawerLoading.value) return '加载中，请稍候';
  if (menuLoadFailed.value) return '菜单加载失败，请关闭后重试';
  return '暂无菜单数据';
});

const formRules = {
  roleName: [{ required: true, message: '角色名称不能为空', trigger: 'blur' }],
  roleKey: [{ required: true, message: '权限字符不能为空', trigger: 'blur' }],
  roleSort: [{ required: true, message: '角色顺序不能为空', trigger: 'blur' }],
};

const drawer = useDrawer({
  placement: 'right',
  okText: '保存',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    roleId: undefined,
    roleName: '',
    roleKey: '',
    roleSort: 0,
    status: '0',
    menuIds: [],
    menuCheckStrictly: true,
    remark: '',
  }),
  async onConfirm() {
    const submitData = {
      ...drawer.state.data,
      menuIds: getMenuAllCheckedKeys(),
    };
    if (submitData.roleId) {
      await updateRole(submitData);
    } else {
      await addRole(submitData);
    }
    emit('success');
    return true;
  },
});

const isEdit = computed(() => !!drawer.state.data.roleId);

/** 获取所有选中的菜单节点 */
function getMenuAllCheckedKeys() {
  const checkedKeys = menuRef.value?.getCheckedKeys() || [];
  const halfCheckedKeys = menuRef.value?.getHalfCheckedKeys() || [];
  return [...halfCheckedKeys, ...checkedKeys];
}

/** 树权限（展开/折叠）*/
function handleCheckedTreeExpand(value) {
  const treeList = menuOptions.value;
  for (let i = 0; i < treeList.length; i++) {
    if (menuRef.value?.store?.nodesMap[treeList[i].id]) {
      menuRef.value.store.nodesMap[treeList[i].id].expanded = value;
    }
  }
}

/** 树权限（全选/全不选） */
function handleCheckedTreeNodeAll(value) {
  menuRef.value?.setCheckedNodes(value ? menuOptions.value : []);
}

/** 重置菜单树状态 */
function resetMenuTree() {
  menuRef.value?.setCheckedKeys([]);
  menuExpand.value = false;
  menuNodeAll.value = false;
}

/** 打开抽屉 */
async function openDrawer(roleId) {
  resetMenuTree();
  menuOptions.value = [];
  menuLoadFailed.value = false;
  drawerLoading.value = true;
  drawer.open();

  try {
    if (roleId) {
      const [roleRes, menuRes] = await Promise.all([getRole(roleId), roleMenuTreeselect(roleId)]);
      // 后端返回的数据已经是正确的树形结构，直接使用
      menuOptions.value = menuRes.menus || [];
      const roleData = roleRes || {};
      drawer.state.data = {
        roleId: roleData.roleId,
        roleName: roleData.roleName,
        roleKey: roleData.roleKey,
        roleSort: Number(roleData.roleSort),
        status: roleData.status,
        menuCheckStrictly: roleData.menuCheckStrictly,
        remark: roleData.remark,
      };
      nextTick(() => {
        const checkedKeys = menuRes.checkedKeys || [];
        checkedKeys.forEach((v) => {
          nextTick(() => menuRef.value?.setChecked(v, true, false));
        });
      });
    } else {
      const menuRes = await menuTreeselect();
      menuOptions.value = menuRes.items;
    }
  } catch {
    menuLoadFailed.value = true;
  } finally {
    drawerLoading.value = false;
  }
}

defineExpose({ open: openDrawer, close: drawer.close });
</script>

<style scoped lang="less">
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
