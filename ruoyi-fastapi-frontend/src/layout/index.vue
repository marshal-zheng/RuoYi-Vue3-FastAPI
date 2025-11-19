<template>
  <div :class="classObj" class="app-wrapper" :style="{ '--current-color': theme }">
    <div
      v-if="device === 'mobile' && sidebar.opened"
      class="drawer-bg"
      @click="handleClickOutside"
    />
    <Sidebar v-if="!sidebar.hide" class="sidebar-container" :style="sidebarInlineStyle" />
    <div :class="{ hasTagsView: needTagsView, sidebarHide: sidebar.hide }" class="main-container">
      <div :class="{ 'fixed-header': true }" :style="fixedHeaderStyle">
        <!-- Header 区域：在未启用 tagsView 时显示 Logo + Navbar；启用时只显示 Navbar -->
        <div
          class="flex items-center justify-between affordable-thunder"
          style="background: var(--top-header-bg); box-shadow: var(--top-header-shadow)"
        >
          <div
            v-if="!needTagsView && showLogo"
            class="flex items-center h-[50px] px-4 gap-2 shrink-0"
          >
            <img :src="headerLogo" class="w-8 h-8 shrink-0" />
            <span
              class="text-[16px] font-semibold leading-none tracking-[0.5px] select-none text-[var(--logo-title-text-color,#f0f4ff)]"
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
const theme = computed(() => settingsStore.theme);
const sidebar = computed(() => useAppStore().sidebar);
const device = computed(() => useAppStore().device);
const needTagsView = computed(() => settingsStore.tagsView);

// 定义显示控制变量
const showLogo = computed(() => settingsStore.sidebarLogo);
const showNavbar = computed(() => true); // Navbar 始终显示
const showTagsView = computed(() => needTagsView.value);

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

.drawer-bg {
  background: #000;
  opacity: 0.3;
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
