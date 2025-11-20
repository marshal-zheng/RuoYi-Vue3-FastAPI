<template>
  <div
    class="sidebar-logo-container relative w-full flex items-center justify-center overflow-hidden"
    :class="[{ collapse: collapse }, variantClass]"
  >
    <transition name="sidebarLogoFade">
      <router-link
        v-if="collapse"
        key="collapse"
        class="h-full w-full flex items-center justify-center"
        to="/"
      >
        <img v-if="logo" :src="logo" class="w-8 h-8 shrink-0" />
        <h1 v-else class="sidebar-title m-0 p-0">{{ title }}</h1>
      </router-link>
      <router-link
        v-else
        key="expand"
        class="h-full w-full flex items-center justify-center"
        to="/"
      >
        <img v-if="logo" :src="logo" :class="logoSizeClass" class="shrink-0 mr-3" />
        <h1 :class="titleSizeClass" class="sidebar-title m-0 p-0 font-semibold leading-none tracking-[0.5px] select-none">
          {{ title }}
        </h1>
      </router-link>
    </transition>
  </div>
</template>

<script setup>
import logoImg from '@/assets/logo/logo.png';
import defaultSettings from '@/settings';
import { computed } from 'vue';

const props = defineProps({
  collapse: {
    type: Boolean,
    required: true,
  },
  variant: {
    type: String,
    default: 'sidebar', // 'sidebar' | 'login'
    validator: (value) => ['sidebar', 'login'].includes(value),
  },
});

const variantClass = computed(() => {
  return props.variant === 'login' ? 'login-variant' : '';
});

const logoSizeClass = computed(() => {
  return props.variant === 'login' ? 'w-12 h-12' : 'w-8 h-8';
});

const titleSizeClass = computed(() => {
  return props.variant === 'login' ? 'text-2xl' : 'text-[16px]';
});

const title = import.meta.env.VITE_APP_TITLE;
// 是否启用 logo 图片，如果为 false 则只显示文字标题
const showLogoImage = defaultSettings.showLogoImage ?? true;
const logo = showLogoImage ? logoImg : null;
</script>

<style scoped>
@import '@/assets/styles/theme.module.css';

/* Vue 过渡动画 - 必须用 CSS */
.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

/* CSS 变量 - 必须用 CSS */
.sidebar-logo-container {
  height: var(--logo-height, 50px);
  background: var(--left-menu-header-bg);
  box-shadow: var(--left-menu-header-shadow);
}

.sidebar-logo-container.login-variant {
  background: transparent;
  box-shadow: none;
  height: auto;
}

.sidebar-title {
  color: var(--logo-title-text-color, #f0f4ff);
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  transition: all 0.3s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.sidebar-logo-container.login-variant .sidebar-title {
  color: #1f2937;
  text-shadow: none;
}

.sidebar-title:hover {
  color: var(--logo-title-text-hover-color, #ffffff);
  transform: scale(1.02);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.sidebar-logo-container.login-variant .sidebar-title:hover {
  color: #111827;
  text-shadow: none;
}

/* collapse 状态下的特殊样式 */
.sidebar-logo-container.collapse .sidebar-logo {
  margin-right: 0;
}
</style>
