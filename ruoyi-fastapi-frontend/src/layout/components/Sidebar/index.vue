<template>
  <div :class="{ 'has-logo': showLogo }" class="sidebar-container">
    <logo v-if="showLogo" :collapse="isCollapse" />
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="var(--left-menu-bg-color)"
        text-color="var(--left-menu-text-color)"
        :unique-opened="true"
        active-text-color="var(--left-menu-text-active-color)"
        :collapse-transition="false"
        mode="vertical"
        class="sidebar-menu"
      >
        <sidebar-item
          v-for="(route, index) in sidebarRouters"
          :key="route.path + index"
          :item="route"
          :base-path="route.path"
        />
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup>
import Logo from './Logo';
import SidebarItem from './SidebarItem';
import variables from '@/assets/styles/variables.module.less';
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';

const route = useRoute();
const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();

const sidebarRouters = computed(() => permissionStore.sidebarRouters);
const showLogo = computed(() => settingsStore.sidebarLogo);
const sideTheme = computed(() => settingsStore.sideTheme);
const theme = computed(() => settingsStore.theme);
const isCollapse = computed(() => !appStore.sidebar.opened);

// 获取菜单背景色
const getMenuBackground = computed(() => {
  if (settingsStore.isDark) {
    return 'var(--sidebar-bg)';
  }
  return sideTheme.value === 'theme-dark' ? variables.menuBg : variables.menuLightBg;
});

// 获取菜单文字颜色
const getMenuTextColor = computed(() => {
  if (settingsStore.isDark) {
    return 'var(--sidebar-text)';
  }
  return sideTheme.value === 'theme-dark' ? variables.menuText : variables.menuLightText;
});

const activeMenu = computed(() => {
  const { meta, path } = route;
  if (meta.activeMenu) {
    return meta.activeMenu;
  }
  return path;
});
</script>

<style lang="less" scoped>
.sidebar-container {
  background-color: var(--left-menu-bg-color);
  transition: width var(--transition-time-02);
  box-shadow: var(--left-menu-box-shadow);

  .scrollbar-wrapper {
    background-color: var(--left-menu-bg-color);
  }

  :deep(.sidebar-menu) {
    border: none;
    height: 100%;
    width: 100% !important;
    background-color: var(--left-menu-bg-color);

    // 父级菜单标题的hover效果
    .el-sub-menu__title {
      position: relative;
      background-color: transparent !important;

      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: transparent !important;

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: var(--left-menu-active-bar-width);
          background: var(--left-menu-hover-bg-color);
          border-top-right-radius: 8px;
          border-bottom-right-radius: 8px;
          z-index: -1;
        }
      }
    }

    // 选中子级时，父级标题保持常规颜色（不高亮）
    .is-active {
      & > .el-sub-menu__title {
        color: var(--left-menu-text-color) !important;
        background-color: transparent !important;

        &:hover {
          color: var(--left-menu-text-active-color) !important;
        }
      }
    }

    // 一级菜单项
    .el-menu-item {
      position: relative;
      z-index: 0;
      background-color: transparent !important;

      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: transparent !important;

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: var(--left-menu-active-bar-width);
          background: var(--left-menu-hover-bg-color);
          border-top-right-radius: 8px;
          border-bottom-right-radius: 8px;
          z-index: -1;
        }
      }
    }

    // 选中状态的菜单项
    .el-menu-item.is-active {
      color: var(--left-menu-text-active-color) !important;
      position: relative;
      background-color: transparent !important;

      &::after {
        content: '';
        position: absolute;
        inset: 0;
        left: var(--left-menu-active-bar-width);
        background: var(--left-menu-bg-active-color);
        border-top-right-radius: var(--left-menu-item-radius);
        border-bottom-right-radius: var(--left-menu-item-radius);
        z-index: -1;
        box-shadow: var(--left-menu-active-shadow);
        transition: background 0.25s ease, box-shadow 0.25s ease;
      }

      // 左侧高亮竖条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-text-active-color);
      }

      &:hover {
        background-color: transparent !important;

        &::after {
          background: var(--left-menu-bg-active-color);
        }
      }
    }

    // 子菜单样式
    .el-menu {
      background-color: var(--left-menu-bg-color) !important;

      .el-sub-menu__title,
      .el-menu-item {
        position: relative;
        z-index: 0;
        background-color: transparent !important;

        // 左侧缩进指示线
        &::before {
          content: '';
          position: absolute;
          left: 16px;
          top: 0;
          bottom: 0;
          width: 2px;
          background-color: var(--left-menu-indent-color);
          z-index: 1;
        }

        &:hover {
          background-color: transparent !important;

          &::after {
            content: '';
            position: absolute;
            inset: 0;
            left: calc(16px + 2px);
            background: var(--left-menu-hover-bg-color);
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            z-index: -1;
          }
        }
      }

      // 子菜单项的 active 状态
      .el-menu-item.is-active {
        color: var(--left-menu-text-active-color) !important;

        &::before {
          background-color: var(--left-menu-text-active-color);
          width: 3px;
        }

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: calc(16px + 3px);
          background: var(--left-menu-bg-active-color);
          border-top-right-radius: var(--left-menu-item-radius);
          border-bottom-right-radius: var(--left-menu-item-radius);
          z-index: -1;
          box-shadow: var(--left-menu-active-shadow);
          transition: background 0.25s ease, box-shadow 0.25s ease;
        }

        &:hover {
          background-color: transparent !important;
        }
      }
    }
  }

  // 折叠状态
  :deep(.el-menu--collapse) {
    width: var(--left-menu-min-width);

    & > .is-active,
    & > .is-active > .el-sub-menu__title {
      position: relative;
      background-color: var(--left-menu-collapse-bg-active-color) !important;

      // 折叠状态下的左侧高亮竖条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-text-active-color);
      }
    }
  }
}
</style>
