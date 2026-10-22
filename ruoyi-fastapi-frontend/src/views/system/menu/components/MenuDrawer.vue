<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :loading="detailLoading"
    :ok-disabled="detailLoading || !!loadError || drawer.state.disabled"
  >
    <DictStatus :types="['sys_show_hide', 'sys_normal_disable']" />
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="formRef"
      :model="drawer.state.data"
      :rules="formRules"
      label-position="top"
    >
      <el-form-item label="上级菜单">
        <el-tree-select
          v-model="drawer.state.data.parentId"
          :data="menuOptions"
          :props="{ value: 'id', label: 'label', children: 'children' }"
          value-key="id"
          placeholder="选择上级菜单"
          check-strictly
          :teleported="false"
        />
      </el-form-item>

      <el-form-item label="菜单类型" prop="menuType">
        <el-radio-group v-model="drawer.state.data.menuType">
          <el-radio value="M">目录</el-radio>
          <el-radio value="C">菜单</el-radio>
          <el-radio value="F">按钮</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'F'" label="菜单图标" prop="icon">
        <el-popover
          placement="bottom-start"
          :width="540"
          :teleported="false"
          trigger="click"
          @show="onIconPopoverShow"
        >
          <template #reference>
            <zx-input v-model="drawer.state.data.icon" placeholder="点击选择图标" readonly>
              <template #prepend>
                <ZxIcon
                  :icon="resolveNavigationIcon(drawer.state.data.icon) || navigationIcons.search"
                />
              </template>
            </zx-input>
          </template>
          <IconSelect
            ref="iconSelectRef"
            :active-icon="drawer.state.data.icon"
            @selected="onIconSelected"
          />
        </el-popover>
      </el-form-item>

      <el-form-item label="菜单名称" prop="menuName">
        <zx-input v-model="drawer.state.data.menuName" placeholder="请输入菜单名称" />
      </el-form-item>

      <el-form-item label="显示排序" prop="orderNum">
        <el-input-number
          v-model="drawer.state.data.orderNum"
          controls-position="right"
          :min="0"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'F'" prop="isFrame">
        <template #label>
          <span>
            <el-tooltip content="选择是外链则路由地址需要以`http(s)://`开头" placement="top">
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            是否外链
          </span>
        </template>
        <el-radio-group v-model="drawer.state.data.isFrame">
          <el-radio value="0">是</el-radio>
          <el-radio value="1">否</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'F'" prop="path">
        <template #label>
          <span>
            <el-tooltip
              content="访问的路由地址，如：`user`，如外网地址需内链访问则以`http(s)://`开头"
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            路由地址
          </span>
        </template>
        <zx-input v-model="drawer.state.data.path" placeholder="请输入路由地址" />
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType === 'C'" prop="component">
        <template #label>
          <span>
            <el-tooltip
              content="访问的组件路径，如：`system/user/index`，默认在`views`目录下"
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            组件路径
          </span>
        </template>
        <zx-input v-model="drawer.state.data.component" placeholder="请输入组件路径" />
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'M'" prop="perms">
        <template #label>
          <span>
            <el-tooltip
              content="控制器中定义的权限字符，如：@PreAuthorize(`@ss.hasPermi('system:user:list')`)"
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            权限字符
          </span>
        </template>
        <zx-input v-model="drawer.state.data.perms" placeholder="请输入权限标识" maxlength="100" />
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType === 'C'" prop="query">
        <template #label>
          <span>
            <el-tooltip
              content='访问路由的默认传递参数，如：`{"id": 1, "name": "ry"}`'
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            路由参数
          </span>
        </template>
        <zx-input v-model="drawer.state.data.query" placeholder="请输入路由参数" maxlength="255" />
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType === 'C'" prop="isCache">
        <template #label>
          <span>
            <el-tooltip
              content="选择是则会被`keep-alive`缓存，需要匹配组件的`name`和地址保持一致"
              placement="top"
            >
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            是否缓存
          </span>
        </template>
        <el-radio-group v-model="drawer.state.data.isCache">
          <el-radio value="0">缓存</el-radio>
          <el-radio value="1">不缓存</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'F'" prop="visible">
        <template #label>
          <span>
            <el-tooltip content="选择隐藏则路由将不会出现在侧边栏，但仍然可以访问" placement="top">
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            显示状态
          </span>
        </template>
        <el-radio-group v-model="drawer.state.data.visible">
          <el-radio v-for="dict in sysShowHide" :key="dict.value" :value="dict.value">
            {{ dict.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="drawer.state.data.menuType !== 'F'" prop="status">
        <template #label>
          <span>
            <el-tooltip content="选择停用则路由将不会出现在侧边栏，也不能被访问" placement="top">
              <el-icon><question-filled /></el-icon>
            </el-tooltip>
            菜单状态
          </span>
        </template>
        <el-radio-group v-model="drawer.state.data.status">
          <el-radio v-for="dict in sysNormalDisable" :key="dict.value" :value="dict.value">
            {{ dict.label }}
          </el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </ZxDrawer>
</template>

<script setup lang="ts" name="MenuDrawer">
import { ref } from 'vue';
import { useEditorRead } from '@/utils/editor-read';
import { useDict } from '@/utils/dict';
import { getMenu, addMenu, updateMenu, treeselect, type MenuTreeNode } from '@/api/system/menu';
import { useDrawer } from '@zxio/zxui/hooks';
import { QuestionFilled } from '@element-plus/icons-vue';
import { ZxIcon } from '@zxio/zxui/core';
import { navigationIcons, resolveNavigationIcon } from '@/icons/navigation';
import IconSelect from '@/components/ui/IconSelect/index.vue';

const { sys_show_hide: sysShowHide, sys_normal_disable: sysNormalDisable } = useDict(
  'sys_show_hide',
  'sys_normal_disable'
);

interface MenuForm {
  menuId?: number;
  parentId?: number;
  menuName?: string;
  menuType?: 'M' | 'C' | 'F';
  icon?: string;
  orderNum?: number;
  isFrame?: '0' | '1' | 0 | 1;
  isCache?: '0' | '1' | 0 | 1;
  visible?: '0' | '1';
  status?: '0' | '1';
  path?: string;
  component?: string;
  perms?: string;
  query?: string;
}

const emit = defineEmits(['success']);

const menuOptions = ref<MenuTreeNode[]>([]);
const formRef = ref();
const detailLoading = ref(false);
let requested: { menuId?: number; parentId?: number } = {};
const iconSelectRef = ref();

const formRules = {
  menuName: [{ required: true, message: '菜单名称不能为空', trigger: 'blur' }],
  orderNum: [{ required: true, message: '菜单顺序不能为空', trigger: 'blur' }],
  path: [{ required: true, message: '路由地址不能为空', trigger: 'blur' }],
};

const drawer = useDrawer<MenuForm>({
  divider: true,
  title: (data: MenuForm) => (data?.menuId ? '修改菜单' : '添加菜单'),
  size: '600px',
  formRef,
  defaultData: () => ({
    menuId: undefined,
    parentId: 0,
    menuName: undefined,
    menuType: 'M',
    icon: undefined,
    orderNum: 0,
    isFrame: '1',
    isCache: '0',
    visible: '0',
    status: '0',
    path: undefined,
    component: undefined,
    perms: undefined,
    query: undefined,
  }),
  onConfirm: async (data: MenuForm) => {
    if (detailLoading.value || loadError.value || data.menuId !== requested.menuId) return false;
    if (data.menuId !== undefined) {
      await updateMenu(data);
    } else {
      await addMenu(data);
    }
    emit('success');
    return true;
  },
});

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => drawer.state.visible, detailLoading);

/** 只接收编辑身份或新增父级，不用列表快照回填详情。 */
function openDrawer(data?: { menuId?: number; parentId?: number }) {
  requested = { menuId: data?.menuId, parentId: data?.parentId ?? 0 };
  const target = requested;
  return runRead(async (read) => {
    drawer.open(target);
    drawer.setDisabled(true);
    menuOptions.value = [];
    const config = { signal: read.signal, silentError: true };
    const [tree, detail] = await Promise.all([
      treeselect(config),
      target.menuId ? getMenu(target.menuId, config) : undefined,
    ]);
    if (!read.isCurrent()) return;
    menuOptions.value = [{ id: 0, label: '主类目', children: tree.items }];
    if (detail) {
      drawer.open({
        menuId: detail.menuId,
        parentId: detail.parentId ?? 0,
        menuName: detail.menuName ?? undefined,
        menuType: detail.menuType ?? undefined,
        icon: detail.icon ?? undefined,
        orderNum: detail.orderNum ?? 0,
        isFrame: detail.isFrame ?? '1',
        isCache: detail.isCache ?? '0',
        visible: detail.visible ?? '0',
        status: detail.status ?? '0',
        path: detail.path ?? undefined,
        component: detail.component ?? undefined,
        perms: detail.perms ?? undefined,
        query: detail.query ?? undefined,
      });
    }
    drawer.setDisabled(false);
  });
}
function closeDrawer() {
  cancelRead();
  return drawer.close();
}
function handleRetry() {
  return openDrawer(requested).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

/** 图标弹窗显示时重置搜索 */
function onIconPopoverShow() {
  iconSelectRef.value?.reset();
}

/** 选择图标 */
function onIconSelected(name: string) {
  drawer.state.data.icon = name;
}

defineExpose({ open: openDrawer, close: closeDrawer });
</script>
