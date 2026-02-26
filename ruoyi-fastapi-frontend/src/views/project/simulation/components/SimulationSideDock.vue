<template>
  <div class="flex flex-col items-center w-full h-full py-2">
    <!-- 顶部装饰线 -->
    <div class="dock-decoration-line mb-4"></div>

    <!-- 功能按钮组 -->
    <div class="flex flex-col items-center gap-5 w-full">
      <button
        type="button"
        class="collapse-btn relative w-[60px] h-10 flex items-center justify-center cursor-pointer transition-all duration-300 ease-out overflow-hidden text-cyan-400/80 hover:text-cyan-300"
        @click="$emit('toggle-all')"
      >
        <div
          class="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/8 to-transparent"
        ></div>
        <div class="absolute inset-0 collapse-glow opacity-0 transition-opacity duration-300"></div>
        <div class="absolute inset-0 collapse-shine opacity-0"></div>
        <div class="relative z-10 flex items-center justify-center gap-1.5">
          <zx-icon
            :name="allCollapsed ? 'ri:expand-left-right-line' : 'ri:contract-left-right-line'"
            class="text-[16px] transition-transform duration-300 collapse-icon"
          />
          <span class="text-[11px] font-bold tracking-widest collapse-text">
            {{ allCollapsed ? '展开' : '收起' }}
          </span>
        </div>
      </button>

      <el-tooltip
        v-for="item in items"
        :key="item.key"
        :content="getDisabledReason(item.key)"
        :disabled="!isItemDisabled(item.key)"
        placement="left"
        :show-after="200"
      >
        <button
          type="button"
          class="dock-btn group relative w-[60px] h-14 flex flex-col items-center justify-center rounded-xl transition-all duration-300 ease-out overflow-hidden border-[1.5px]"
          :class="getButtonClass(item.key)"
          :disabled="isItemDisabled(item.key)"
          @click="!isItemDisabled(item.key) && $emit('toggle', item.key)"
        >
          <!-- 背景渐变层 -->
          <div
            class="absolute inset-0 bg-gradient-to-b from-slate-800/95 to-slate-900/98 group-hover:from-slate-700/98 group-hover:to-slate-800"
            :class="{ 'disabled-overlay': isItemDisabled(item.key) }"
          ></div>

          <!-- 顶部光晕 -->
          <div
            v-if="!isItemDisabled(item.key)"
            class="absolute inset-0 bg-radial-cyan-top opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          ></div>

          <!-- 激活状态背景 -->
          <div
            v-if="activeKeys.includes(item.key)"
            class="absolute inset-0 bg-gradient-to-b from-cyan-400/20 to-cyan-400/5"
          ></div>

          <!-- 内容 -->
          <div
            class="relative z-10 flex flex-col items-center justify-center gap-1"
            :class="{ 'disabled-content': isItemDisabled(item.key) }"
          >
            <zx-icon
              :name="item.icon"
              class="text-[22px] transition-transform duration-200"
              :class="[
                activeKeys.includes(item.key) ? 'icon-glow' : '',
                !isItemDisabled(item.key) ? 'group-hover:scale-110' : '',
              ]"
            />
            <span
              class="text-[13px] font-bold leading-none tracking-wider"
              :class="activeKeys.includes(item.key) ? 'text-glow' : ''"
            >
              {{ item.label }}
            </span>
          </div>

          <!-- 禁用锁定图标 -->
          <div
            v-if="isItemDisabled(item.key)"
            class="absolute top-1 right-1 w-4 h-4 rounded-full bg-slate-600/70 flex items-center justify-center z-20 border border-cyan-300/30"
          >
            <zx-icon name="ri:lock-line" class="text-[10px] text-cyan-200/80" />
          </div>

          <!-- 徽章 -->
          <span
            v-if="badges[item.key] && !isItemDisabled(item.key)"
            class="absolute -top-[1.5px] -right-[1.2px] min-w-[20px] h-5 px-1.5 rounded-full bg-gradient-to-br from-red-500 to-red-600 text-white text-[11px] font-extrabold inline-flex items-center justify-center z-20 border-2 border-slate-900/90 shadow-[0_3px_10px_rgba(239,68,68,0.5),0_0_16px_rgba(239,68,68,0.35)]"
          >
            {{ badges[item.key] }}
          </span>

          <!-- 激活指示条 - 增强版 -->
          <span
            v-if="activeKeys.includes(item.key)"
            class="absolute -left-px top-1/2 -translate-y-1/2 w-1 h-10 rounded-r-md bg-gradient-to-b from-cyan-300 via-cyan-400 to-cyan-500 indicator-glow-enhanced"
          >
          </span>
        </button>
      </el-tooltip>
    </div>

    <!-- 底部装饰线 -->
    <div class="dock-decoration-line mt-auto"></div>
  </div>
</template>

<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  activeKeys: {
    type: Array,
    default: () => [],
  },
  badges: {
    type: Object,
    default: () => ({}),
  },
  allCollapsed: {
    type: Boolean,
    default: false,
  },
  // 禁用的按钮配置：{ fault: '请先启动仿真' }
  disabledItems: {
    type: Object,
    default: () => ({}),
  },
});
defineEmits(['toggle', 'toggle-all']);

function isItemDisabled(key) {
  return !!props.disabledItems[key];
}

function getDisabledReason(key) {
  return props.disabledItems[key] || '';
}

function getButtonClass(key) {
  if (isItemDisabled(key)) {
    return 'dock-btn--disabled border-cyan-300/25 text-slate-200 cursor-not-allowed';
  }
  if (props.activeKeys.includes(key)) {
    return 'dock-btn--active border-cyan-400/50 text-cyan-400 shadow-cyan cursor-pointer';
  }
  return 'border-cyan-400/20 text-slate-400 shadow-default hover:border-cyan-400/40 hover:text-slate-200 hover:-translate-y-1 hover:scale-105 cursor-pointer';
}
</script>

<style scoped>
/* 装饰线 */
.dock-decoration-line {
  width: 32px;
  height: 2px;
  border-radius: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(34, 211, 238, 0.4) 50%, transparent 100%);
  flex-shrink: 0;
}

/* 收起/展开按钮样式 */
.collapse-btn {
  &:hover {
    transform: scale(1.05);
    text-shadow: 0 0 12px rgba(34, 211, 238, 0.8);

    .collapse-glow {
      opacity: 1;
    }

    .collapse-shine {
      opacity: 1;
      animation: shine-sweep 1.2s ease-in-out;
    }

    .collapse-text {
      letter-spacing: 0.15em;
    }

    .collapse-icon {
      filter: drop-shadow(0 0 8px rgba(34, 211, 238, 0.8));
      transform: rotate(180deg);
    }
  }

  &:active {
    transform: scale(0.98);
  }
}

.collapse-glow {
  background: radial-gradient(ellipse at center, rgba(34, 211, 238, 0.18) 0%, transparent 70%);
}

.collapse-shine {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(34, 211, 238, 0.2) 30%,
    rgba(34, 211, 238, 0.35) 50%,
    rgba(34, 211, 238, 0.2) 70%,
    transparent 100%
  );
  transition: opacity 0.3s ease-out;
}

@keyframes shine-sweep {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.collapse-text {
  transition: letter-spacing 0.3s ease-out;
  text-shadow: 0 0 8px rgba(34, 211, 238, 0.4);
}

.collapse-icon {
  filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.5));
  transition: all 0.3s ease-out;
}

/* 功能按钮默认阴影 */
.shadow-default {
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.35),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
}

.dock-btn.shadow-default:hover {
  box-shadow:
    0 8px 24px rgba(34, 211, 238, 0.18),
    0 4px 12px rgba(0, 0, 0, 0.3),
    0 0 32px rgba(34, 211, 238, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.15);
}

/* 激活状态阴影 */
.shadow-cyan {
  box-shadow:
    0 6px 24px rgba(34, 211, 238, 0.3),
    0 2px 8px rgba(0, 0, 0, 0.25),
    0 0 40px rgba(34, 211, 238, 0.15),
    inset 0 1px 0 rgba(34, 211, 238, 0.2),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
}

.dock-btn--active:hover {
  box-shadow:
    0 8px 32px rgba(34, 211, 238, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.2),
    0 0 48px rgba(34, 211, 238, 0.2),
    inset 0 1px 0 rgba(34, 211, 238, 0.25),
    inset 0 -1px 0 rgba(0, 0, 0, 0.08);
}

/* 径向渐变背景 */
.bg-radial-cyan-top {
  background: radial-gradient(
    ellipse 80% 50% at 50% 0%,
    rgba(34, 211, 238, 0.12) 0%,
    transparent 60%
  );
}

/* 图标发光 */
.icon-glow {
  filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.6));
}

/* 文字发光 */
.text-glow {
  text-shadow: 0 0 12px rgba(34, 211, 238, 0.6);
}

/* 指示条发光 */
.indicator-glow {
  box-shadow:
    0 0 8px rgba(34, 211, 238, 0.8),
    0 0 16px rgba(34, 211, 238, 0.4);
}

/* 指示条增强发光 */
.indicator-glow-enhanced {
  box-shadow:
    0 0 12px rgba(34, 211, 238, 0.9),
    0 0 24px rgba(34, 211, 238, 0.6),
    0 0 36px rgba(34, 211, 238, 0.3),
    inset 0 0 4px rgba(255, 255, 255, 0.5);
}

/* 禁用状态 */
.dock-btn--disabled {
  box-shadow:
    0 0 0 1px rgba(148, 163, 184, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transform: none !important;
  border-color: rgba(94, 234, 212, 0.35) !important;
}

.dock-btn--disabled:hover {
  transform: none !important;
}

.disabled-overlay {
  opacity: 0.78 !important;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.92) 100%);
  box-shadow: inset 0 0 24px rgba(148, 163, 184, 0.08);
}

.disabled-content {
  opacity: 1 !important;
  color: #d7e3ff !important;
  text-shadow: 0 0 8px rgba(148, 163, 184, 0.4);
}

.disabled-content zx-icon {
  color: #c7d2fe !important;
  filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.35));
}

.disabled-content span {
  color: #e2e8f0 !important;
}
</style>
