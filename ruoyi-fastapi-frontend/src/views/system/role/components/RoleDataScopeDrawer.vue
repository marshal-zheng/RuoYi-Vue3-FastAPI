<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    title="分配数据权限"
    placement="right"
    :loading="drawerLoading"
    :ok-disabled="drawerLoading || !!loadError || drawer.state.disabled"
  >
    <span v-if="editorQuery.isPaused.value || deptQuery.isPaused.value" aria-live="polite">
      数据权限读取等待网络连接
    </span>
    <el-alert
      v-else-if="!loadError && (editorQuery.error.value || deptQuery.error.value)"
      title="数据权限刷新失败，保留编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryResources">重试读取</el-button>
    </el-alert>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form v-show="!loadError" :model="drawer.state.data" label-position="top" class="role-form">
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
import { ref, computed, nextTick, shallowRef, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { useEditorRead } from '@/utils/editor-read';
import { useDrawer } from '@zxio/zxui/hooks';
import {
  captureRoleCommand,
  roleCommands,
  roleDetailOptions,
  roleDeptOptions,
  readRoleDataScopeEditor,
} from '@/queries/system/role';
import { queryScope, requireQueryScope } from '@/queries/context';

const emit = defineEmits(['success']);

const deptRef = ref();
const deptOptions = ref([]);
const deptExpand = ref(true);
const deptNodeAll = ref(false);
const requestedId = ref();
const editorScope = shallowRef(null);

/** 数据范围选项 */
const dataScopeOptions = [
  { value: '1', label: '全部数据权限' },
  { value: '2', label: '自定数据权限' },
  { value: '3', label: '本部门数据权限' },
  { value: '4', label: '本部门及以下数据权限' },
  { value: '5', label: '仅本人数据权限' },
];

const drawer = useDrawer({
  divider: true,
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
      roleId: drawer.state.data.roleId,
      dataScope: drawer.state.data.dataScope,
      deptCheckStrictly: drawer.state.data.deptCheckStrictly,
      deptIds: deptRef.value?.getCheckedKeys() || [],
    };
    await roleCommands.updateDataScope(captureRoleCommand(submitData, scope));
    if (scope !== queryScope.value || drawer.state.data !== data || !drawer.state.visible)
      return false;
    emit('success');
    return true;
  },
});

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
const deptQuery = useQuery(() => roleDeptOptions(activeScope.value, requestedId.value));
watch(
  queryScope,
  () => {
    cancelRead();
    editorScope.value = null;
    drawer.state.visible = false;
  },
  { flush: 'sync' }
);

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
function openDrawer(roleId) {
  const scope = requireQueryScope();
  editorScope.value = scope;
  requestedId.value = roleId;
  return runRead(async (read) => {
    drawer.open({ roleId });
    drawer.setDisabled(true);
    resetDeptTree();
    deptOptions.value = [];
    let response;
    try {
      response = await readRoleDataScopeEditor(scope, roleId, read.signal);
    } catch (error) {
      if (!read.isCurrent()) return;
      throw error;
    }
    if (!read.isCurrent() || scope !== queryScope.value) return;
    const { data: roleData, depts: deptRes } = response;
    deptOptions.value = deptRes.depts || [];
    drawer.open({
      roleId: roleData.roleId,
      roleName: roleData.roleName,
      roleKey: roleData.roleKey,
      dataScope: roleData.dataScope || '1',
      deptCheckStrictly: roleData.deptCheckStrictly,
    });
    drawer.setDisabled(true);
    await nextTick();
    await nextTick();
    if (!read.isCurrent()) return;
    deptRef.value?.setCheckedKeys(deptRes.checkedKeys || []);
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
  if (deptQuery.isEnabled.value) void deptQuery.refetch({ cancelRefetch: false });
}

defineExpose({ open: openDrawer, close: closeDrawer });
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
