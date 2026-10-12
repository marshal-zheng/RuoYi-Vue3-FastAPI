<template>
  <div class="flex flex-col items-center w-full h-full py-2">
    <!-- 顶部装饰线 -->
    <div class="dock-decoration-line mb-4"></div>

    <!-- 功能按钮组 -->
    <div class="flex flex-col items-center gap-5 w-full">
      <button
        type="button"
        class="collapse-btn relative w-[60px] h-10 flex items-center justify-center cursor-pointer transition-all duration-300 ease-out overflow-hidden text-zx-accent-on-surface/80 hover:text-zx-accent-on-surface"
        @click="$emit('toggle-all')"
      >
        <div
          class="absolute inset-0 bg-gradient-to-r from-transparent via-zx-accent/8 to-transparent"
        ></div>
        <div class="absolute inset-0 collapse-glow opacity-0 transition-opacity duration-300"></div>
        <div class="absolute inset-0 collapse-shine opacity-0"></div>
        <div class="relative z-10 flex items-center justify-center gap-1.5">
          <zx-icon
            :name="allCollapsed ? 'Expand' : 'Fold'"
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
            class="absolute inset-0 bg-gradient-to-b from-zx-surface-card-fill/95 to-zx-surface-card-fill/98 group-hover:from-zx-surface-panel-fill/98 group-hover:to-zx-surface-card-fill"
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
            class="absolute inset-0 bg-gradient-to-b from-zx-accent/20 to-zx-accent/5"
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
            class="absolute top-1 right-1 w-4 h-4 rounded-full bg-zx-surface-field-fill/70 flex items-center justify-center z-20 border border-zx-action-focus-ring/30"
          >
            <zx-icon name="Lock" class="text-[10px] text-zx-accent-on-surface/80" />
          </div>

          <!-- 徽章 -->
          <span
            v-if="badges[item.key] && !isItemDisabled(item.key)"
            class="absolute -top-[1.5px] -right-[1.2px] min-w-[20px] h-5 px-1.5 rounded-full bg-gradient-to-br from-red-500 to-red-600 text-white text-[11px] font-extrabold inline-flex items-center justify-center z-20 border-2 border-zx-border-default/90 shadow-[0_3px_10px_rgba(239,68,68,0.5),0_0_16px_rgba(239,68,68,0.35)]"
          >
            {{ badges[item.key] }}
          </span>

          <!-- 激活指示条 - 增强版 -->
          <span
            v-if="activeKeys.includes(item.key)"
            class="absolute -left-px top-1/2 -translate-y-1/2 w-1 h-10 rounded-r-md bg-gradient-to-b from-zx-accent via-zx-accent to-zx-accent indicator-glow-enhanced"
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
    return 'dock-btn--disabled border-zx-action-focus-ring/25 text-zx-text-primary cursor-not-allowed';
  }
  if (props.activeKeys.includes(key)) {
    return 'dock-btn--active border-zx-action-focus-ring/50 text-zx-accent-on-surface shadow-cyan cursor-pointer';
  }
  return 'border-zx-action-focus-ring/20 text-zx-text-secondary shadow-default hover:border-zx-action-focus-ring/40 hover:text-zx-text-primary hover:-translate-y-1 hover:scale-105 cursor-pointer';
}
</script>

<style scoped>
/* 装饰线 */
.dock-decoration-line {
  width: 32px;
  height: 2px;
  border-radius: 1px;
  background: linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent) 50%, transparent 100%);
  flex-shrink: 0;
}

/* 收起/展开按钮样式 */
.collapse-btn {
  &:hover {
    transform: scale(1.05);
    text-shadow: 0 0 12px color-mix(in srgb, var(--zx-semantic-accent-base) 80%, transparent);

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
      filter: drop-shadow(0 0 8px color-mix(in srgb, var(--zx-semantic-accent-base) 80%, transparent));
      transform: rotate(180deg);
    }
  }

  &:active {
    transform: scale(0.98);
  }
}

.collapse-glow {
  background: radial-gradient(ellipse at center, color-mix(in srgb, var(--zx-semantic-accent-base) 18%, transparent) 0%, transparent 70%);
}

.collapse-shine {
  background: linear-gradient(
    90deg,
    transparent 0%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 20%, transparent) 30%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 35%, transparent) 50%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 20%, transparent) 70%,
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
  text-shadow: 0 0 8px color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent);
}

.collapse-icon {
  filter: drop-shadow(0 0 6px color-mix(in srgb, var(--zx-semantic-accent-base) 50%, transparent));
  transition: all 0.3s ease-out;
}

/* 功能按钮默认阴影 */
.shadow-default {
  box-shadow: var(--zx-semantic-surface-card-depth);
}

.dock-btn.shadow-default:hover {
  box-shadow: var(--zx-semantic-surface-card-depth);
}

/* 激活状态阴影 */
.shadow-cyan {
  box-shadow: var(--zx-semantic-surface-card-depth);
}

.dock-btn--active:hover {
  box-shadow: var(--zx-semantic-surface-card-depth);
}

/* 径向渐变背景 */
.bg-radial-cyan-top {
  background: radial-gradient(
    ellipse 80% 50% at 50% 0%,
    color-mix(in srgb, var(--zx-semantic-accent-base) 12%, transparent) 0%,
    transparent 60%
  );
}

/* 图标发光 */
.icon-glow {
  filter: drop-shadow(0 0 6px color-mix(in srgb, var(--zx-semantic-accent-base) 60%, transparent));
}

/* 文字发光 */
.text-glow {
  text-shadow: 0 0 12px color-mix(in srgb, var(--zx-semantic-accent-base) 60%, transparent);
}

/* 指示条发光 */
.indicator-glow {
  box-shadow:
    0 0 8px color-mix(in srgb, var(--zx-semantic-accent-base) 80%, transparent),
    0 0 16px color-mix(in srgb, var(--zx-semantic-accent-base) 40%, transparent);
}

/* 指示条增强发光 */
.indicator-glow-enhanced {
  box-shadow:
    0 0 12px color-mix(in srgb, var(--zx-semantic-accent-base) 90%, transparent),
    0 0 24px color-mix(in srgb, var(--zx-semantic-accent-base) 60%, transparent),
    0 0 36px color-mix(in srgb, var(--zx-semantic-accent-base) 30%, transparent),
    inset 0 0 4px var(--zx-semantic-border-subtle);
}

/* 禁用状态 */
.dock-btn--disabled {
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--zx-semantic-border-default) 25%, transparent),
    inset 0 1px 0 var(--zx-semantic-border-subtle);
  transform: none !important;
  border-color: rgba(94, 234, 212, 0.35) !important;
}

.dock-btn--disabled:hover {
  transform: none !important;
}

.disabled-overlay {
  opacity: 0.78 !important;
  background: linear-gradient(180deg, var(--zx-semantic-surface-panel-fill) 0%, var(--zx-semantic-surface-card-fill) 100%);
  box-shadow: inset 0 0 24px color-mix(in srgb, var(--zx-semantic-border-default) 8%, transparent);
}

.disabled-content {
  opacity: 1 !important;
  color: var(--zx-semantic-text-disabled);
  text-shadow: 0 0 8px color-mix(in srgb, var(--zx-semantic-border-default) 40%, transparent);
}

.disabled-content zx-icon {
  color: var(--zx-semantic-text-disabled);
  filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.35));
}

.disabled-content span {
  color: var(--zx-semantic-text-primary) !important;
}
</style>
