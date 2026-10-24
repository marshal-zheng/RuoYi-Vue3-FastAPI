<template>
  <footer v-if="visible" class="copyright">
    <span>{{ content }}</span>
  </footer>
</template>

<script setup>
import useSettingsStore from '@/store/modules/settings';

const settingsStore = useSettingsStore();

const visible = computed(() => settingsStore.footerVisible);
const content = computed(() => settingsStore.footerContent);
</script>

<style scoped>
.copyright {
  flex: 0 0 auto;
  padding: 10px 20px;
  text-align: right;
  background-color: var(--zx-semantic-surface-header-fill);
  color: var(--zx-semantic-surface-header-on-text-secondary);
  font-size: 14px;
  border-top: var(--zx-semantic-surface-header-edge);
  z-index: 999;
}
</style>
