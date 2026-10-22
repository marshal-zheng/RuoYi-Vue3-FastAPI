<template>
  <button
    type="button"
    class="navigation-toggle"
    :class="{ 'has-brand': $slots.brand && !isActive }"
    :aria-label="isActive ? '收起导航' : '展开导航'"
    :title="isActive ? '收起导航' : '展开导航'"
    :aria-expanded="isActive"
    aria-controls="app-sidebar"
    @click="toggleClick"
  >
    <span v-if="$slots.brand && !isActive" class="navigation-toggle-brand" aria-hidden="true">
      <slot name="brand" />
    </span>
    <ZxIcon
      :icon="navigationIcons.toggle"
      :class="{ 'is-active': isActive }"
      class="hamburger"
      size="var(--app-nav-icon-size)"
      aria-hidden="true"
    />
  </button>
</template>

<script setup>
import { ZxIcon } from '@zxio/zxui/core';
import { navigationIcons } from '@/icons/navigation';

defineProps({
  isActive: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['toggleClick']);
const toggleClick = () => {
  emit('toggleClick');
};
</script>

<style scoped>
.navigation-toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--app-nav-control-size);
  height: var(--app-nav-control-size);
  padding: 0;
  border: 0;
  border-radius: var(--app-nav-control-radius);
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.navigation-toggle:hover {
  background: var(--app-nav-hover-fill);
}

.navigation-toggle:focus-visible {
  outline: var(--app-nav-focus-width) solid var(--app-nav-focus);
  outline-offset: calc(-1 * var(--app-nav-focus-width));
}

.hamburger {
  display: inline-block;
  vertical-align: middle;
  width: var(--app-nav-icon-size);
  height: var(--app-nav-icon-size);
  transform: rotate(180deg);
  transition: transform var(--app-nav-motion-control) var(--app-nav-ease-control);
}

.hamburger.is-active {
  transform: rotate(0deg);
}

.navigation-toggle-brand {
  position: absolute;
  inset: var(--app-nav-brand-inset);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  opacity: 1;
  transition: opacity var(--app-nav-motion-panel) var(--app-nav-ease-panel);
}

.has-brand .hamburger {
  opacity: 0;
  transition:
    opacity var(--app-nav-motion-panel) var(--app-nav-ease-panel),
    transform var(--app-nav-motion-control) var(--app-nav-ease-control);
}

.has-brand:is(:hover, :focus-visible) .navigation-toggle-brand {
  opacity: 0;
}

.has-brand:is(:hover, :focus-visible) .hamburger {
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .hamburger,
  .navigation-toggle-brand,
  .has-brand .hamburger {
    transition: none;
  }
}
</style>
