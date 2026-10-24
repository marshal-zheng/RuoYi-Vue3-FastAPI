<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :title="isEdit ? '修改角色' : '添加角色'"
    placement="right"
    :loading="drawerLoading"
    :ok-disabled="drawerLoading || !!loadError || drawer.state.disabled"
  >
    <span v-if="editorQuery.isPaused.value || menuQuery.isPaused.value" aria-live="polite">
      角色权限读取等待网络连接
    </span>
    <el-alert
      v-else-if="!loadError && (editorQuery.error.value || menuQuery.error.value)"
      title="角色权限刷新失败，保留编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryResources">重试读取</el-button>
    </el-alert>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
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
          <span class="inline-flex items-center gap-1">
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
        <DictStatus :types="['sys_normal_disable']" />
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
import { ref, computed, nextTick, shallowRef, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { useEditorRead } from '@/utils/editor-read';
import { useDict } from '@/utils/dict';
import { useDrawer } from '@zxio/zxui/hooks';
import {
  captureRoleCommand,
  roleCommands,
  roleDetailOptions,
  roleMenuOptions,
  readRoleEditor,
} from '@/queries/system/role';
import { queryScope, requireQueryScope } from '@/queries/context';

const { sys_normal_disable: statusOptions } = useDict('sys_normal_disable');

const emit = defineEmits(['success']);

const formRef = ref();
const menuRef = ref();
const menuOptions = ref([]);
const menuExpand = ref(false);
const menuNodeAll = ref(false);
const requestedId = ref();
const editorScope = shallowRef(null);

const menuEmptyText = computed(() => {
  if (drawerLoading.value) return '加载中，请稍候';
  if (loadError.value) return '菜单加载失败，请关闭后重试';
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
    const scope = editorScope.value;
    const data = drawer.state.data;
    if (
      !drawer.state.visible ||
      !scope ||
      scope !== queryScope.value ||
      drawerLoading.value ||
      loadError.value
    )
      return false;
    const submitData = {
      roleName: drawer.state.data.roleName,
      roleKey: drawer.state.data.roleKey,
      roleSort: drawer.state.data.roleSort,
      status: drawer.state.data.status,
      menuCheckStrictly: drawer.state.data.menuCheckStrictly,
      remark: drawer.state.data.remark,
      menuIds: getMenuAllCheckedKeys(),
    };
    if (drawer.state.data.roleId) {
      await roleCommands.updateRole(
        captureRoleCommand({ ...submitData, roleId: data.roleId }, scope)
      );
    } else {
      await roleCommands.createRole(captureRoleCommand(submitData, scope));
    }
    if (scope !== queryScope.value || drawer.state.data !== data || !drawer.state.visible)
      return false;
    emit('success');
    return true;
  },
});

const isEdit = computed(() => !!drawer.state.data.roleId);

const {
  loading: drawerLoading,
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => drawer.state.visible);
const activeScope = computed(() =>
  drawer.state.visible && editorScope.value === queryScope.value ? editorScope.value : null
);
const editorQuery = useQuery(() => roleDetailOptions(activeScope.value, requestedId.value));
const menuQuery = useQuery(() => roleMenuOptions(activeScope.value, requestedId.value));
watch(
  queryScope,
  () => {
    cancelRead();
    editorScope.value = null;
    drawer.state.visible = false;
  },
  { flush: 'sync' }
);

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
function openDrawer(roleId) {
  const scope = requireQueryScope();
  editorScope.value = scope;
  requestedId.value = roleId;
  return runRead(async (read) => {
    drawer.open(roleId ? { roleId } : undefined);
    drawer.setDisabled(true);
    resetMenuTree();
    menuOptions.value = [];
    let response;
    try {
      response = await readRoleEditor(scope, roleId, read.signal);
    } catch (error) {
      if (!read.isCurrent()) return;
      throw error;
    }
    if (!read.isCurrent() || scope !== queryScope.value) return;
    const { data: roleData, menus: menuRes } = response;
    if (roleId) {
      menuOptions.value = menuRes.menus || [];
      drawer.open({
        roleId: roleData.roleId,
        roleName: roleData.roleName,
        roleKey: roleData.roleKey,
        roleSort: Number(roleData.roleSort),
        status: roleData.status,
        menuCheckStrictly: roleData.menuCheckStrictly,
        remark: roleData.remark,
      });
      drawer.setDisabled(true);
      await nextTick();
      await nextTick();
      if (!read.isCurrent()) return;
      (menuRes.checkedKeys || []).forEach((id) => menuRef.value?.setChecked(id, true, false));
    } else {
      menuOptions.value = menuRes.menus;
    }
    drawer.setDisabled(false);
  });
}
function closeDrawer() {
  cancelRead();
  return drawer.close();
}
function handleRetry() {
  return openDrawer(requestedId.value).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

function retryResources() {
  if (editorQuery.isEnabled.value) void editorQuery.refetch({ cancelRefetch: false });
  if (menuQuery.isEnabled.value) void menuQuery.refetch({ cancelRefetch: false });
}

defineExpose({ open: openDrawer, close: closeDrawer });
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
