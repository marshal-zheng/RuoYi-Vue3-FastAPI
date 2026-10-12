<template>
  <div
    class="flex items-center justify-between h-14 px-5 bg-zx-surface-canvas-fill border-b border-zx-border-default/50"
  >
    <!-- 左侧：返回和标题 -->
    <div class="flex items-center gap-3">
      <button
        aria-label="返回工程"
        class="flex items-center justify-center w-8 h-8 rounded-md bg-zx-surface-card-fill border border-zx-border-default/50 text-zx-text-secondary hover:text-zx-accent-on-surface hover:border-zx-action-focus-ring/50 hover:bg-zx-surface-field-fill transition-all duration-200"
        @click="$emit('back')"
      >
        <el-icon :size="16"><ArrowLeft /></el-icon>
      </button>
      <div class="flex items-center gap-2">
        <span class="text-base font-semibold text-zx-text-primary tracking-wide">仿真控制台</span>
        <span
          v-if="projectName"
          data-testid="simulation-header-project"
          class="max-w-56 truncate text-sm font-medium text-zx-accent-on-surface"
        >
          {{ projectName }}
        </span>
        <span
          class="px-2 py-0.5 text-xs font-medium rounded bg-zx-surface-card-fill text-zx-text-secondary border border-zx-border-default"
        >
          v1.0
        </span>
      </div>
    </div>

    <!-- 中间：控制按钮组 -->
    <div class="flex items-center gap-6">
      <div
        class="flex items-center gap-2 p-1 rounded-lg bg-zx-surface-card-fill/50 border border-zx-border-default/50"
      >
        <!-- 开始/暂停/继续 -->
        <template v-if="status === 'idle' || status === 'stopped'">
          <button
            data-testid="simulation-start-button"
            :disabled="readonly"
            :class="[
              'inline-flex items-center gap-2 h-8 px-4 rounded-md text-sm font-semibold transition-all duration-200 shadow-zx-surface-card-depth',
              readonly
                ? 'bg-zx-surface-card-fill text-zx-text-secondary cursor-not-allowed shadow-none'
                : 'bg-zx-accent text-zx-accent-on-fill hover:bg-zx-accent-tint-3 hover:text-zx-accent-on-fill-hover shadow-zx-surface-card-depth hover:scale-[1.02]',
            ]"
            @click="$emit('start')"
          >
            <el-icon :size="14"><VideoPlay /></el-icon>
            <span>开始仿真</span>
          </button>
        </template>
        <template v-else-if="status === 'running'">
          <button
            data-testid="simulation-pause-button"
            :disabled="readonly"
            :class="[
              'inline-flex items-center gap-2 h-8 px-4 rounded-md text-sm font-semibold transition-all duration-200 shadow-zx-surface-card-depth',
              readonly
                ? 'bg-zx-surface-card-fill text-zx-text-secondary cursor-not-allowed shadow-none'
                : 'bg-zx-accent text-zx-accent-on-fill hover:bg-zx-accent-tint-3 hover:text-zx-accent-on-fill-hover shadow-zx-surface-card-depth',
            ]"
            @click="$emit('pause')"
          >
            <el-icon :size="14"><VideoPause /></el-icon>
            <span>暂停</span>
          </button>
        </template>
        <template v-else-if="status === 'paused'">
          <button
            data-testid="simulation-resume-button"
            :disabled="readonly"
            :class="[
              'inline-flex items-center gap-2 h-8 px-4 rounded-md text-sm font-semibold transition-all duration-200 shadow-zx-surface-card-depth',
              readonly
                ? 'bg-zx-surface-card-fill text-zx-text-secondary cursor-not-allowed shadow-none'
                : 'bg-zx-accent text-zx-accent-on-fill hover:bg-zx-accent-tint-3 hover:text-zx-accent-on-fill-hover shadow-zx-surface-card-depth hover:scale-[1.02]',
            ]"
            @click="$emit('resume')"
          >
            <el-icon :size="14"><VideoPlay /></el-icon>
            <span>继续</span>
          </button>
        </template>

        <!-- 停止 -->
        <button
          data-testid="simulation-stop-button"
          :disabled="readonly || status === 'idle' || status === 'stopped'"
          :class="[
            'inline-flex items-center gap-2 h-8 px-3 rounded-md text-sm font-medium transition-all duration-200',
            readonly || status === 'idle' || status === 'stopped'
              ? 'bg-zx-surface-card-fill text-zx-text-secondary cursor-not-allowed'
              : 'bg-zx-surface-field-fill text-zx-text-primary hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/30',
          ]"
          @click="$emit('stop')"
        >
          <el-icon :size="14"><CircleClose /></el-icon>
          <span>停止</span>
        </button>

        <!-- 单步 -->
        <button
          data-testid="simulation-step-button"
          :disabled="readonly || status !== 'paused' || stepping"
          :class="[
            'inline-flex items-center gap-2 h-8 px-3 rounded-md text-sm font-medium transition-all duration-200',
            readonly || status !== 'paused' || stepping
              ? 'bg-zx-surface-card-fill text-zx-text-secondary cursor-not-allowed'
              : 'bg-zx-surface-field-fill text-zx-text-primary hover:bg-zx-surface-field-fill hover:text-zx-text-primary',
            stepping ? 'cursor-wait opacity-80' : '',
          ]"
          @click="$emit('step')"
        >
          <el-icon v-if="stepping" :size="14" class="animate-spin"><Loading /></el-icon>
          <el-icon v-else :size="14"><DArrowRight /></el-icon>
          <span>{{ stepping ? '单步中' : '单步' }}</span>
        </button>
      </div>

      <!-- 速度调节 -->
      <!-- <div class="flex items-center gap-3 pl-4 border-l border-zx-border-default/50">
        <span class="text-xs font-medium text-zx-text-secondary tracking-wider">速度</span>
        <div class="flex items-center gap-1 p-0.5 rounded-md bg-zx-surface-card-fill/50 border border-zx-border-default/50">
          <button
            v-for="speed in speedOptions"
            :key="speed"
            :class="[
              'px-2.5 py-1 text-xs font-semibold rounded transition-all duration-200',
              localSpeed === speed
                ? 'bg-zx-accent text-zx-accent-on-fill shadow-zx-surface-card-depth'
                : 'text-zx-text-secondary hover:text-zx-text-primary hover:bg-zx-surface-field-fill'
            ]"
            @click="handleSpeedClick(speed)"
          >
            {{ speed }}x
          </button>
        </div>
      </div> -->
    </div>

    <!-- 右侧：状态和时间 -->
    <div class="flex items-center gap-4">
      <!-- 状态指示 -->
      <div
        :class="[
          'flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold border shadow-zx-surface-card-depth',
          statusStyles[status],
        ]"
      >
        <span
          :class="[
            'w-2 h-2 rounded-full shadow-zx-surface-card-depth',
            statusDotStyles[status],
            status === 'running' && 'status-dot-running',
          ]"
        ></span>
        <span class="tracking-wide">{{ statusText }}</span>
      </div>

      <!-- 仿真时间 -->
      <div
        class="flex items-center gap-2 px-3 py-1.5 rounded-md bg-zx-surface-card-fill/80 border border-zx-border-default/50 shadow-zx-surface-card-depth"
      >
        <el-icon class="text-zx-text-secondary" :size="14"><Timer /></el-icon>
        <span class="text-sm font-mono font-bold text-zx-text-primary tracking-wider tabular-nums">
          {{ formattedTime }}
        </span>
      </div>

      <!-- 工具按钮 -->
      <div class="flex items-center gap-1.5 pl-3 border-l border-zx-border-default/50">
        <el-tooltip content="健康自检" placement="bottom" :show-after="300">
          <button
            class="flex items-center justify-center w-8 h-8 rounded-md text-zx-text-secondary hover:text-zx-accent-on-surface hover:bg-zx-surface-card-fill transition-all duration-200 hover:shadow-zx-surface-card-depth"
            aria-label="健康自检"
            @click="$emit('health-check')"
          >
            <el-icon :size="16"><Cpu /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip
          :content="isSimulationActive ? '事件触发' : '请先启动仿真'"
          placement="bottom"
          :show-after="300"
        >
          <button
            :disabled="!isSimulationActive"
            :class="[
              'flex items-center justify-center w-8 h-8 rounded-md transition-all duration-200',
              isSimulationActive
                ? 'text-zx-text-secondary hover:text-amber-400 hover:bg-zx-surface-card-fill hover:shadow-zx-surface-card-depth shadow-zx-surface-card-depth'
                : 'text-zx-text-disabled cursor-not-allowed',
            ]"
            aria-label="事件触发"
            @click="isSimulationActive && $emit('show-events')"
          >
            <el-icon :size="16"><Lightning /></el-icon>
          </button>
        </el-tooltip>
        <el-tooltip content="生成报告" placement="bottom" :show-after="300">
          <button
            class="flex items-center justify-center w-8 h-8 rounded-md text-zx-text-secondary hover:text-zx-accent-on-surface hover:bg-zx-surface-card-fill transition-all duration-200 hover:shadow-zx-surface-card-depth"
            aria-label="生成报告"
            @click="$emit('show-report')"
          >
            <el-icon :size="16"><Document /></el-icon>
          </button>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import {
  ArrowLeft,
  VideoPlay,
  VideoPause,
  CircleClose,
  DArrowRight,
  Timer,
  Loading,
  Cpu,
  Lightning,
  Document,
} from '@element-plus/icons-vue';
import { formatSimulationTime } from '../utils/timeFormatter';

const props = defineProps({
  status: {
    type: String,
    default: 'idle',
  },
  elapsedTime: {
    type: Number,
    default: 0,
  },
  speed: {
    type: Number,
    default: 1,
  },
  projectName: {
    type: String,
    default: '',
  },
  stepping: {
    type: Boolean,
    default: false,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  'start',
  'pause',
  'resume',
  'stop',
  'step',
  'speed-change',
  'back',
  'health-check',
  'show-events',
  'show-report',
]);

const localSpeed = ref(props.speed);
const speedOptions = [0.5, 1, 2, 4];

// 状态样式映射 - 使用克制的配色
const statusStyles = {
  idle: 'bg-zx-surface-card-fill/50 border-zx-border-default/50 text-zx-text-secondary',
  running: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  paused: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  stopped: 'bg-zx-surface-card-fill/50 border-zx-border-default/50 text-zx-text-secondary',
};

const statusDotStyles = {
  idle: 'bg-zx-surface-field-fill',
  running: 'bg-emerald-400',
  paused: 'bg-amber-400',
  stopped: 'bg-zx-surface-field-fill',
};

const statusText = computed(() => {
  const statusMap = {
    idle: '就绪',
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
  };
  return statusMap[props.status] || '未知';
});

// 仿真是否处于活跃状态（运行中或暂停）
const isSimulationActive = computed(() => {
  return props.status === 'running' || props.status === 'paused';
});

const formattedTime = computed(() => {
  return formatSimulationTime(props.elapsedTime);
});

function handleSpeedClick(speed) {
  localSpeed.value = speed;
  emit('speed-change', speed);
}

watch(
  () => props.speed,
  (newSpeed) => {
    localSpeed.value = newSpeed;
  }
);
</script>

<style scoped>
/* 状态指示灯动画 */
@keyframes pulse-glow {
  0%,
  100% {
    opacity: 1;
    box-shadow: 0 0 8px currentColor;
  }
  50% {
    opacity: 0.6;
    box-shadow: 0 0 12px currentColor;
  }
}

.status-dot-running {
  animation: pulse-glow 1.5s ease-in-out infinite;
}

/* 按钮按下效果 */
button:active {
  transform: scale(0.98);
}
</style>
