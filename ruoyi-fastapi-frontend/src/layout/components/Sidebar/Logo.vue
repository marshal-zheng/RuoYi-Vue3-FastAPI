<template>
  <div
    class="sidebar-logo-container relative w-full flex items-center justify-center overflow-hidden"
    :class="[{ 'is-collapsed': collapse }, variantClass]"
    :data-zx-surface="surfaceRole"
  >
    <transition name="sidebarLogoFade">
      <router-link
        v-if="collapse"
        key="collapse"
        class="h-full w-full flex items-center justify-center"
        to="/"
        :aria-label="title"
        :title="title"
      >
        <img v-if="logo" :src="logo" class="w-8 h-8 shrink-0" />
        <span v-else class="sidebar-title m-0 p-0 font-semibold whitespace-nowrap" aria-hidden="true">
          {{ compactTitle }}
        </span>
      </router-link>
      <router-link
        v-else
        key="expand"
        class="h-full w-full flex items-center justify-center"
        to="/"
        :aria-label="title"
        :title="title"
      >
        <img v-if="logo" :src="logo" :class="logoSizeClass" class="shrink-0 mr-3" />
        <h1
          :class="titleSizeClass"
          class="sidebar-title m-0 p-0 font-semibold leading-none tracking-[0.5px] select-none"
        >
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

const variantClass = computed(() => `${props.variant}-variant`);

// The sidebar strip continues the top header band, as in the ZXUI app shell;
// `brand` is a badge role and would flood the whole strip with the accent.
// On the login page the logo sits on the page itself and carries no surface.
const surfaceRole = computed(() => (props.variant === 'login' ? undefined : 'header'));

const logoSizeClass = computed(() => {
  return props.variant === 'login' ? 'w-12 h-12' : 'w-8 h-8';
});

const titleSizeClass = computed(() => {
  return props.variant === 'login' ? 'text-2xl' : 'text-[16px]';
});

const title = import.meta.env.VITE_APP_TITLE;
const compactTitle = Array.from(title || '').slice(0, 2).join('');
// 是否启用 logo 图片，如果为 false 则只显示文字标题
const showLogoImage = defaultSettings.showLogoImage ?? true;
const logo = showLogoImage ? logoImg : null;
</script>

<style scoped>
/* Vue 过渡动画 - 必须用 CSS */
.sidebarLogoFade-enter-active {
  transition: opacity 1.5s;
}

.sidebarLogoFade-enter,
.sidebarLogoFade-leave-to {
  opacity: 0;
}

.sidebar-logo-container {
  height: var(--logo-height, 50px);
}

/* The header surface paints background, edge and on-text colour. Like the
   header band it keeps only the bottom edge below a full-height band, so
   both bands end on the same line. */
.sidebar-logo-container.sidebar-variant {
  box-sizing: content-box;
  border-width: 0 0 1px;
}

.sidebar-logo-container.login-variant {
  background: transparent;
  box-shadow: none;
  height: auto;
}

.sidebar-title {
  margin: 0;
  padding: 0;
  color: inherit;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  transition: all 0.3s ease;
}

.sidebar-logo-container.sidebar-variant .sidebar-title {
  font-size: var(--logo-title-font-size, 16px);
}

.sidebar-logo-container.login-variant .sidebar-title {
  color: var(--zx-semantic-text-primary);
}

.sidebar-title:hover {
  transform: scale(1.02);
}

/* collapse 状态下的特殊样式 */
.sidebar-logo-container.is-collapsed .sidebar-logo {
  margin-right: 0;
}
</style>
