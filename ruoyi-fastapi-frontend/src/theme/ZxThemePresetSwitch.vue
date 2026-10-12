<template>
  <div class="zx-theme-controls">
    <el-dropdown trigger="click" placement="bottom-end" @command="onSelect">
      <button
        type="button"
        class="zx-theme-preset-switch"
        data-testid="zx-theme-preset-switch"
        :aria-label="`ZXUI 主题：${current.label}`"
        :aria-busy="zxThemePreferencePending"
      >
        <span class="zx-theme-preset-switch__swatch" :style="{ background: current.swatch }" />
        <span class="zx-theme-preset-switch__label">{{ current.label }}</span>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="choice in ZX_THEME_PACKAGE_CHOICES"
            :key="choice.id"
            :command="choice.id"
            :data-zx-theme-preset="choice.id"
          >
            <span class="zx-theme-preset-switch__item">
              <span class="zx-theme-preset-switch__swatch" :style="{ background: choice.swatch }" />
              <span>{{ choice.label }}</span>
            </span>
          </el-dropdown-item>
          <el-dropdown-item
            v-for="(choice, index) in densityChoices"
            :key="choice.value"
            :command="{ density: choice.value }"
            :divided="index === 0"
            :disabled="zxThemePreference.density === choice.value"
          >
            界面密度：{{ choice.label }}
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
      <ZxIcon :icon="settingsStore.isDark ? 'Sunny' : 'Moon'" :size="16" />
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
  border-radius: 6px;
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
  padding: 0 10px 0 8px;
}

.zx-theme-mode-switch {
  width: 32px;
  padding: 0;
}

.zx-theme-preset-switch__swatch {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  flex: none;
}

.zx-theme-preset-switch__label {
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
}

.zx-theme-preset-switch__item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
@media (max-width: 640px) {
  .zx-theme-preset-switch__label {
    display: none;
  }
  .zx-theme-preset-switch {
    width: 32px;
    padding: 0;
  }
}
</style>
