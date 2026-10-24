<template>
  <div class="app-container"></div>
</template>

<style scoped>
/* 组件特定样式 */
.app-container {
  min-height: 100vh;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .grid.md\:grid-cols-5 {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid.md\:grid-cols-3 {
    grid-template-columns: 1fr;
  }
}

/* 确保色阶展示在小屏幕上的可读性 */
@media (max-width: 640px) {
  .flex.flex-wrap.gap-2 {
    justify-content: center;
  }
}
</style>
