<template>
  <div class="navbar flex justify-between">
    <div class="fl">
      <hamburger id="hamburger-container" :is-active="appStore.sidebar.opened" class="hamburger-container" @toggleClick="toggleSideBar" />
      <breadcrumb v-if="!settingsStore.topNav" id="breadcrumb-container" class="breadcrumb-container" />
      <top-nav v-if="settingsStore.topNav" id="topmenu-container" class="topmenu-container" />
    </div>

    <div class="rt items-center flex mr-4">
      <el-dropdown @command="handleCommand" class="avatar-container flex ml-4 right-menu-item hover-effect" trigger="hover">
        <div class="avatar-wrapper flex items-center gap-1">
          <svg-icon icon-class="users" class="user-avatar-icon" size="20" />
          <span class="user-nickname"> {{ userStore.nickName }} </span>
          <svg-icon icon-class="ArrowDown" class="ml-0" />
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
import { ElMessageBox } from 'element-plus'
import Breadcrumb from '@/components/Breadcrumb'
import TopNav from '@/components/TopNav'
import Hamburger from '@/components/Hamburger'
import Screenfull from '@/components/Screenfull'
import SizeSelect from '@/components/SizeSelect'
import HeaderSearch from '@/components/HeaderSearch'
import RuoYiGit from '@/components/RuoYi/Git'
import RuoYiDoc from '@/components/RuoYi/Doc'
import useAppStore from '@/store/modules/app'
import useUserStore from '@/store/modules/user'
import useSettingsStore from '@/store/modules/settings'


const appStore = useAppStore()
const userStore = useUserStore()
const settingsStore = useSettingsStore()

function toggleSideBar() {
  appStore.toggleSideBar()
}

function handleCommand(command) {
  console.log('handleCommand called with:', command)
  switch (command) {
    case "setLayout":
      setLayout()
      break
    case "logout":
      logout()
      break
    default:
      break
  }
}

function logout() {
  console.log('logout function called')
  ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    zIndex: 9999
  }).then(() => {
    console.log('User confirmed logout')
    userStore.logOut().then(() => {
      console.log('logOut successful, redirecting...')
      location.href = '/index'
    }).catch(error => {
      console.error('logOut failed:', error)
    })
  }).catch(() => { 
    console.log('User cancelled logout')
  })
}

const emits = defineEmits(['setLayout'])
function setLayout() {
  emits('setLayout')
}

function toggleTheme() {
  settingsStore.toggleTheme()
}
</script>

<style lang='less' scoped>
.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  background: var(--navbar-bg);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    cursor: pointer;
    transition: background 0.3s;
    -webkit-tap-highlight-color: transparent;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
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
      color: #5a5e66;
      vertical-align: text-bottom;

      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: rgba(0, 0, 0, 0.025);
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
        
        &:hover {
          .user-avatar-icon,
          .user-nickname {
            color: var(--el-color-primary);
          }
        }

        .user-avatar-icon {
          cursor: pointer;
          width: 20px;
          height: 20px;
          margin-right: 8px;
          color: #5a5e66;
          transition: color 0.3s;
          
          &:hover {
            color: var(--el-color-primary);
          }
        }

        .user-nickname{
          font-size: 14px;
          font-weight: bold;
          color: #5a5e66;
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
