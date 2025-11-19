<template>
  <el-menu :default-active="activeMenu" mode="horizontal" @select="handleSelect" :ellipsis="false">
    <template v-for="(item, index) in topMenus">
      <el-menu-item
        :style="{ '--theme': theme }"
        :index="item.path"
        :key="index"
        v-if="index < visibleNumber"
      >
        <ZxIcon
          v-if="item.meta && item.meta.icon && item.meta.icon !== '#'"
          :icon="resolveMenuIcon(item.meta.icon)"
          :size="16"
        />
        {{ item.meta.title }}
      </el-menu-item>
    </template>

    <!-- 顶部菜单超出数量折叠 -->
    <el-sub-menu :style="{ '--theme': theme }" index="more" v-if="topMenus.length > visibleNumber">
      <template #title>更多菜单</template>
      <template v-for="(item, index) in topMenus">
        <el-menu-item :index="item.path" :key="index" v-if="index >= visibleNumber">
          <ZxIcon
            v-if="item.meta && item.meta.icon && item.meta.icon !== '#'"
            :icon="resolveMenuIcon(item.meta.icon)"
            :size="16"
          />
          {{ item.meta.title }}
        </el-menu-item>
      </template>
    </el-sub-menu>
  </el-menu>
</template>

<script setup>
import { constantRoutes } from '@/router';
import { isHttp } from '@/utils/validate';
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';

// 顶部栏初始数
const visibleNumber = ref(null);
// 当前激活菜单的 index
const currentIndex = ref(null);
// 隐藏侧边栏路由
const hideList = ['/index', '/user/profile'];

const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();
const route = useRoute();
const router = useRouter();

// 主题颜色
const theme = computed(() => settingsStore.theme);
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

/**
 * 将 RuoYi 路由里的 meta.icon（如 'dashboard'）转换为 ZxIcon 识别的格式
 * 目前路由里的图标都是本地 svg，所以统一加上 'svg-icon:' 前缀
 */
function resolveMenuIcon(icon) {
  if (!icon) {
    return '';
  }
  // 如果已经是带前缀的写法（例如 'mdi:home' 或 'svg-icon:xxx'），直接返回
  if (typeof icon === 'string' && icon.includes(':')) {
    return icon;
  }
  return `svg-icon:${icon}`;
}

function setVisibleNumber() {
  const width = document.body.getBoundingClientRect().width / 3;
  visibleNumber.value = parseInt(width / 85);
}

function handleSelect(key) {
  currentIndex.value = key;
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

onMounted(() => {
  window.addEventListener('resize', setVisibleNumber);
});
onBeforeUnmount(() => {
  window.removeEventListener('resize', setVisibleNumber);
});

onMounted(() => {
  setVisibleNumber();
});
</script>

<style>
/* TopNav 顶部菜单整体容器，复用顶部导航主题色 */
.topmenu-container.el-menu--horizontal {
  height: var(--top-header-height);
  line-height: var(--top-header-height);
  border-bottom: none;
  background-color: transparent;
  box-shadow: none;
}

.topmenu-container.el-menu--horizontal > .el-menu-item,
.topmenu-container.el-menu--horizontal > .el-sub-menu .el-sub-menu__title {
  float: left;
  height: var(--top-header-height) !important;
  line-height: var(--top-header-height) !important;
  color: var(--top-header-breadcrumb-color) !important;
  padding: 0 8px !important;
  margin: 0 6px !important;
  font-size: 14px;
  font-weight: 500;
  transition:
    color 0.2s ease,
    background-color 0.2s ease,
    border-color 0.2s ease;
}

.topmenu-container.el-menu--horizontal > .el-menu-item.is-active,
.topmenu-container.el-menu--horizontal > .el-sub-menu.is-active .el-submenu__title {
  border-bottom: none !important;
  background-color: var(--top-header-menu-active-bg);
  color: var(--top-header-breadcrumb-hover-color) !important;
}

/* 背景色与顶部渐变协调，避免出现一条纯白色横条 */
.topmenu-container.el-menu--horizontal > .el-menu-item:not(.is-disabled):focus,
.topmenu-container.el-menu--horizontal > .el-menu-item:not(.is-disabled):hover,
.topmenu-container.el-menu--horizontal > .el-sub-menu .el-submenu__title:hover {
  background-color: var(--top-header-menu-hover-bg);
  color: var(--top-header-breadcrumb-hover-color) !important;
}

/* 图标右间距 */
.topmenu-container .zx-icon {
  margin-right: 4px;
}

/* topmenu more arrow */
.topmenu-container .el-sub-menu .el-sub-menu__icon-arrow {
  position: static;
  vertical-align: middle;
  margin-left: 8px;
  margin-top: 0px;
}
</style>
