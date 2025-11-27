<template>
  <zx-floating-panel
    ref="panelRef"
    v-if="visible"
    title="数据注入策略"
    :position="position"
    :size="{ width: '320px', maxHeight: '400px' }"
    :collapsed-size="{ width: '48px', height: '48px' }"
    :default-collapsed="defaultCollapsed"
  >
    <template #header>
      <div class="flex items-center gap-2">
        <el-icon class="text-blue-500"><Setting /></el-icon>
        <span class="font-semibold text-sm">数据注入策略</span>
      </div>
    </template>

    <div class="injection-panel-content">
      <!-- 全局策略选择 -->
      <div class="strategy-section">
        <div class="section-label">全局填充策略</div>
        <el-select v-model="globalStrategy" placeholder="选择策略" size="small" class="w-full">
          <el-option
            v-for="strategy in strategies"
            :key="strategy.value"
            :value="strategy.value"
            :label="strategy.label"
          >
            <div class="flex items-center gap-2">
              <el-icon :class="strategy.iconClass"><component :is="strategy.icon" /></el-icon>
              <div class="flex flex-col">
                <span class="text-sm">{{ strategy.label }}</span>
                <span class="text-xs text-gray-400">{{ strategy.description }}</span>
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
        <el-button type="primary" size="small" class="w-full" @click="handleApply">
          <el-icon class="mr-1"><Check /></el-icon>
          确认策略
        </el-button>
        <div class="tips text-xs text-gray-400 mt-2 text-center">
          提示：执行仿真时将使用选择的策略生成报文数据
        </div>
      </div>

      <!-- 策略说明 -->
      <div class="info-section">
        <el-divider content-position="left">
          <span class="text-xs text-gray-400">策略说明</span>
        </el-divider>
        <div class="strategy-info">
          <div
            v-for="strategy in strategies"
            :key="strategy.value"
            class="strategy-item"
            :class="{ active: globalStrategy === strategy.value }"
          >
            <el-icon :class="strategy.iconClass"><component :is="strategy.icon" /></el-icon>
            <span class="strategy-name">{{ strategy.label }}</span>
            <span class="strategy-desc">{{ strategy.description }}</span>
          </div>
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
.injection-panel-content {
  padding: 8px;
}

.section-label {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.strategy-section {
  margin-bottom: 16px;
}

.params-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;

  .compact-item {
    margin-bottom: 8px;

    :deep(.el-form-item__label) {
      font-size: 12px;
      padding-bottom: 4px;
    }
  }
}

.action-section {
  margin-bottom: 16px;
}

.info-section {
  .strategy-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .strategy-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 12px;
    transition: all 0.2s;

    &.active {
      background: #ecf5ff;
    }

    .el-icon {
      font-size: 14px;
    }

    .strategy-name {
      font-weight: 500;
      min-width: 60px;
    }

    .strategy-desc {
      color: #909399;
      flex: 1;
    }
  }
}

.tips {
  line-height: 1.4;
}
</style>
