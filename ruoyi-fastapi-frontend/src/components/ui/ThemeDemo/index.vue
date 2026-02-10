<template>
  <div class="app-container"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Plus } from '@element-plus/icons-vue';

// Element Plus 表单数据
const form = ref({
  username: '',
  email: '',
  status: '',
  description: '',
});

// Tailwind 表单数据
const tailwindForm = ref({
  username: '',
  email: '',
  status: '',
  description: '',
});

// 主题切换
const isDark = ref(false);

const toggleTheme = (value) => {
  const html = document.documentElement;
  if (value) {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
};

// 初始化主题
onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark');
});
</script>

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
