<template>
  <div class="app-container">
    <div class="page-header">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        CSS-First 主题系统示例
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        展示基于 CSS 变量的统一主题系统，支持 Tailwind v4 + Element Plus 无缝集成
      </p>
    </div>

    <!-- 主题色彩系统 -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">主题色彩系统</h2>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div class="el-card p-4">
          <div class="w-full h-12 bg-primary-500 rounded mb-2"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Primary</p>
          <code class="text-xs text-gray-500">bg-primary-500</code>
        </div>
        <div class="el-card p-4">
          <div class="w-full h-12 bg-success-500 rounded mb-2"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Success</p>
          <code class="text-xs text-gray-500">bg-success-500</code>
        </div>
        <div class="el-card p-4">
          <div class="w-full h-12 bg-warning-500 rounded mb-2"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Warning</p>
          <code class="text-xs text-gray-500">bg-warning-500</code>
        </div>
        <div class="el-card p-4">
          <div class="w-full h-12 bg-danger-500 rounded mb-2"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Danger</p>
          <code class="text-xs text-gray-500">bg-danger-500</code>
        </div>
        <div class="theme-card p-4">
          <div class="w-full h-12 bg-info-500 rounded mb-2"></div>
          <p class="text-sm text-gray-600 dark:text-gray-400">Info</p>
          <code class="text-xs text-gray-500">bg-info-500</code>
        </div>
      </div>
      
      <!-- 色阶展示 -->
      <div class="el-card p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Primary 色阶</h3>
        <div class="flex flex-wrap gap-2">
          <div v-for="shade in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]" :key="shade" class="text-center">
            <div :class="`w-16 h-16 bg-primary-${shade} rounded mb-1`"></div>
            <code class="text-xs text-gray-500">{{ shade }}</code>
          </div>
        </div>
      </div>
    </section>

    <!-- 按钮组件展示 -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">按钮组件</h2>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Element Plus 按钮 -->
        <div class="el-card p-6">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Element Plus 按钮</h3>
          <div class="space-y-4">
            <div class="flex flex-wrap gap-2">
              <el-button type="primary">Primary</el-button>
              <el-button type="success">Success</el-button>
              <el-button type="warning">Warning</el-button>
              <el-button type="danger">Danger</el-button>
              <el-button type="info">Info</el-button>
            </div>
            <div class="flex flex-wrap gap-2">
              <el-button type="primary" plain>Plain</el-button>
              <el-button type="primary" round>Round</el-button>
              <el-button type="primary" circle>
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- Tailwind 工具类按钮 -->
        <div class="el-card p-6">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Tailwind 工具类按钮</h3>
          <div class="space-y-4">
            <div class="flex flex-wrap gap-2">
              <button class="el-button el-button--primary">Primary</button>
              <button class="el-button el-button--success">Success</button>
              <button class="el-button el-button--warning">Warning</button>
              <button class="el-button el-button--danger">Danger</button>
              <button class="el-button el-button--info">Info</button>
            </div>
            <div class="flex flex-wrap gap-2">
              <button class="px-4 py-2 border border-primary-500 text-primary-500 rounded hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors">
                Plain
              </button>
              <button class="px-4 py-2 bg-primary-500 text-white rounded-full hover:bg-primary-600 transition-colors">
                Round
              </button>
              <button class="w-10 h-10 bg-primary-500 text-white rounded-full hover:bg-primary-600 transition-colors flex items-center justify-center">
                +
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 表单组件展示 -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">表单组件</h2>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Element Plus 表单 -->
        <div class="el-card p-6">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Element Plus 表单</h3>
          <el-form :model="form" label-width="80px">
            <el-form-item label="用户名">
              <el-input v-model="form.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="请输入邮箱" type="email" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="form.status" placeholder="请选择状态">
                <el-option label="启用" value="1" />
                <el-option label="禁用" value="0" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" placeholder="请输入描述" />
            </el-form-item>
          </el-form>
        </div>

        <!-- Tailwind 工具类表单 -->
        <div class="el-card p-6">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Tailwind 工具类表单</h3>
          <form class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">用户名</label>
              <input
                v-model="tailwindForm.username"
                class="el-input w-full"
                placeholder="请输入用户名"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱</label>
              <input
                v-model="tailwindForm.email"
                class="el-input w-full"
                type="email"
                placeholder="请输入邮箱"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">状态</label>
              <select v-model="tailwindForm.status" class="el-input w-full">
                <option value="">请选择状态</option>
                <option value="1">启用</option>
                <option value="0">禁用</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
              <textarea
                v-model="tailwindForm.description"
                class="el-input w-full"
                rows="3"
                placeholder="请输入描述"
              ></textarea>
            </div>
          </form>
        </div>
      </div>
    </section>

    <!-- 卡片布局展示 -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">卡片布局</h2>

      <div class="grid md:grid-cols-3 gap-6">
        <!-- Element Plus 原生卡片 -->
        <el-card shadow="hover">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-lg font-medium">Element Plus 卡片</span>
              <el-button type="text" class="text-primary-500">更多</el-button>
            </div>
          </template>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            使用 Element Plus 原生 el-card 组件，自动适配主题色彩。
          </p>
          <div class="flex justify-end">
            <el-button type="primary" size="small">操作</el-button>
          </div>
        </el-card>

        <!-- Tailwind 工具类卡片 -->
        <div class="el-card p-0 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <span class="text-lg font-medium text-gray-900 dark:text-gray-100">Tailwind 工具类卡片</span>
            <button class="text-primary-500 hover:text-primary-600 transition-colors">更多</button>
          </div>
          <div class="p-6">
            <p class="text-gray-600 dark:text-gray-400 mb-4">
              使用 Tailwind 工具类构建，与 Element Plus 样式保持一致。
            </p>
            <div class="flex justify-end">
              <button class="px-3 py-1.5 bg-primary-500 text-white text-sm rounded hover:bg-primary-600 transition-colors">
                操作
              </button>
            </div>
          </div>
        </div>

        <!-- 渐变卡片示例 -->
        <div class="card-shadow bg-white dark:bg-gray-800 rounded overflow-hidden">
          <div class="px-6 py-4 bg-gradient-to-r from-primary-500 to-primary-600">
            <span class="text-lg font-medium text-white">渐变主题卡片</span>
          </div>
          <div class="p-6">
            <p class="text-gray-600 dark:text-gray-400 mb-4">
              展示主题色彩的渐变效果，支持暗黑模式自动适配。
            </p>
            <div class="flex justify-between items-center">
              <el-tag type="success" size="small">推荐</el-tag>
              <el-button type="primary" size="small">操作</el-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主题切换演示 -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">主题切换演示</h2>
      <div class="el-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-gray-900 dark:text-gray-100">
            当前主题：{{ isDark ? '暗黑模式' : '亮色模式' }}
          </span>
          <el-switch
            v-model="isDark"
            @change="toggleTheme"
            active-text="暗黑"
            inactive-text="亮色"
          />
        </div>
        <p class="text-gray-600 dark:text-gray-400 mb-4">
          切换主题可以看到所有组件都会自动适配新的主题色彩，这得益于统一的 CSS 变量系统。
        </p>
        
        <!-- 主题特性说明 -->
        <div class="grid md:grid-cols-2 gap-4 mt-6">
          <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded">
            <h4 class="font-medium text-gray-900 dark:text-gray-100 mb-2">CSS-First 架构</h4>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              所有主题变量定义在 theme-tokens.scss 中，通过 CSS 变量实现主题切换。
            </p>
          </div>
          <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded">
            <h4 class="font-medium text-gray-900 dark:text-gray-100 mb-2">无缝集成</h4>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Tailwind v4 + Element Plus 共享相同的主题变量，确保视觉一致性。
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
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

const toggleTheme = value => {
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
