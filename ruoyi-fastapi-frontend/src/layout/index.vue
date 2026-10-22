<template>
  <div :class="[classObj, { sidebarHidden: sidebar.hide }]" class="app-wrapper">
    <header
      v-if="visibility.headerVisible"
      class="app-header flex items-center justify-between"
      data-zx-surface="header"
    >
      <Navbar
        class="flex-1"
        :breadcrumb-visible="visibility.breadcrumbVisible"
        @setLayout="setLayout"
      />
    </header>
    <Sidebar v-if="!sidebar.hide && device !== 'mobile'" class="sidebar-container" />
    <el-drawer
      v-if="!sidebar.hide && device === 'mobile'"
      :model-value="sidebar.opened"
      direction="ltr"
      size="min(var(--app-nav-sidebar-width), calc(100vw - var(--app-nav-header-height)))"
      title="主导航"
      :with-header="false"
      :show-close="false"
      append-to-body
      class="app-navigation-drawer"
      body-class="app-navigation-drawer__body"
      modal-class="app-navigation-overlay"
      @close="handleClickOutside"
      @opened="focusNavigation"
      @closed="restoreNavigationFocus"
    >
      <Sidebar @close="handleClickOutside" />
    </el-drawer>
    <div :class="{ sidebarHide: sidebar.hide }" class="main-container">
      <TagsView v-if="visibility.tagsView" class="app-tabs" />
      <AppMain />
    </div>
    <div v-if="!visibility.headerVisible" class="layout-recovery">
      <Hamburger
        v-if="!sidebar.hide && device === 'mobile'"
        :is-active="sidebar.opened"
        id="mobile-navigation-recovery"
        @toggleClick="appStore.toggleSideBar()"
      />
      <ZxButton
        v-if="settingsStore.showSettings"
        class="layout-settings-recovery"
        circle
        aria-label="打开布局设置"
        @click="setLayout"
      >
        <ZxIcon :icon="navigationIcons.settings" size="var(--app-nav-action-icon-size)" />
      </ZxButton>
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
import { ZxButton } from '@zxio/zxui/core';
import { ZxIcon } from '@zxio/zxui/core';
import Hamburger from '@/components/ui/Hamburger';
import { resolveLayoutVisibility } from './policy';
import { navigationIcons } from '@/icons/navigation';
const route = useRoute();

const settingsStore = useSettingsStore();
const appStore = useAppStore();
const sidebar = computed(() => appStore.sidebar);
const device = computed(() => useAppStore().device);
const visibility = computed(() => resolveLayoutVisibility(settingsStore, route.meta));

const classObj = computed(() => ({
  hideSidebar: !sidebar.value.opened,
  openSidebar: sidebar.value.opened,
  withoutAnimation: sidebar.value.withoutAnimation,
  mobile: device.value === 'mobile',
}));

const { width } = useWindowSize();

watch(
  () => device.value,
  () => {
    if (device.value === 'mobile' && sidebar.value.opened) {
      useAppStore().closeSideBar({ withoutAnimation: false });
    }
  }
);

watchEffect(() => {
  const breakpoint = Number.parseFloat(
    getComputedStyle(document.body).getPropertyValue('--app-nav-mobile-breakpoint')
  );
  if (width.value - 1 < breakpoint) {
    useAppStore().toggleDevice('mobile');
    useAppStore().closeSideBar({ withoutAnimation: true });
  } else {
    useAppStore().toggleDevice('desktop');
  }
});

function focusNavigation() {
  document.getElementById('sidebar-toggle')?.focus();
}

function restoreNavigationFocus() {
  const target = visibility.value.headerVisible
    ? 'hamburger-container'
    : 'mobile-navigation-recovery';
  document.getElementById(target)?.focus();
}

function handleClickOutside() {
  useAppStore().closeSideBar({ withoutAnimation: false });
}

const settingRef = ref(null);
function setLayout() {
  settingRef.value.openSetting();
}
</script>

<style lang="less" scoped>
.app-header {
  border-width: 0 0 var(--app-nav-line-width);
  font-family: var(--app-nav-font-family);
}

.app-wrapper {
  --app-sidebar-size: var(--app-nav-sidebar-width);
  display: grid;
  grid-template-columns: var(--app-sidebar-size) minmax(0, 1fr);
  grid-template-rows: auto minmax(0, 1fr);
  position: relative;
  height: 100vh;
  height: 100dvh;
  width: 100%;
  overflow: hidden;
  transition: grid-template-columns var(--app-nav-motion-panel) var(--app-nav-ease-panel);
}
.app-wrapper.hideSidebar {
  --app-sidebar-size: var(--app-nav-rail-width);
}
.app-wrapper.sidebarHidden,
.app-wrapper.mobile {
  --app-sidebar-size: 0px;
}
.app-wrapper.sidebarHidden,
.app-wrapper.mobile,
.app-wrapper.withoutAnimation {
  transition: none;
}
.app-header {
  grid-column: 2;
  grid-row: 1;
  height: var(--app-nav-header-height);
  min-width: 0;
  z-index: var(--app-nav-header-layer);
}
.app-wrapper > .sidebar-container {
  grid-column: 1;
  grid-row: 1 / -1;
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
.app-wrapper.sidebarHidden > .app-header,
.app-wrapper.mobile > .app-header {
  grid-column: 1 / -1;
}
.layout-recovery {
  font-family: var(--app-nav-font-family);
  position: absolute;
  right: var(--app-nav-content-end);
  bottom: var(--app-nav-content-end);
  display: flex;
  gap: calc(var(--app-nav-space) * 2);
  z-index: var(--app-nav-header-layer);
}
.layout-recovery .layout-settings-recovery {
  width: var(--app-nav-control-size);
  height: var(--app-nav-control-size);
  min-width: var(--app-nav-control-size);
  padding: 0;
  border-radius: var(--app-nav-control-radius);
  font-family: var(--app-nav-font-family);
  transition: var(--app-nav-state-transition);
}
.layout-recovery .layout-settings-recovery:focus-visible {
  outline: var(--app-nav-focus-width) solid var(--app-nav-focus);
  outline-offset: calc(-1 * var(--app-nav-focus-width));
}

@media (prefers-reduced-motion: reduce) {
  .app-wrapper {
    transition: none;
  }
}
</style>
