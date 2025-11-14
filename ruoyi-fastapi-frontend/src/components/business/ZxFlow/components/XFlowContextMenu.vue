<template>
  <teleport to="body">
    <div
      v-show="menu.visible"
      class="xflow-context-menu"
      :style="{
        left: menu.x + 'px',
        top: menu.y + 'px'
      }"
      @click.stop
    >
      <div
        v-for="(item, index) in menu.items"
        :key="item.id || index"
        :class="[
          'menu-item',
          {
            'menu-item--disabled': item.disabled,
            'menu-item--danger': item.danger,
            'menu-item--divider': item.type === 'divider'
          }
        ]"
        @click="$emit('menu-click', item)"
      >
        <template v-if="item.type !== 'divider'">
          <el-icon v-if="item.icon" class="menu-item__icon">
            <component :is="getIconComponent(item.icon)" />
          </el-icon>
          <span class="menu-item__label">{{ item.label }}</span>
          <span v-if="item.shortcut" class="menu-item__shortcut">{{ item.shortcut }}</span>
        </template>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed } from 'vue'
import {
  Select,
  DocumentCopy,
  FullScreen,
  ZoomIn,
  Delete,
  Lock,
  Unlock,
  Edit,
  Plus
} from '@element-plus/icons-vue'

const props = defineProps({
  contextMenu: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['menu-click'])

// 兼容父组件传入的是 ref 或 普通对象
const menu = computed(() => {
  const cm = props.contextMenu
  // 如果是 ref，取其 value；否则直接返回对象
  return cm && typeof cm === 'object' && 'value' in cm ? cm.value || {} : cm || {}
})

// 图标组件映射
const iconComponents = {
  Select,
  DocumentCopy,
  FullScreen,
  ZoomIn,
  Delete,
  Lock,
  Unlock,
  Edit,
  Plus
}

const getIconComponent = (iconName) => {
  return iconComponents[iconName] || null
}
</script>

<style scoped>
/* 深色主题支持 */
@media (prefers-color-scheme: dark) {
  .xflow-context-menu {
    color: #e4e7ed;
    background: #2d2d2d;
    border-color: #4c4d4f;
  }

  .menu-item:hover:not(.menu-item--disabled, .menu-item--divider) {
    background-color: #3a3a3a;
  }

  .menu-item--disabled {
    color: #6c6e72;
  }

  .menu-item--divider {
    background-color: #4c4d4f;
  }

  .menu-item__shortcut {
    color: #909399;
  }
}

.xflow-context-menu {
  position: fixed;
  z-index: 9999;
  max-width: 240px;
  min-width: 160px;
  padding: 4px 0;
  font-size: 14px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
  user-select: none;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  gap: 8px;
}

.menu-item:hover:not(.menu-item--disabled, .menu-item--divider) {
  background-color: #f5f7fa;
}

.menu-item--disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}

.menu-item--danger {
  color: #f56c6c;
}

.menu-item--danger:hover:not(.menu-item--disabled) {
  color: #f56c6c;
  background-color: #fef0f0;
}

.menu-item--divider {
  height: 1px;
  padding: 0;
  margin: 4px 8px;
  cursor: default;
  background-color: #e4e7ed;
}

.menu-item--divider:hover {
  background-color: #e4e7ed;
}

.menu-item__icon {
  flex-shrink: 0;
  font-size: 16px;
}

.menu-item__label {
  flex: 1;
  white-space: nowrap;
}

.menu-item__shortcut {
  font-family: 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', monospace;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}
</style>
