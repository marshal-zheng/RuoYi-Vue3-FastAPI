<template>
  <teleport to="body">
    <div
      v-if="!collapsed"
      class="floating-panel fixed z-50 rounded-lg overflow-hidden transition-all duration-300 ease-in-out"
      :class="panelClass"
      :style="panelStyle"
      @mousedown="handleMouseDown"
    >
      <!-- Header -->
      <div
        class="flex items-center justify-between px-4 py-3 border-b cursor-move"
        :class="headerClass"
        :style="headerStyle"
      >
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <slot name="header">
            <span class="text-sm font-semibold truncate" :class="titleClass">{{ title }}</span>
          </slot>
        </div>
        <div class="flex items-center gap-2 ml-2">
          <slot name="actions"></slot>
          <button
            @click="handleCollapse"
            class="p-1 rounded transition-colors"
            :class="iconBtnClass"
            title="最小化"
          >
            <el-icon :class="iconClass"><Minus /></el-icon>
          </button>
          <button
            v-if="closable"
            @click="handleClose"
            class="p-1 rounded transition-colors"
            :class="closeBtnClass"
            title="关闭"
          >
            <el-icon :class="closeIconClass"><Close /></el-icon>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="overflow-auto" :style="contentStyle">
        <div class="p-4">
          <slot></slot>
        </div>
      </div>

      <!-- Resize Handle -->
      <div
        v-if="resizable"
        class="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize opacity-50 hover:opacity-100 transition-opacity"
        @mousedown.stop="handleResizeStart"
      >
        <svg class="w-full h-full text-gray-400" viewBox="0 0 16 16" fill="currentColor">
          <path d="M16 16V14L14 16H16ZM16 11V9L9 16H11L16 11ZM16 6V4L4 16H6L16 6Z" />
        </svg>
      </div>
    </div>

    <!-- Collapsed State -->
    <div
      v-else
      class="floating-panel-collapsed fixed z-50 rounded-full cursor-pointer transition-all duration-300"
      :class="collapsedClass"
      :style="collapsedStyle"
      @click="handleExpand"
      :title="title"
    >
      <div class="flex items-center justify-center w-full h-full">
        <el-icon :class="collapseIconClass"><Expand /></el-icon>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { Close, Minus, Expand } from '@element-plus/icons-vue';

const props = defineProps({
  title: {
    type: String,
    default: '面板',
  },
  position: {
    type: Object,
    default: () => ({ top: '100px', right: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '400px', maxHeight: '500px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: false,
  },
  closable: {
    type: Boolean,
    default: false,
  },
  resizable: {
    type: Boolean,
    default: true,
  },
  draggable: {
    type: Boolean,
    default: true,
  },
  theme: {
    type: String,
    default: 'auto', // auto | light | dark
  },
  visible: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['close', 'collapse', 'expand']);

const collapsed = ref(props.defaultCollapsed);
const currentPosition = ref({ ...props.position });
const currentSize = ref({ ...props.size });
const isDragging = ref(false);
const isResizing = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 });

watch(
  () => props.visible,
  (newVal) => {
    if (!newVal) {
      collapsed.value = true;
    }
  }
);

const panelTokens = computed(() =>
  isDark.value
    ? {
        bg: 'rgba(15,23,42,0.95)',
        border: '1px solid rgba(51,65,85,0.7)',
        headerBg: 'rgba(30,41,59,0.85)',
        headerBorder: '1px solid rgba(51,65,85,0.7)',
        shadow: '0 18px 38px -18px rgba(0,0,0,0.65)',
        text: '#e2e8f0',
      }
    : {
        bg: '#ffffff',
        border: '1px solid #e5e7eb',
        headerBg: '#f8fafc',
        headerBorder: '1px solid #e5e7eb',
        shadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
        text: '#0f172a',
      }
);

const panelStyle = computed(() => {
  const style = {
    ...currentPosition.value,
    ...currentSize.value,
    backgroundColor: panelTokens.value.bg,
    border: panelTokens.value.border,
    boxShadow: panelTokens.value.shadow,
    backdropFilter: isDark.value ? 'blur(8px)' : 'none',
    color: panelTokens.value.text,
  };

  if (isDragging.value) {
    style.transition = 'none';
  }

  return style;
});

const contentStyle = computed(() => {
  return {
    maxHeight: currentSize.value.maxHeight || '500px',
    backgroundColor: panelTokens.value.bg,
  };
});

const headerStyle = computed(() => ({
  backgroundColor: panelTokens.value.headerBg,
  borderColor: panelTokens.value.headerBorder.replace('1px solid ', ''),
  color: panelTokens.value.text,
}));

const isDark = computed(() => {
  if (props.theme === 'dark') return true;
  if (props.theme === 'light') return false;
  // auto: follow simulation shell or body dark class
  const hasSimulationShell = document.querySelector('.simulation-dark');
  const bodyDark = document.body.classList.contains('dark');
  return Boolean(hasSimulationShell || bodyDark);
});

const panelClass = computed(() =>
  isDark.value
    ? 'bg-slate-900/95 border border-slate-700/70 shadow-[0_18px_38px_-18px_rgba(0,0,0,0.65)] backdrop-blur'
    : 'bg-white border border-gray-200 shadow-2xl'
);

const headerClass = computed(() =>
  isDark.value
    ? 'bg-slate-800/70 border-slate-700/70 text-slate-100'
    : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-gray-200 text-gray-800'
);

const titleClass = computed(() => (isDark.value ? 'text-slate-100' : 'text-gray-800'));
const iconClass = computed(() => (isDark.value ? 'text-slate-200' : 'text-gray-600'));
const closeIconClass = computed(() =>
  isDark.value ? 'text-slate-200 hover:text-red-400' : 'text-gray-600 hover:text-red-600'
);
const iconBtnClass = computed(() =>
  isDark.value ? 'hover:bg-slate-700/60 text-slate-100' : 'hover:bg-white/50'
);
const closeBtnClass = computed(() =>
  isDark.value ? 'hover:bg-red-500/10' : 'hover:bg-red-50'
);

const collapsedClass = computed(() =>
  isDark.value
    ? 'bg-slate-800/90 border border-slate-700/80 shadow-lg hover:shadow-xl'
    : 'bg-white border border-gray-200 shadow-lg hover:shadow-xl'
);

const collapseIconClass = computed(() => (isDark.value ? 'text-slate-100 text-xl' : 'text-blue-600 text-xl'));

const collapsedStyle = computed(() => {
  return {
    ...currentPosition.value,
    ...props.collapsedSize,
  };
});

const handleCollapse = () => {
  collapsed.value = true;
  emit('collapse');
};

const handleExpand = () => {
  collapsed.value = false;
  emit('expand');
};

const handleClose = () => {
  emit('close');
};

const handleMouseDown = (e) => {
  if (!props.draggable) return;
  if (e.target.closest('.floating-panel > div:first-child') === null) return;

  isDragging.value = true;
  dragStart.value = {
    x: e.clientX - parseInt(currentPosition.value.left || currentPosition.value.right || 0),
    y: e.clientY - parseInt(currentPosition.value.top || currentPosition.value.bottom || 0),
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

const handleMouseMove = (e) => {
  if (!isDragging.value && !isResizing.value) return;

  if (isDragging.value) {
    const newLeft = e.clientX - dragStart.value.x;
    const newTop = e.clientY - dragStart.value.y;

    currentPosition.value = {
      left: `${Math.max(0, Math.min(newLeft, window.innerWidth - 400))}px`,
      top: `${Math.max(0, Math.min(newTop, window.innerHeight - 100))}px`,
    };
  } else if (isResizing.value) {
    const deltaX = e.clientX - resizeStart.value.x;
    const deltaY = e.clientY - resizeStart.value.y;

    const newWidth = Math.max(300, resizeStart.value.width + deltaX);
    const newHeight = Math.max(200, resizeStart.value.height + deltaY);

    currentSize.value = {
      width: `${newWidth}px`,
      maxHeight: `${newHeight}px`,
    };
  }
};

const handleMouseUp = () => {
  isDragging.value = false;
  isResizing.value = false;
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
};

const handleResizeStart = (e) => {
  if (!props.resizable) return;

  isResizing.value = true;
  resizeStart.value = {
    x: e.clientX,
    y: e.clientY,
    width: parseInt(currentSize.value.width),
    height: parseInt(currentSize.value.maxHeight),
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

// 暴露方法给外部调用
defineExpose({
  collapse: handleCollapse,
  expand: handleExpand,
});
</script>

<style scoped>
.floating-panel {
  user-select: none;
}

.floating-panel:hover {
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
</style>
