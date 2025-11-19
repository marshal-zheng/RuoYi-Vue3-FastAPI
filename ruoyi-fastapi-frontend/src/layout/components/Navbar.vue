<template>
  <div class="navbar flex justify-between">
    <div class="float-left">
      <hamburger
        id="hamburger-container"
        :is-active="appStore.sidebar.opened"
        class="hamburger-container"
        @toggleClick="toggleSideBar"
      />
      <breadcrumb
        v-if="!settingsStore.topNav"
        id="breadcrumb-container"
        class="breadcrumb-container"
      />
      <top-nav v-if="settingsStore.topNav" id="topmenu-container" class="topmenu-container" />
    </div>

    <div class="rt items-center flex mr-4">
      <el-dropdown
        @command="handleCommand"
        class="avatar-container flex ml-4 right-menu-item hover-effect"
        trigger="hover"
      >
        <div class="avatar-wrapper flex items-center gap-1">
          <ZxIcon icon="User" :size="20" class="user-avatar-icon" />
          <span class="user-nickname"> {{ userStore.nickName }} </span>
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
import Screenfull from '@/components/Screenfull';
import SizeSelect from '@/components/SizeSelect';
import HeaderSearch from '@/components/HeaderSearch';
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
  console.log('handleCommand called with:', command);
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
  console.log('logout function called');
  ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    zIndex: 9999,
  })
    .then(() => {
      console.log('User confirmed logout');
      userStore
        .logOut()
        .then(() => {
          console.log('logOut successful, redirecting...');
          location.href = '/index';
        })
        .catch((error) => {
          console.error('logOut failed:', error);
        });
    })
    .catch(() => {
      console.log('User cancelled logout');
    });
}

const emits = defineEmits(['setLayout']);
function setLayout() {
  emits('setLayout');
}

function toggleTheme() {
  settingsStore.toggleTheme();
}
</script>

<style lang="less" scoped>
.navbar {
  height: var(--top-header-height, 50px);
  overflow: hidden;
  position: relative;
  background: var(--top-header-bg);
  box-shadow: var(--top-header-shadow);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    cursor: pointer;
    transition: all 0.3s;
    -webkit-tap-highlight-color: transparent;
    color: var(--top-header-hamburger-color);

    &:hover {
      background: var(--top-header-hamburger-hover-bg);
      color: var(--top-header-hamburger-hover-color);
    }
  }

  .breadcrumb-container {
    float: left;
  }

  .topmenu-container {
    position: absolute;
    left: 50px;
  }

  .errLog-container {
    display: inline-block;
    vertical-align: top;
  }

  .right-menu {
    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: var(--top-header-icon-color);
      vertical-align: text-bottom;

      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: var(--top-header-hover-bg);
        }
      }

      &.theme-switch-wrapper {
        display: flex;
        align-items: center;

        svg {
          transition: transform 0.3s;

          &:hover {
            transform: scale(1.15);
          }
        }
      }
    }

    .avatar-container {
      margin-right: 0px;
      padding-right: 0px;

      .avatar-wrapper {
        display: flex;
        align-items: center;
        margin-top: 0;
        right: 8px;
        position: relative;
        padding: 6px 12px;
        transition: all 0.3s;

        &:hover {
          background: var(--top-header-avatar-bg-hover);
          border-radius: 6px;
          
          .user-avatar-icon {
            color: var(--top-header-avatar-icon-hover-color);
          }
          
          .user-nickname {
            color: var(--top-header-avatar-text-hover-color);
          }
        }

        .user-avatar-icon {
          cursor: pointer;
          width: 20px;
          height: 20px;
          margin-right: 8px;
          color: var(--top-header-avatar-icon-color);
          transition: color 0.3s;

          &:hover {
            color: var(--top-header-avatar-icon-hover-color);
          }
        }

        .user-nickname {
          font-size: 14px;
          font-weight: 500;
          color: var(--top-header-avatar-text-color);
          transition: color 0.3s;
        }

        i {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 25px;
          font-size: 12px;
        }
      }
    }
  }
}
</style>
