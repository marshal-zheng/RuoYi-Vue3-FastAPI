<template>
  <div class="zx-theme-controls">
    <el-dropdown
      trigger="click"
      placement="bottom-end"
      popper-class="zx-theme-preset-popper"
      @command="onSelect"
    >
      <button
        type="button"
        class="zx-theme-preset-switch"
        data-testid="zx-theme-preset-switch"
        :aria-label="`ZXUI 主题：${current.label}`"
        :aria-busy="zxThemePreferencePending"
      >
        <span class="zx-theme-preset-switch__swatch" :style="{ background: current.swatch }" />
        <span class="zx-theme-preset-switch__label">{{ current.label }}</span>
        <ZxIcon
          class="zx-theme-preset-switch__caret"
          :icon="navigationIcons.chevronDown"
          size="var(--app-nav-chevron-size)"
        />
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="choice in ZX_THEME_PACKAGE_CHOICES"
            :key="choice.id"
            :command="choice.id"
            :data-zx-theme-preset="choice.id"
          >
            <span class="zx-theme-preset-menu__item">
              <span class="zx-theme-preset-menu__swatch" :style="{ background: choice.swatch }" />
              <span class="zx-theme-preset-menu__label">{{ choice.label }}</span>
              <span v-if="choice.id === zxThemeId" class="zx-theme-preset-menu__state">启用中</span>
            </span>
          </el-dropdown-item>
          <el-dropdown-item
            v-for="(choice, index) in densityChoices"
            :key="choice.value"
            :command="{ density: choice.value }"
            :divided="index === 0"
          >
            <span class="zx-theme-preset-menu__item">
              <span class="zx-theme-preset-menu__label">界面密度：{{ choice.label }}</span>
              <span
                v-if="zxThemePreference.density === choice.value"
                class="zx-theme-preset-menu__state"
              >
                启用中
              </span>
            </span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <button
      type="button"
      class="zx-theme-mode-switch"
      data-testid="zx-theme-mode-switch"
      :aria-pressed="settingsStore.isDark"
      :aria-label="settingsStore.isDark ? '切换到浅色模式' : '切换到深色模式'"
      @click="onToggleMode"
    >
      <ZxIcon
        :icon="settingsStore.isDark ? navigationIcons.lightMode : navigationIcons.darkMode"
        size="var(--app-nav-action-icon-size)"
      />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import useSettingsStore from '@/store/modules/settings';
import {
  setZxThemePreference,
  zxThemeChoice,
  zxThemeId,
  zxThemePreference,
  zxThemePreferencePending,
  type ZxThemeDensity,
} from '@/theme/zx-theme-config';
import { ZX_THEME_PACKAGE_CHOICES } from '@/theme/zx-theme-packages';
import { navigationIcons } from '@/icons/navigation';

const settingsStore = useSettingsStore();
const current = computed(() => zxThemeChoice(zxThemeId.value));
const densityChoices: { label: string; value: ZxThemeDensity }[] = [
  { label: '紧凑', value: 'compact' },
  { label: '默认', value: 'default' },
  { label: '宽松', value: 'comfortable' },
];

function onSelect(command: string | { density: ZxThemeDensity }) {
  setZxThemePreference(typeof command === 'string' ? { themeId: command } : command);
}

function onToggleMode() {
  settingsStore.toggleTheme();
}
</script>

<style scoped>
.zx-theme-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

/* The switch sits on whatever surface hosts it (today the header bar), so it
   tints itself from that surface's own text colour instead of the page body. */
.zx-theme-preset-switch,
.zx-theme-mode-switch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 32px;
  border: 1px solid
    color-mix(in oklab, currentColor calc(var(--zx-semantic-border-current-tint) * 1%), transparent);
  border-radius: var(--zx-semantic-radius-control);
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.zx-theme-preset-switch:hover,
.zx-theme-mode-switch:hover {
  background: color-mix(
    in oklab,
    currentColor calc(var(--zx-semantic-fill-current-tint) * 1%),
    transparent
  );
}

.zx-theme-preset-switch {
  padding: 0 8px 0 6px;
}

.zx-theme-mode-switch {
  width: 32px;
  padding: 0;
}

.zx-theme-preset-switch__swatch,
.zx-theme-preset-menu__swatch {
  width: 24px;
  height: 24px;
  border-radius: var(--zx-semantic-radius-control);
  flex: none;
}

.zx-theme-preset-switch__label {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.zx-theme-preset-switch__caret {
  color: var(--zx-semantic-text-secondary);
}

@media (max-width: 640px) {
  .zx-theme-preset-switch__label,
  .zx-theme-preset-switch__caret {
    display: none;
  }
  .zx-theme-preset-switch {
    width: 32px;
    padding: 0;
  }
}
</style>

<style>
/* Geometry follows the docs theme dropdown. Fill, edge and depth stay on the
   Element Plus overlay tokens, so this only shapes the menu. */
.zx-theme-preset-popper.el-dropdown__popper {
  padding: 6px;
  border-radius: var(--zx-semantic-radius-surface);
}

.zx-theme-preset-popper .el-dropdown-menu {
  max-height: min(32rem, calc(100vh - 6rem));
  padding: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.zx-theme-preset-popper .el-dropdown-menu__item {
  padding: 0;
  border-radius: var(--zx-semantic-radius-control);
  line-height: 1.2;
}

.zx-theme-preset-popper .el-dropdown-menu__item:not(.is-disabled):hover,
.zx-theme-preset-popper .el-dropdown-menu__item:not(.is-disabled):focus {
  background-color: var(--zx-semantic-fill-hover);
  color: var(--zx-semantic-text-primary);
}

.zx-theme-preset-popper .zx-theme-preset-menu__item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 196px;
  padding: 10px 12px;
}

.zx-theme-preset-popper .zx-theme-preset-menu__swatch {
  width: 24px;
  height: 24px;
  border-radius: var(--zx-semantic-radius-control);
  flex: none;
}

.zx-theme-preset-popper .zx-theme-preset-menu__label {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--zx-semantic-text-primary);
}

.zx-theme-preset-popper .zx-theme-preset-menu__state {
  font-size: 11px;
  font-weight: 600;
  color: var(--zx-semantic-accent-base);
  white-space: nowrap;
}

.zx-theme-preset-popper .el-popper__arrow {
  display: none;
}
</style>
