<template>
  <div class="xflow-control" :class="className" :style="style">
    <slot></slot>
  </div>
</template>

<script setup>
// Props 定义
defineProps({
  className: {
    type: String,
    default: '',
  },
  style: {
    type: Object,
    default: () => ({}),
  },
});
</script>

<style scoped>
.xflow-control {
  position: absolute;
  z-index: 10;
  padding: 8px;
  background: var(--zx-semantic-surface-overlay-fill);
  border-radius: 4px;
  box-shadow: var(--zx-semantic-surface-overlay-depth);
}
</style>
