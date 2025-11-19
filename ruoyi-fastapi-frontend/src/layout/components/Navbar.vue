<template>
  <div class="navbar flex justify-between h-[50px] overflow-hidden relative">
    <div class="flex items-center">
      <hamburger
        id="hamburger-container"
        :is-active="appStore.sidebar.opened"
        class="hamburger-container h-full leading-[46px] cursor-pointer transition-all duration-300 px-4"
        style="color: var(--top-header-hamburger-color)"
        @toggleClick="toggleSideBar"
      />
      <breadcrumb
        v-if="!settingsStore.topNav"
        id="breadcrumb-container"
        class="breadcrumb-container"
      />
      <top-nav v-if="settingsStore.topNav" id="topmenu-container" class="topmenu-container ml-2" />
    </div>

    <div class="flex items-center mr-4">
      <el-dropdown
        @command="handleCommand"
        class="avatar-container flex ml-4 cursor-pointer"
        trigger="hover"
      >
        <div
          class="avatar-wrapper flex items-center gap-2 px-3 py-1.5 rounded-md transition-all duration-300 font-medium"
          style="color: var(--top-header-avatar-text-color)"
        >
          <ZxIcon
            icon="User"
            :size="20"
            class="transition-colors duration-300"
            style="color: var(--top-header-avatar-icon-color)"
          />
          <span class="text-sm">{{ userStore.nickName }}</span>
          <ZxIcon icon="ArrowDown" :size="14" class="ml-0" />
        </div>
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
import { ElMessageBox } from 'element-plus';
import Breadcrumb from '@/components/Breadcrumb';
import TopNav from '@/components/TopNav';
import Hamburger from '@/components/Hamburger';
import useAppStore from '@/store/modules/app';
import useUserStore from '@/store/modules/user';
import useSettingsStore from '@/store/modules/settings';

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

function logout() {
  ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    zIndex: 9999,
  })
    .then(() => {
      userStore.logOut().then(() => {
        location.href = '/index';
      });
    })
    .catch(() => {});
}

const emits = defineEmits(['setLayout']);
function setLayout() {
  emits('setLayout');
}
</script>

<style scoped>
/* Minimal custom styles - most styling is done via Tailwind classes */

.hamburger-container:hover {
  background: var(--top-header-hamburger-hover-bg);
  color: var(--top-header-hamburger-hover-color);
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
