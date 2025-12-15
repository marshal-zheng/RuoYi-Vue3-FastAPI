<template>
  <zx-floating-panel
    ref="panelRef"
    v-if="visible"
    class="injection-floating simbus-floating-panel"
    theme="dark"
    title="数据注入策略"
    :position="position"
    :size="{ width: '340px', maxHeight: '520px' }"
    :collapsed-size="{ width: '48px', height: '48px' }"
    :default-collapsed="defaultCollapsed"
  >
    <template #header>
      <div class="header">
        <div class="flex items-center gap-2">
          <el-icon class="text-cyan-400"><Setting /></el-icon>
          <div>
            <div class="title">数据注入策略</div>
            <div class="sub">配置仿真数据填充方式</div>
          </div>
        </div>
      </div>
    </template>

    <div class="injection-panel-content">
      <!-- 全局策略选择 -->
      <div class="strategy-section">
        <div class="section-label">全局填充策略</div>
        <el-select 
          v-model="globalStrategy" 
          placeholder="选择策略" 
          size="small" 
          class="w-full strategy-select"
          popper-class="sim-popper-dark"
        >
          <el-option
            v-for="strategy in strategies"
            :key="strategy.value"
            :value="strategy.value"
            :label="strategy.label"
          >
            <div class="flex items-center gap-2">
              <el-icon :class="strategy.iconClass"><component :is="strategy.icon" /></el-icon>
              <div class="flex flex-col">
                <span class="option-label">{{ strategy.label }}</span>
                <span class="option-desc">{{ strategy.description }}</span>
              </div>
            </div>
          </el-option>
        </el-select>
      </div>

      <!-- 策略参数配置 -->
      <div class="params-section" v-if="currentStrategyParams.length > 0">
        <div class="section-label">策略参数</div>

        <!-- 随机值参数 -->
        <template v-if="globalStrategy === 'random'">
          <el-form size="small" label-position="top">
            <el-form-item label="值域范围" class="compact-item">
              <el-input v-model="params.valueRange" placeholder="如: 0~255" />
            </el-form-item>
          </el-form>
        </template>

        <!-- 序列递增参数 -->
        <template v-if="globalStrategy === 'increment'">
          <el-form size="small" label-position="top">
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="起始值" class="compact-item">
                  <el-input-number v-model="params.startValue" :min="0" controls-position="right" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="步长" class="compact-item">
                  <el-input-number v-model="params.step" :min="1" controls-position="right" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </template>

        <!-- 固定值参数 -->
        <template v-if="globalStrategy === 'fixed'">
          <el-form size="small" label-position="top">
            <el-form-item label="固定值" class="compact-item">
              <el-input v-model="params.fixedValue" placeholder="如: 100 或 0xFF" />
            </el-form-item>
          </el-form>
        </template>

        <!-- 循环模式参数 -->
        <template v-if="globalStrategy === 'cycle'">
          <el-form size="small" label-position="top">
            <el-form-item label="预设值列表" class="compact-item">
              <el-input v-model="params.presetValues" placeholder="逗号分隔，如: 0,1,2,3" />
            </el-form-item>
          </el-form>
        </template>

        <!-- 正弦波参数 -->
        <template v-if="globalStrategy === 'sine_wave'">
          <el-form size="small" label-position="top">
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="振幅" class="compact-item">
                  <el-input-number
                    v-model="params.amplitude"
                    :precision="1"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="偏移" class="compact-item">
                  <el-input-number
                    v-model="params.offset"
                    :precision="1"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="频率(Hz)" class="compact-item">
                  <el-input-number
                    v-model="params.frequency"
                    :min="0.1"
                    :precision="2"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="初相位" class="compact-item">
                  <el-input-number
                    v-model="params.phase"
                    :precision="2"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </template>
      </div>

      <!-- 应用按钮 -->
      <div class="action-section">
        <el-button type="primary" size="small" class="w-full apply-btn" @click="handleApply">
          <el-icon class="mr-1"><Check /></el-icon>
          确认策略
        </el-button>
        <div class="tips text-xs mt-2 text-center">
          提示：启动仿真时将使用选择的策略生成报文数据
        </div>
      </div>
    </div>
  </zx-floating-panel>
</template>

<script setup>
import { ref, computed, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Setting,
  Check,
  MagicStick,
  Top,
  Lock,
  Refresh,
  TrendCharts,
} from '@element-plus/icons-vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: true,
  },
  position: {
    type: Object,
    default: () => ({ top: '80px', left: '30px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['apply']);

const panelRef = ref();

// 全局策略
const globalStrategy = ref('random');

// 策略参数
const params = reactive({
  // 随机值
  valueRange: '0~255',
  // 序列递增
  startValue: 0,
  step: 1,
  // 固定值
  fixedValue: '0',
  // 循环模式
  presetValues: '0,1,2,3,4,5',
  // 正弦波
  amplitude: 100,
  offset: 0,
  frequency: 1,
  phase: 0,
});

// 策略列表
const strategies = [
  {
    value: 'random',
    label: '随机值',
    description: '在值域范围内随机生成',
    icon: 'MagicStick',
    iconClass: 'text-blue-500',
    params: ['valueRange'],
  },
  {
    value: 'increment',
    label: '序列递增',
    description: '计数器模式，数值递增',
    icon: 'Top',
    iconClass: 'text-green-500',
    params: ['startValue', 'step'],
  },
  {
    value: 'fixed',
    label: '固定值',
    description: '使用预设固定值',
    icon: 'Lock',
    iconClass: 'text-gray-500',
    params: ['fixedValue'],
  },
  {
    value: 'cycle',
    label: '循环模式',
    description: '循环使用预设数据',
    icon: 'Refresh',
    iconClass: 'text-orange-500',
    params: ['presetValues'],
  },
  {
    value: 'sine_wave',
    label: '正弦波',
    description: '模拟周期性变化',
    icon: 'TrendCharts',
    iconClass: 'text-purple-500',
    params: ['amplitude', 'offset', 'frequency', 'phase'],
  },
];

// 当前策略的参数列表
const currentStrategyParams = computed(() => {
  const strategy = strategies.find((s) => s.value === globalStrategy.value);
  return strategy?.params || [];
});

// 应用策略
function handleApply() {
  const strategyConfig = {
    strategy: globalStrategy.value,
    params: { ...params },
  };

  emit('apply', strategyConfig);
  ElMessage.success(
    `已将"${strategies.find((s) => s.value === globalStrategy.value)?.label}"策略应用到所有字段`
  );
}

defineExpose({
  getConfig: () => ({
    strategy: globalStrategy.value,
    params: { ...params },
  }),
});
</script>

<style lang="less" scoped>
/* 浮动面板样式 - 使用CSS变量 */
.injection-floating {
  border: 1px solid var(--sim-border-accent, rgba(34, 211, 238, 0.3));
  box-shadow: var(--sim-shadow-glow-accent, 0 8px 32px rgba(34, 211, 238, 0.15));
}

.header {
  margin-bottom: 8px;
}

.title {
  font-weight: 700;
  color: var(--sim-accent, #22d3ee);
}

.sub {
  font-size: 11px;
  color: var(--sim-text-tertiary, #94a3b8);
  margin-top: 2px;
}

.injection-panel-content {
  padding: 8px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--sim-text-tertiary, #94a3b8);
  margin-bottom: 8px;
}

.strategy-section {
  margin-bottom: 16px;

  .option-label {
    font-size: 13px;
    color: var(--sim-text-regular, #e2e8f0);
  }

  .option-desc {
    font-size: 11px;
    color: var(--sim-text-disabled, #64748b);
  }
}

/* Select 输入框暗黑样式 - 使用CSS变量 */
.strategy-select {
  :deep(.el-input__wrapper) {
    background-color: var(--sim-fill-light, rgba(15, 23, 42, 0.8)) !important;
    border: 1px solid var(--sim-border-base, rgba(51, 65, 85, 0.5)) !important;
    box-shadow: none !important;
  }

  :deep(.el-input__wrapper:hover) {
    border-color: var(--sim-border-accent, rgba(34, 211, 238, 0.4)) !important;
  }

  :deep(.el-input__wrapper.is-focus) {
    border-color: var(--sim-border-focus, rgba(34, 211, 238, 0.6)) !important;
  }

  :deep(.el-input__inner) {
    color: var(--sim-text-regular, #e2e8f0) !important;
  }

  :deep(.el-select__caret) {
    color: var(--sim-text-tertiary, #94a3b8) !important;
  }
}

.params-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--sim-fill-lighter, rgba(15, 23, 42, 0.6));
  border: 1px solid var(--sim-border-light, rgba(45, 212, 191, 0.08));
  border-radius: var(--sim-radius-lg, 10px);

  .compact-item {
    margin-bottom: 8px;

    :deep(.el-form-item__label) {
      font-size: 12px;
      padding-bottom: 4px;
      color: var(--sim-text-tertiary, #94a3b8);
    }
  }
}

.action-section {
  margin-bottom: 8px;
}

/* 确认策略按钮样式 - 使用CSS变量 */
.apply-btn {
  background: linear-gradient(135deg, var(--sim-accent-bg, rgba(34, 211, 238, 0.2)), rgba(45, 212, 191, 0.2)) !important;
  border: 1px solid var(--sim-border-focus, rgba(34, 211, 238, 0.5)) !important;
  color: var(--sim-accent, #22d3ee) !important;
  font-weight: 600;
  transition: all var(--sim-transition-normal, 0.3s ease);
}

.apply-btn:hover {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.3), rgba(45, 212, 191, 0.3)) !important;
  border-color: var(--sim-accent-light, rgba(34, 211, 238, 0.7)) !important;
  box-shadow: var(--sim-shadow-glow-accent, 0 4px 12px rgba(34, 211, 238, 0.25));
  transform: translateY(-1px);
}

.tips {
  line-height: 1.4;
  color: var(--sim-text-disabled, #64748b);
}
</style>
