<template>
  <div :class="classObj" class="app-wrapper">
    <div
      v-if="device === 'mobile' && sidebar.opened"
      class="drawer-bg"
      @click="handleClickOutside"
    />
    <Sidebar v-if="!sidebar.hide" class="sidebar-container" :style="sidebarInlineStyle" />
    <div :class="{ hasTagsView: needTagsView, sidebarHide: sidebar.hide }" class="main-container">
      <div :class="{ 'fixed-header': true }" :style="fixedHeaderStyle">
        <!-- Header 区域：在未启用 tagsView 时显示 Logo + Navbar；启用时只显示 Navbar -->
        <div class="app-header flex items-center justify-between" data-zx-surface="header">
          <div v-if="!needTagsView && showLogo" class="flex items-center h-[50px] px-4 gap-2">
            <img :src="headerLogo" class="w-8 h-8 shrink-0" />
            <!-- 收起侧边栏时隐藏标题文字，效果与 Sidebar 中 Logo 收起一致 -->
            <span
              v-if="!isCollapse"
              class="text-[16px] font-semibold leading-none tracking-[0.5px] select-none"
            >
              {{ headerTitle }}
            </span>
          </div>
          <Navbar v-if="showNavbar" class="flex-1" @setLayout="setLayout" />
        </div>
        <!-- TagsView 显示在 Header 下方 -->
        <TagsView v-if="showTagsView" />
      </div>
      <app-main />
      <settings ref="settingRef" />
    </div>
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

const settingsStore = useSettingsStore();
const sidebar = computed(() => useAppStore().sidebar);
const device = computed(() => useAppStore().device);
const needTagsView = computed(() => settingsStore.tagsView);

// 定义显示控制变量
const showLogo = computed(() => settingsStore.sidebarLogo);
const showNavbar = computed(() => true); // Navbar 始终显示
const showTagsView = computed(() => needTagsView.value);

// 与 Sidebar 折叠状态保持一致，用于控制 Header 中标题的显隐
const isCollapse = computed(() => !sidebar.value.opened);

// Header 中展示的系统标题
const headerTitle = computed(() => defaultSettings.title || import.meta.env.VITE_APP_TITLE);
const headerHeight = 50;

const fixedHeaderStyle = computed(() => {
  if (!needTagsView.value) {
    return {
      width: '100%',
      left: '0',
    };
  }
  return {};
});

const sidebarInlineStyle = computed(() => {
  if (!needTagsView.value) {
    return {
      top: `${headerHeight}px`,
      height: `calc(100% - ${headerHeight}px)`,
    };
  }
  return {};
});

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
@on-surface-tint: ~"color-mix(in oklab, currentColor calc(var(--zx-semantic-fill-current-tint) * 1%), transparent)";

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
  .clearfix();
  position: relative;
  height: 100%;
  width: 100%;

  &.mobile.openSidebar {
    position: fixed;
    top: 0;
  }
}

.main-container:has(.fixed-header) {
  height: 100vh;
  overflow: hidden;
}

// The mobile sidebar is a drawer, so it shares the dialog/drawer backdrop.
.drawer-bg {
  background: var(--zx-semantic-overlay-modal);
  width: 100%;
  top: 0;
  height: 100%;
  position: absolute;
  z-index: 999;
}

.fixed-header {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9;
  width: calc(100% - @base-sidebar-width);
  transition: width 0.28s;
}

.hideSidebar .fixed-header {
  width: calc(100% - 54px);
}

.sidebarHide .fixed-header {
  width: 100%;
}

.mobile .fixed-header {
  width: 100%;
}
</style>
