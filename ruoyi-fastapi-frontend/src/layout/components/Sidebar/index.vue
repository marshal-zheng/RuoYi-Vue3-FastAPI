<template>
  <nav
    id="app-sidebar"
    class="sidebar-container"
    :class="{
      'is-collapsed': isCollapse,
      'is-collapsing': isCollapse && !menuCollapsed,
    }"
    aria-label="主导航"
    data-zx-surface="panel"
  >
    <div class="sidebar-header" data-zx-surface="header">
      <Logo
        v-if="settingsStore.sidebarLogo"
        :collapse="false"
        :aria-hidden="isCollapse || undefined"
        :inert="isCollapse"
      />
      <Hamburger
        id="sidebar-toggle"
        :is-active="appStore.sidebar.opened"
        @toggleClick="appStore.toggleSideBar()"
      >
        <template v-if="settingsStore.sidebarLogo && appStore.device !== 'mobile'" #brand>
          <img :src="compactLogo" class="sidebar-compact-logo" alt="" />
        </template>
      </Hamburger>
    </div>
    <el-scrollbar wrap-class="scrollbar-wrapper" @click="expandFromRail">
      <el-menu
        ref="menuRef"
        :key="menuCollapsed ? 'rail' : 'expanded'"
        :default-active="activeMenu"
        :collapse="menuCollapsed"
        :unique-opened="defaultSettings.uniqueOpened"
        :collapse-transition="false"
        mode="vertical"
        class="sidebar-menu"
        @select="closeMobileNavigation"
      >
        <sidebar-item
          v-for="(route, index) in sidebarRouters"
          :key="route.path + index"
          :item="route"
          :base-path="route.path"
          :collapsed="isCollapse"
          @expand-group="expandGroup"
        />
      </el-menu>
    </el-scrollbar>
  </nav>
</template>

<script setup>
import Logo from './Logo';
import Hamburger from '@/components/ui/Hamburger';
import SidebarItem from './SidebarItem';
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';
import compactLogo from '@/assets/logo/logo.png';
import defaultSettings from '@/settings';

const emit = defineEmits(['close']);
const route = useRoute();
const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();
const menuRef = ref(null);

const sidebarRouters = computed(() => permissionStore.sidebarRouters);
const isCollapse = computed(() => appStore.device !== 'mobile' && !appStore.sidebar.opened);
const menuCollapsed = ref(isCollapse.value);
let foldingGroups = [];

watch(isCollapse, async (collapsed, _, onCleanup) => {
  let cancelled = false;
  onCleanup(() => (cancelled = true));

  if (!collapsed) {
    menuCollapsed.value = false;
    await nextTick();
    if (cancelled) return;
    foldingGroups.forEach((index) => menuRef.value?.open(index));
    foldingGroups = [];
    return;
  }

  const menu = menuRef.value?.$el;
  foldingGroups = Array.from(menu?.querySelectorAll('.el-sub-menu.is-opened') ?? []).map(
    (group) => group.dataset.sidebarGroup
  );
  if (
    appStore.sidebar.withoutAnimation ||
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    menuCollapsed.value = true;
    foldingGroups = [];
    return;
  }

  // Keep the menu mounted until its native transitions and the shell have folded.
  foldingGroups.forEach((index) => menuRef.value.close(index));
  await nextTick();
  await new Promise(requestAnimationFrame);
  if (cancelled) return;
  const transitions = menu
    .getAnimations({ subtree: true })
    .filter((animation) =>
      animation.effect?.target?.matches('.el-menu--inline, .el-sub-menu__title, .el-menu-item')
    );
  await Promise.all(transitions.map((animation) => animation.finished.catch(() => {})));
  if (!cancelled) {
    menuCollapsed.value = true;
    foldingGroups = [];
  }
});

function closeMobileNavigation() {
  if (appStore.device === 'mobile') emit('close');
}

function expandFromRail(event) {
  if (
    isCollapse.value &&
    event.target instanceof Element &&
    !event.target.closest('a, button, [role="menuitem"], .el-scrollbar__bar')
  ) {
    appStore.toggleSideBar();
  }
}

async function expandGroup(index) {
  if (!isCollapse.value) return;
  foldingGroups = [];
  appStore.toggleSideBar();
  await nextTick();
  menuRef.value?.open(index);
  await nextTick();
  menuRef.value?.$el.querySelector(`[data-sidebar-group="${CSS.escape(index)}"]`)?.focus({
    preventScroll: true,
  });
}

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
  display: flex;
  flex-direction: column;
  font-family: var(--app-nav-font-family);
  border-width: 0 var(--app-nav-line-width) 0 0;

  .sidebar-header {
    position: relative;
    display: flex;
    align-items: center;
    flex: 0 0 var(--app-nav-header-height);
    min-width: 0;
    border-width: 0 0 var(--app-nav-line-width);

    .sidebar-logo-container {
      position: absolute;
      inset-inline: var(--app-nav-brand-start) var(--app-nav-brand-end);
      opacity: 1;
      visibility: visible;
      transition:
        opacity var(--app-nav-motion-fast) var(--app-nav-ease-state),
        visibility 0s;
    }

    .navigation-toggle {
      position: absolute;
      inset-inline-end: var(--app-nav-control-end);
    }

    .sidebar-compact-logo {
      display: block;
      width: var(--app-nav-compact-logo-size);
      height: var(--app-nav-compact-logo-size);
    }
  }

  &.is-collapsed .sidebar-logo-container {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition-delay: 0s, var(--app-nav-motion-fast);
  }

  .el-scrollbar {
    flex: 1;
    min-height: 0;
  }

  &.is-collapsed .el-scrollbar {
    cursor: e-resize;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar-container .sidebar-header .sidebar-logo-container {
    transition: none;
  }
}
</style>
