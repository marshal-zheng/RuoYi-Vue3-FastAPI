<template>
  <div
    :class="{ 'has-logo': showLogo, 'no-logo-spacing': !showLogo }"
    class="sidebar-container"
    data-zx-surface="panel"
  >
    <Logo v-if="showLogo" :collapse="isCollapse" />
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="var(--left-menu-bg-color)"
        text-color="var(--left-menu-text-color)"
        :unique-opened="settingsStore.uniqueOpened"
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
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';

const props = defineProps({ headerVisible: { type: Boolean, default: true } });
const route = useRoute();
const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();

const sidebarRouters = computed(() => permissionStore.sidebarRouters);
const isCollapse = computed(() => !appStore.sidebar.opened);

// Brand placement follows header visibility, independently of multi-page tabs.
const showLogo = computed(
  () => settingsStore.sidebarLogo && (!props.headerVisible || isCollapse.value)
);

const activeMenu = computed(() => {
  const { meta, path } = route;
  if (meta.activeMenu) {
    return meta.activeMenu;
  }
  return path;
});
</script>

<style lang="less" scoped>
@import '@/assets/styles/mixin.less';

.sidebar-container {
  // The panel surface paints background, border and depth. The menu sits
  // transparently on top of it, so only the interaction states are defined
  // here — rebound at this boundary rather than on the document root.
  --left-menu-bg-color: transparent;
  --left-menu-bg-light-color: transparent;
  --left-menu-submenu-bg-color: transparent;
  --left-menu-text-color: var(--zx-semantic-surface-panel-on-text);
  --left-menu-submenu-text-color: var(--zx-semantic-surface-panel-on-text);
  --left-menu-text-active-color: var(--zx-semantic-surface-selected-on-text);
  --left-menu-active-indicator-color: var(--zx-semantic-accent-base);
  --left-menu-hover-bg-color: @on-surface-tint;
  --left-menu-submenu-hover-bg-color: @on-surface-tint;
  --left-menu-bg-active-color: var(--zx-semantic-surface-selected-fill);
  --left-menu-collapse-bg-active-color: var(--zx-semantic-surface-selected-fill);
  --left-menu-border-color: var(--zx-semantic-border-subtle);
  --left-menu-indent-color: var(--zx-semantic-border-subtle);
  --left-menu-active-shadow:
    var(--zx-semantic-surface-selected-depth), var(--zx-semantic-surface-selected-inner);
  --left-menu-box-shadow:
    var(--zx-semantic-surface-panel-depth), var(--zx-semantic-surface-panel-inner);

  transition: width var(--transition-time-02);
  box-shadow: var(--left-menu-box-shadow);
  // Like the app-shell aside, the rail only separates itself from the content,
  // so the logo strip starts flush with the top header band.
  border-width: 0 1px 0 0;

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
        color: var(--left-menu-text-color) !important;
        background-color: transparent !important;
      }
    }

    // 选中子级时，父级标题保持常规颜色（不高亮）
    .is-active {
      & > .el-sub-menu__title {
        color: var(--left-menu-text-color) !important;
        background-color: transparent !important;

        &:hover {
          color: var(--left-menu-text-color) !important;
        }
      }
    }

    // 一级菜单项
    .el-menu-item {
      position: relative;
      z-index: 0;
      background-color: transparent !important;

      &:hover {
        color: var(--left-menu-text-color) !important;
        background-color: transparent !important;

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: var(--left-menu-active-bar-width);
          background: var(--left-menu-hover-bg-color);
          border-top-right-radius: var(--left-menu-item-radius);
          border-bottom-right-radius: var(--left-menu-item-radius);
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
        transition:
          background 0.25s ease,
          box-shadow 0.25s ease;
      }

      // 左侧高亮竖条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-active-indicator-color);
      }

      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: transparent !important;

        &::after {
          background: var(--left-menu-bg-active-color);
        }
      }
    }

    // 子菜单样式
    .el-menu {
      background-color: var(--left-menu-bg-color) !important;

      .el-sub-menu__title {
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
          color: var(--left-menu-text-color) !important;
        }
      }

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
            border-top-right-radius: var(--left-menu-item-radius);
            border-bottom-right-radius: var(--left-menu-item-radius);
            z-index: -1;
          }
        }
      }

      // 子菜单项的 active 状态
      .el-menu-item.is-active {
        color: var(--left-menu-text-active-color) !important;

        &::before {
          background-color: var(--left-menu-active-indicator-color);
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
          transition:
            background 0.25s ease,
            box-shadow 0.25s ease;
        }

        &:hover {
          color: var(--left-menu-text-active-color) !important;
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
      color: var(--left-menu-text-active-color) !important;
      background-color: var(--left-menu-collapse-bg-active-color) !important;

      // 折叠状态下的左侧高亮竖条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-active-indicator-color);
      }
    }
  }
}
</style>
