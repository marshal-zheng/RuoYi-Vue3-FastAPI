<template>
  <div class="navbar flex justify-between relative">
    <div class="navbar-navigation flex items-center">
      <hamburger
        v-if="appStore.device === 'mobile' && !appStore.sidebar.hide"
        id="hamburger-container"
        :is-active="appStore.sidebar.opened"
        class="hamburger-container"
        style="color: var(--top-header-hamburger-color)"
        @toggleClick="toggleSideBar"
      />
      <breadcrumb
        v-if="breadcrumbVisible && !settingsStore.topNav"
        id="breadcrumb-container"
        class="breadcrumb-container"
      />
      <top-nav v-if="settingsStore.topNav" id="topmenu-container" class="topmenu-container" />
    </div>

    <div class="navbar-actions flex items-center">
      <ZxThemePresetSwitch />
      <el-dropdown @command="handleCommand" class="avatar-container flex" trigger="click">
        <button
          type="button"
          :aria-label="`用户菜单：${userStore.nickName}`"
          class="avatar-wrapper flex items-center"
          style="color: var(--top-header-avatar-text-color)"
        >
          <ZxIcon
            icon="User"
            size="var(--app-nav-action-icon-size)"
            class="avatar-icon"
            style="color: var(--top-header-avatar-icon-color)"
          />
          <span class="avatar-name">{{ userStore.nickName }}</span>
          <ZxIcon icon="ArrowDown" size="var(--app-nav-chevron-size)" class="ml-0" />
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <router-link to="/user/profile">
              <el-dropdown-item>个人中心</el-dropdown-item>
            </router-link>
            <el-dropdown-item command="setLayout" v-if="settingsStore.showSettings">
              <span>布局设置</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { useOperation } from '@/utils/operation';
import { ElMessageBox } from 'element-plus';
import Breadcrumb from '@/components/ui/Breadcrumb';
import TopNav from '@/components/ui/TopNav';
import Hamburger from '@/components/ui/Hamburger';
import useAppStore from '@/store/modules/app';
import useUserStore from '@/store/modules/user';
import useSettingsStore from '@/store/modules/settings';
import ZxThemePresetSwitch from '@/theme/ZxThemePresetSwitch.vue';

defineProps({ breadcrumbVisible: { type: Boolean, default: true } });

const appStore = useAppStore();
const userStore = useUserStore();
const settingsStore = useSettingsStore();

function toggleSideBar() {
  appStore.toggleSideBar();
}

function handleCommand(command) {
  switch (command) {
    case 'setLayout':
      setLayout();
      break;
    case 'logout':
      logout();
      break;
    default:
      break;
  }
}

const { run: logout } = useOperation(async () => {
  await ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    zIndex: 9999,
  })
    .then(async () => {
      await userStore.logOut().then(() => {
        location.href = '/login';
      });
    })
    .catch(() => {});
});

const emits = defineEmits(['setLayout']);
function setLayout() {
  emits('setLayout');
}
</script>

<style scoped>
.navbar {
  align-items: center;
  min-width: 0;
  height: 100%;
  padding-inline: calc(var(--app-nav-space) * 5) var(--app-nav-content-end);
  gap: var(--app-nav-content-end);
}
.navbar-navigation {
  flex: 1;
  min-width: 0;
  gap: var(--app-nav-icon-gap);
  overflow: hidden;
}
.navbar-actions {
  gap: var(--app-nav-content-end);
}
.navbar-actions :deep(.zx-theme-preset-switch),
.navbar-actions :deep(.zx-theme-mode-switch) {
  height: var(--app-nav-control-size);
}
.navbar-actions :deep(.zx-theme-mode-switch) {
  width: var(--app-nav-control-size);
}
.navbar-actions,
.hamburger-container {
  flex-shrink: 0;
}
.breadcrumb-container {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}
.avatar-name {
  max-width: var(--app-nav-avatar-max-width);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.avatar-wrapper {
  min-height: var(--app-nav-control-size);
  min-width: var(--app-nav-control-size);
  padding: 0 calc(var(--app-nav-space) * 2);
  border: 0;
  border-radius: var(--app-nav-item-radius);
  background: transparent;
  font: inherit;
  gap: calc(var(--app-nav-space) * 2);
  font-size: var(--app-nav-font-size);
  font-weight: var(--app-nav-emphasis-weight);
  cursor: pointer;
}
.avatar-wrapper:focus-visible {
  outline: var(--app-nav-focus-width) solid var(--app-nav-focus);
  outline-offset: calc(-1 * var(--app-nav-focus-width));
}
.topmenu-container {
  margin-inline-start: calc(var(--app-nav-space) * 2);
}
.avatar-icon {
  transition: color var(--app-nav-motion-fast) var(--app-nav-ease-state);
}
:global(.app-wrapper.mobile .navbar) {
  padding-inline: calc(var(--app-nav-space) * 2);
  gap: calc(var(--app-nav-space) * 2);
}
:global(.app-wrapper.mobile .navbar-actions) {
  gap: calc(var(--app-nav-space) * 2);
}
:global(.app-wrapper.mobile .navbar-actions .zx-theme-preset-switch) {
  width: var(--app-nav-control-size);
}
:global(.app-wrapper.mobile .avatar-wrapper) {
  padding-inline: calc(var(--app-nav-space) * 1.5);
}
:global(.app-wrapper.mobile .avatar-name) {
  display: none;
}
:global(.app-wrapper.mobile .breadcrumb-container .el-breadcrumb__item:not(:last-child)) {
  display: none;
}
:global(.app-wrapper.mobile .breadcrumb-container .el-breadcrumb__inner) {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.avatar-wrapper:hover {
  background: var(--top-header-avatar-bg-hover);
}

.avatar-wrapper:hover :deep(.zx-icon) {
  color: var(--top-header-avatar-icon-hover-color) !important;
}

.avatar-wrapper:hover span {
  color: var(--top-header-avatar-text-hover-color);
}
</style>
