<template>
  <div class="theme-demo theme-container">
    <div class="theme-page-header">
      <h1 class="text-2xl font-bold text-theme-primary-text mb-2">
        Tailwind CSS + Element Plus 主题融合示例
      </h1>
      <p class="text-theme-secondary-text">
        展示如何在项目中统一使用 Tailwind CSS 和 Element Plus 组件，保持主题一致性
      </p>
    </div>

    <!-- 颜色系统展示 -->
    <div class="theme-section">
      <h2 class="text-xl font-semibold text-theme-primary-text mb-4">颜色系统</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="theme-card p-4">
          <div class="w-full h-12 bg-primary-500 rounded mb-2"></div>
          <p class="text-sm text-theme-secondary-text">Primary</p>
          <code class="text-xs text-theme-placeholder">bg-primary-500</code>
        </div>
        <div class="theme-card p-4">
          <div class="w-full h-12 bg-success-500 rounded mb-2"></div>
          <p class="text-sm text-theme-secondary-text">Success</p>
          <code class="text-xs text-theme-placeholder">bg-success-500</code>
        </div>
        <div class="theme-card p-4">
          <div class="w-full h-12 bg-warning-500 rounded mb-2"></div>
          <p class="text-sm text-theme-secondary-text">Warning</p>
          <code class="text-xs text-theme-placeholder">bg-warning-500</code>
        </div>
        <div class="theme-card p-4">
          <div class="w-full h-12 bg-danger-500 rounded mb-2"></div>
          <p class="text-sm text-theme-secondary-text">Danger</p>
          <code class="text-xs text-theme-placeholder">bg-danger-500</code>
        </div>
      </div>
    </div>

    <!-- 按钮组件对比 -->
    <div class="theme-section">
      <h2 class="text-xl font-semibold text-theme-primary-text mb-4">按钮组件对比</h2>
      
      <div class="grid md:grid-cols-2 gap-6">
        <!-- Element Plus 按钮 -->
        <div class="theme-card p-6">
          <h3 class="text-lg font-medium text-theme-primary-text mb-4">Element Plus 按钮</h3>
          <div class="space-y-3">
            <div class="flex flex-wrap gap-2">
              <el-button type="primary">Primary</el-button>
              <el-button type="success">Success</el-button>
              <el-button type="warning">Warning</el-button>
              <el-button type="danger">Danger</el-button>
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

        <!-- Tailwind 样式按钮 -->
        <div class="theme-card p-6">
          <h3 class="text-lg font-medium text-theme-primary-text mb-4">Tailwind CSS 按钮</h3>
          <div class="space-y-3">
            <div class="flex flex-wrap gap-2">
              <button class="theme-button primary">Primary</button>
              <button class="theme-button success">Success</button>
              <button class="theme-button warning">Warning</button>
              <button class="theme-button danger">Danger</button>
            </div>
            <div class="flex flex-wrap gap-2">
              <button class="px-4 py-2 border border-primary-500 text-primary-500 rounded-base hover:bg-primary-50 transition-colors">
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
    </div>

    <!-- 表单组件对比 -->
    <div class="theme-section">
      <h2 class="text-xl font-semibold text-theme-primary-text mb-4">表单组件对比</h2>
      
      <div class="grid md:grid-cols-2 gap-6">
        <!-- Element Plus 表单 -->
        <div class="theme-card p-6">
          <h3 class="text-lg font-medium text-theme-primary-text mb-4">Element Plus 表单</h3>
          <el-form :model="form" label-width="80px">
            <el-form-item label="用户名">
              <el-input v-model="form.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="form.status" placeholder="请选择状态">
                <el-option label="启用" value="1" />
                <el-option label="禁用" value="0" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- Tailwind 样式表单 -->
        <div class="theme-card p-6">
          <h3 class="text-lg font-medium text-theme-primary-text mb-4">Tailwind CSS 表单</h3>
          <form class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-theme-secondary-text mb-1">用户名</label>
              <input 
                v-model="tailwindForm.username"
                class="theme-input w-full" 
                placeholder="请输入用户名"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-theme-secondary-text mb-1">邮箱</label>
              <input 
                v-model="tailwindForm.email"
                class="theme-input w-full" 
                placeholder="请输入邮箱"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-theme-secondary-text mb-1">状态</label>
              <select v-model="tailwindForm.status" class="theme-input w-full">
                <option value="">请选择状态</option>
                <option value="1">启用</option>
                <option value="0">禁用</option>
              </select>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 卡片布局示例 -->
    <div class="theme-section">
      <h2 class="text-xl font-semibold text-theme-primary-text mb-4">卡片布局示例</h2>
      
      <div class="grid md:grid-cols-3 gap-6">
        <!-- Element Plus 卡片 -->
        <el-card shadow="hover">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-lg font-medium">Element Plus 卡片</span>
              <el-button type="text" class="text-primary-500">更多</el-button>
            </div>
          </template>
          <p class="text-theme-secondary-text mb-4">
            使用 Element Plus 的 el-card 组件，具有内置的阴影效果和头部插槽。
          </p>
          <div class="flex justify-end">
            <el-button type="primary" size="small">操作</el-button>
          </div>
        </el-card>

        <!-- Tailwind 卡片 -->
        <div class="theme-card p-0 overflow-hidden">
          <div class="px-6 py-4 border-b border-theme-light flex justify-between items-center">
            <span class="text-lg font-medium text-theme-primary-text">Tailwind CSS 卡片</span>
            <button class="text-primary-500 hover:text-primary-600 transition-colors">更多</button>
          </div>
          <div class="p-6">
            <p class="text-theme-secondary-text mb-4">
              使用 Tailwind CSS 构建的卡片，通过工具类快速实现样式。
            </p>
            <div class="flex justify-end">
              <button class="px-3 py-1.5 bg-primary-500 text-white text-sm rounded-base hover:bg-primary-600 transition-colors">
                操作
              </button>
            </div>
          </div>
        </div>

        <!-- 混合使用示例 -->
        <div class="theme-card p-0 overflow-hidden">
          <div class="px-6 py-4 bg-gradient-to-r from-primary-500 to-primary-600">
            <span class="text-lg font-medium text-white">混合使用</span>
          </div>
          <div class="p-6">
            <p class="text-theme-secondary-text mb-4">
              结合两个框架的优势，Tailwind 布局 + Element Plus 组件。
            </p>
            <div class="flex justify-between items-center">
              <el-tag type="success" size="small">推荐</el-tag>
              <el-button type="primary" size="small">操作</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主题切换演示 -->
    <div class="theme-section">
      <h2 class="text-xl font-semibold text-theme-primary-text mb-4">主题切换演示</h2>
      <div class="theme-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-theme-primary-text">当前主题：{{ isDark ? '暗黑模式' : '亮色模式' }}</span>
          <el-switch 
            v-model="isDark"
            @change="toggleTheme"
            active-text="暗黑"
            inactive-text="亮色"
          />
        </div>
        <p class="text-theme-secondary-text">
          切换主题可以看到所有组件（包括 Tailwind 和 Element Plus）都会自动适配新的主题色彩。
          这得益于统一的 CSS 变量系统。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'

// 表单数据
const form = ref({
  username: '',
  email: '',
  status: ''
})

const tailwindForm = ref({
  username: '',
  email: '',
  status: ''
})

// 主题切换
const isDark = ref(false)

const toggleTheme = (value) => {
  const html = document.documentElement
  if (value) {
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
  }
}

// 初始化主题
onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
})
</script>

<style scoped>
/* 组件特定样式 */
.theme-demo {
  min-height: 100vh;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
