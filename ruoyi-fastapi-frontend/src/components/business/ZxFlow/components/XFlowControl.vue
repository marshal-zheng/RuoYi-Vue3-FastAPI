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
    default: ''
  },
  style: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.xflow-control {
  position: absolute;
  z-index: 10;
  padding: 8px;
  background: rgb(255 255 255 / 90%);
  border-radius: 4px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 10%);
}
</style>
