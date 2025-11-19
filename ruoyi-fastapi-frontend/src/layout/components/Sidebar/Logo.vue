<template>
  <div class="sidebar-logo-container" :class="{ collapse: collapse }">
    <transition name="sidebarLogoFade">
      <router-link v-if="collapse" key="collapse" class="sidebar-logo-link" to="/">
        <!-- <img v-if="logo" :src="logo" class="sidebar-logo" /> -->
        <!-- <h1 v-else class="sidebar-title">{{ title }}</h1> -->
      </router-link>
      <router-link v-else key="expand" class="sidebar-logo-link" to="/">
        <!-- <img v-if="logo" :src="logo" class="sidebar-logo" /> -->
        <h1 class="sidebar-title">{{ title }}</h1>
      </router-link>
    </transition>
  </div>
</template>

<script setup>
import logo from '@/assets/logo/logo.png';
import useSettingsStore from '@/store/modules/settings';
import variables from '@/assets/styles/theme.module.css';

defineProps({
  collapse: {
    type: Boolean,
    required: true,
  },
});

const title = import.meta.env.VITE_APP_TITLE;
const settingsStore = useSettingsStore();
const sideTheme = computed(() => settingsStore.sideTheme);

// 获取Logo背景色
const getLogoBackground = computed(() => {
  if (settingsStore.isDark) {
    return 'var(--sidebar-bg)';
  }
  return sideTheme.value === 'theme-dark' ? variables.menuBg : variables.menuLightBg;
});

// 获取Logo文字颜色
const getLogoTextColor = computed(() => {
  if (settingsStore.isDark) {
    return 'var(--sidebar-text)';
  }
  return sideTheme.value === 'theme-dark' ? '#fff' : variables.menuLightText;
});
</script>

<style scoped>
@import '@/assets/styles/theme.module.css';

.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

.sidebar-logo-container {
  position: relative;
  width: 100%;
  height: var(--logo-height, 50px);
  line-height: var(--logo-height, 50px);
  background: var(--left-menu-header-bg);
  box-shadow: var(--left-menu-header-shadow);
  text-align: center;
  overflow: hidden;
}

.sidebar-logo-container .sidebar-logo-link {
  height: 100%;
  width: 100%;
}

.sidebar-logo-container .sidebar-logo-link .sidebar-logo {
  width: 32px;
  height: 32px;
  vertical-align: middle;
  margin-right: 12px;
}

.sidebar-logo-container .sidebar-logo-link .sidebar-title {
  display: inline-block;
  margin: 0;
  color: var(--logo-title-text-color, #f0f4ff);
  font-weight: bold;
  line-height: var(--logo-height, 50px);
  font-size: 14px;
  font-family:
    Avenir,
    Helvetica Neue,
    Arial,
    Helvetica,
    sans-serif;
  vertical-align: middle;
  transition: color 0.3s ease;

  &:hover {
    color: var(--logo-title-text-hover-color, #ffffff);
  }
}

.sidebar-logo-container.collapse .sidebar-logo {
  margin-right: 0px;
}
</style>
