<template>
  <div :class="[classObj, { sidebarHidden: sidebar.hide }]" class="app-wrapper">
    <div
      v-if="device === 'mobile' && sidebar.opened"
      class="drawer-bg"
      @click="handleClickOutside"
    />
    <div
      v-if="visibility.headerVisible"
      class="app-header flex items-center justify-between"
      data-zx-surface="header"
    >
      <div v-if="showLogo" class="flex items-center h-[50px] px-4 gap-2">
        <img :src="headerLogo" class="w-8 h-8 shrink-0" alt="" />
        <span
          v-if="!isCollapse"
          class="text-[16px] font-semibold leading-none tracking-[0.5px] select-none"
          >{{ headerTitle }}</span
        >
      </div>
      <Navbar
        class="flex-1"
        :breadcrumb-visible="visibility.breadcrumbVisible"
        @setLayout="setLayout"
      />
    </div>
    <Sidebar
      v-if="!sidebar.hide"
      :header-visible="visibility.headerVisible"
      class="sidebar-container"
    />
    <div :class="{ sidebarHide: sidebar.hide }" class="main-container">
      <TagsView v-if="visibility.tagsView" class="app-tabs" />
      <AppMain />
    </div>
    <div v-if="!visibility.headerVisible" class="layout-recovery">
      <ZxButton
        v-if="!sidebar.hide"
        icon="Menu"
        circle
        aria-label="展开或收起导航"
        @click="appStore.toggleSideBar()"
      />
      <ZxButton
        v-if="settingsStore.showSettings"
        icon="Setting"
        circle
        aria-label="打开布局设置"
        @click="setLayout"
      />
    </div>
    <Settings ref="settingRef" />
  </div>
</template>

<script setup>
import { useWindowSize } from '@vueuse/core';
import Sidebar from './components/Sidebar/index.vue';
import { AppMain, Navbar, Settings, TagsView } from './components';
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import defaultSettings from '@/settings';
import headerLogo from '@/assets/logo/logo.png';
import { ZxButton } from '@zxio/zxui/button';
import { resolveLayoutVisibility } from './policy';
const route = useRoute();

const settingsStore = useSettingsStore();
const appStore = useAppStore();
const sidebar = computed(() => appStore.sidebar);
const device = computed(() => useAppStore().device);
const visibility = computed(() => resolveLayoutVisibility(settingsStore, route.meta));
const showLogo = computed(() => settingsStore.sidebarLogo);
const isCollapse = computed(() => !sidebar.value.opened);
const headerTitle = computed(() => defaultSettings.title || import.meta.env.VITE_APP_TITLE);

const classObj = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile',
}));

const { width } = useWindowSize();
const WIDTH = 992; // refer to Bootstrap's responsive design

watch(
  () => device.value,
  () => {
    if (device.value === 'mobile' && sidebar.value.opened) {
      useAppStore().closeSideBar({ withoutAnimation: false });
    }
  }
);

watchEffect(() => {
  if (width.value - 1 < WIDTH) {
    useAppStore().toggleDevice('mobile');
    useAppStore().closeSideBar({ withoutAnimation: true });
  } else {
    useAppStore().toggleDevice('desktop');
  }
});

function handleClickOutside() {
  useAppStore().closeSideBar({ withoutAnimation: false });
}

const settingRef = ref(null);
function setLayout() {
  settingRef.value.openSetting();
}
</script>

<style lang="less" scoped>
@import '@/assets/styles/mixin.less';
@import '@/assets/styles/variables.module.less';

// Keep the tint local so Vite HMR does not compile this block against a stale mixin import.
@on-surface-tint: ~'color-mix(in oklab, currentColor calc(var(--zx-semantic-fill-current-tint) * 1%), transparent)';

// The header surface paints background, border, shadow and on-text colour.
// Its children still read the legacy --top-header-* names, so they are rebound
// here, at the scope boundary, instead of on the document root.
.app-header {
  // A top band only separates itself from the content below it.
  border-width: 0 0 1px;

  --top-header-text-color: var(--zx-semantic-surface-header-on-text);
  --top-header-icon-color: var(--zx-semantic-surface-header-on-text-secondary);
  --top-header-icon-hover-color: var(--zx-semantic-surface-header-on-text);
  --top-header-hover-bg: @on-surface-tint;

  --top-header-hamburger-color: var(--zx-semantic-surface-header-on-text);
  --top-header-hamburger-hover-color: var(--zx-semantic-surface-header-on-text);
  --top-header-hamburger-hover-bg: @on-surface-tint;
  --top-header-menu-hover-bg: @on-surface-tint;
  --top-header-menu-active-bg: var(--zx-semantic-fill-selected);

  --top-header-breadcrumb-color: var(--zx-semantic-surface-header-on-text);
  --top-header-breadcrumb-hover-color: var(--zx-semantic-surface-header-on-text);
  --top-header-breadcrumb-separator-color: var(--zx-semantic-surface-header-on-text-secondary);

  --top-header-avatar-icon-color: var(--zx-semantic-surface-header-on-text-secondary);
  --top-header-avatar-icon-hover-color: var(--zx-semantic-surface-header-on-text);
  --top-header-avatar-text-color: var(--zx-semantic-surface-header-on-text);
  --top-header-avatar-text-hover-color: var(--zx-semantic-surface-header-on-text);
  --top-header-avatar-bg-hover: @on-surface-tint;

  --logo-title-text-color: var(--zx-semantic-surface-header-on-text);
  --logo-title-text-hover-color: var(--zx-semantic-surface-header-on-text);
}

.app-wrapper {
  --app-sidebar-size: var(--base-sidebar-width);
  display: grid;
  grid-template-columns: var(--app-sidebar-size) minmax(0, 1fr);
  grid-template-rows: auto minmax(0, 1fr);
  position: relative;
  height: 100vh;
  height: 100dvh;
  width: 100%;
  overflow: hidden;
}
.app-wrapper.hideSidebar {
  --app-sidebar-size: 54px;
}
.app-wrapper.sidebarHidden,
.app-wrapper.mobile {
  --app-sidebar-size: 0px;
}
.app-header {
  grid-column: 1 / -1;
  grid-row: 1;
  min-width: 0;
  z-index: 9;
}
.app-wrapper > .sidebar-container {
  grid-column: 1;
  grid-row: 2;
  position: relative;
  top: auto;
  bottom: auto;
  min-height: 0;
  height: auto;
  transition: none;
}
.app-wrapper > .main-container {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  margin-left: 0;
  overflow: hidden;
  transition: none;
}
.app-tabs {
  flex: 0 0 auto;
}
.app-wrapper.mobile > .sidebar-container {
  position: fixed;
  top: 0;
  bottom: 0;
  height: 100%;
}
.drawer-bg {
  background: var(--zx-semantic-overlay-modal);
  position: absolute;
  inset: 0;
  z-index: 999;
}
.layout-recovery {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  gap: 8px;
  z-index: 9;
}
</style>
