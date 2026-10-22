<template>
  <el-menu
    :default-active="activeMenu"
    mode="horizontal"
    popper-class="app-topnav-popper"
    :ellipsis-icon="OverflowIcon"
    @select="handleSelect"
    :class="{ 'has-bottom-border': settingsStore.topNavBorder }"
  >
    <el-menu-item v-for="item in topMenus" :index="item.path" :key="item.path">
      <ZxIcon
        v-if="item.meta && item.meta.icon && item.meta.icon !== '#'"
        :icon="resolveNavigationIcon(item.meta.icon)"
        class="navigation-menu-icon"
        size="var(--app-nav-icon-size)"
        aria-hidden="true"
      />
      {{ item.meta.title }}
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { h } from 'vue';
import { constantRoutes } from '@/router';
import { isHttp } from '@/utils/validate';
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';
import { ZxIcon } from '@zxio/zxui/core';
import { navigationIcons, resolveNavigationIcon } from '@/icons/navigation';

const OverflowIcon = () =>
  h(ZxIcon, {
    icon: navigationIcons.more,
    size: 'var(--app-nav-icon-size)',
    role: 'img',
    'aria-label': '更多菜单',
  });

// 隐藏侧边栏路由
const hideList = ['/index', '/user/profile'];

const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();
const route = useRoute();
const router = useRouter();

// 主题颜色
// 所有的路由信息
const routers = computed(() => permissionStore.topbarRouters);

// 顶部显示菜单
const topMenus = computed(() => {
  let topMenus = [];
  routers.value.map((menu) => {
    if (menu.hidden !== true) {
      // 兼容顶部栏一级菜单内部跳转
      if (menu.path === '/') {
        topMenus.push(menu.children[0]);
      } else {
        topMenus.push(menu);
      }
    }
  });
  return topMenus;
});

// 设置子路由
const childrenMenus = computed(() => {
  let childrenMenus = [];
  routers.value.map((router) => {
    for (let item in router.children) {
      if (router.children[item].parentPath === undefined) {
        if (router.path === '/') {
          router.children[item].path = '/' + router.children[item].path;
        } else {
          if (!isHttp(router.children[item].path)) {
            router.children[item].path = router.path + '/' + router.children[item].path;
          }
        }
        router.children[item].parentPath = router.path;
      }
      childrenMenus.push(router.children[item]);
    }
  });
  return constantRoutes.concat(childrenMenus);
});

// 默认激活的菜单
const activeMenu = computed(() => {
  const path = route.path;
  let activePath = path;
  if (path !== undefined && path.lastIndexOf('/') > 0 && hideList.indexOf(path) === -1) {
    const tmpPath = path.substring(1, path.length);
    if (!route.meta.link) {
      activePath = '/' + tmpPath.substring(0, tmpPath.indexOf('/'));
      appStore.toggleSideBarHide(false);
    }
  } else if (!route.children) {
    activePath = path;
    appStore.toggleSideBarHide(true);
  }
  activeRoutes(activePath);
  return activePath;
});

function handleSelect(key) {
  const route = routers.value.find((item) => item.path === key);
  if (isHttp(key)) {
    // http(s):// 路径新窗口打开
    window.open(key, '_blank');
  } else if (!route || !route.children) {
    // 没有子路由路径内部打开
    const routeMenu = childrenMenus.value.find((item) => item.path === key);
    if (routeMenu && routeMenu.query) {
      let query = JSON.parse(routeMenu.query);
      router.push({ path: key, query: query });
    } else {
      router.push({ path: key });
    }
    appStore.toggleSideBarHide(true);
  } else {
    // 显示左侧联动菜单
    activeRoutes(key);
    appStore.toggleSideBarHide(false);
  }
}

function activeRoutes(key) {
  let routes = [];
  if (childrenMenus.value && childrenMenus.value.length > 0) {
    childrenMenus.value.map((item) => {
      if (key == item.parentPath || (key == 'index' && '' == item.path)) {
        routes.push(item);
      }
    });
  }
  if (routes.length > 0) {
    permissionStore.setSidebarRouters(routes);
  } else {
    appStore.toggleSideBarHide(true);
  }
  return routes;
}
</script>

<style>
/* TopNav 顶部菜单整体容器，复用顶部导航主题色 */
.topmenu-container.el-menu--horizontal {
  font-family: var(--app-nav-font-family);
  height: var(--app-nav-header-height);
  line-height: var(--app-nav-header-height);
  border-bottom: none;
  background-color: transparent;
  box-shadow: none;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  width: 0;
}

.topmenu-container.el-menu--horizontal > .el-menu-item,
.topmenu-container.el-menu--horizontal > .el-sub-menu .el-sub-menu__title {
  float: none;
  height: var(--app-nav-header-height) !important;
  line-height: var(--app-nav-header-height) !important;
  color: var(--app-nav-header-text) !important;
  padding: 0 var(--app-nav-content-end) !important;
  margin: 0 !important;
  font-size: var(--app-nav-font-size);
  font-weight: var(--app-nav-emphasis-weight);
  border-radius: 0;
  border-bottom: var(--app-nav-indicator-width) solid transparent !important;
  box-sizing: border-box;
  transition: var(--app-nav-state-transition);
}

/* 悬停和焦点保留 header 文字语义，不覆盖激活项的 selected 表面。 */
.topmenu-container.el-menu--horizontal
  > .el-menu-item:not(.is-disabled):not(.is-active):is(:focus, :hover),
.topmenu-container.el-menu--horizontal
  > .el-sub-menu:not(.is-disabled):not(.is-active)
  .el-sub-menu__title:is(:focus, :hover) {
  background-color: var(--app-nav-hover-fill) !important;
  color: var(--app-nav-hover-text) !important;
}

/* 激活、悬停激活项和聚焦激活项共用主题的 selected 表面。 */
.topmenu-container.el-menu--horizontal > .el-menu-item.is-active,
.topmenu-container.el-menu--horizontal > .el-sub-menu.is-active .el-sub-menu__title {
  color: var(--app-nav-active-text) !important;
  font-weight: var(--app-nav-emphasis-weight) !important;
  background-color: var(--app-nav-active-fill) !important;
  background-image: var(--app-nav-active-highlight);
  box-shadow: var(--app-nav-active-shadow);
}

/* 边框开关只控制底部指示线，激活项的主题材质保持一致。 */
.topmenu-container.el-menu--horizontal:not(.has-bottom-border) > .el-menu-item.is-active,
.topmenu-container.el-menu--horizontal:not(.has-bottom-border)
  > .el-sub-menu.is-active
  .el-sub-menu__title {
  border-bottom-color: transparent !important;
}

.topmenu-container.el-menu--horizontal.has-bottom-border > .el-menu-item.is-active,
.topmenu-container.el-menu--horizontal.has-bottom-border
  > .el-sub-menu.is-active
  .el-sub-menu__title {
  border-bottom-color: var(--app-nav-indicator) !important;
}

/* 图标右间距 */
.topmenu-container.el-menu--horizontal > .el-menu-item .navigation-menu-icon {
  width: var(--app-nav-icon-size);
  height: var(--app-nav-icon-size);
  margin-right: calc(var(--app-nav-space) * 1.5);
}

/* topmenu more arrow */
.topmenu-container .el-sub-menu .el-sub-menu__icon-arrow {
  width: var(--app-nav-chevron-size);
  font-size: var(--app-nav-chevron-size);
  transition: transform var(--app-nav-motion-arrow) var(--app-nav-ease-control);
  position: static;
  vertical-align: middle;
  margin-left: calc(var(--app-nav-space) * 2);
  margin-top: 0;
}
</style>
