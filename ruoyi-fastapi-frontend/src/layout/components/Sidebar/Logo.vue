<template>
  <div class="sidebar-logo-container" :class="`${variant}-variant`">
    <router-link class="sidebar-brand" to="/" :aria-label="title" :title="title">
      <img v-if="logo" :src="logo" class="sidebar-logo" alt="" />
      <component
        :is="variant === 'login' ? 'h1' : 'span'"
        v-if="!collapse || !logo"
        class="sidebar-title"
      >
        {{ collapse ? compactTitle : title }}
      </component>
    </router-link>
  </div>
</template>

<script setup>
import logoImg from '@/assets/logo/logo.png';
import defaultSettings from '@/settings';

defineProps({
  collapse: { type: Boolean, required: true },
  variant: {
    type: String,
    default: 'sidebar',
    validator: (value) => ['sidebar', 'login'].includes(value),
  },
});

const title = defaultSettings.title || import.meta.env.VITE_APP_TITLE;
const compactTitle = Array.from(title || '')
  .slice(0, 2)
  .join('');
const logo = (defaultSettings.showLogoImage ?? true) ? logoImg : null;
</script>

<style scoped>
.sidebar-logo-container {
  flex: 1;
  min-width: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--app-nav-icon-gap);
  min-width: 0;
  color: inherit;
}

.sidebar-brand:focus-visible {
  outline: var(--app-nav-focus-width) solid var(--app-nav-focus);
  outline-offset: var(--app-nav-space);
}

.sidebar-logo {
  width: var(--app-nav-brand-size);
  height: var(--app-nav-brand-size);
  flex-shrink: 0;
}

.sidebar-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--app-nav-brand-font-size);
  font-weight: var(--app-nav-brand-font-weight);
  line-height: var(--app-nav-brand-line-height);
}

.login-variant .sidebar-brand {
  gap: 12px;
  justify-content: center;
  color: var(--zx-semantic-text-primary);
}

.login-variant .sidebar-logo {
  width: 48px;
  height: 48px;
}

.login-variant .sidebar-title {
  font-size: 24px;
  line-height: 32px;
  white-space: normal;
  text-align: center;
}
</style>
