<template>
  <zx-floating-panel
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
    class="floating-panel shadow-lg"
    theme="dark"
  >
    <template #header>
      <div class="panel-header">
        <div class="panel-title">
          <span class="title-text">带宽监控</span>
        </div>
        <div class="panel-actions">
          <div class="view-toggle">
            <span
              class="toggle-item"
              :class="{ active: !localShowTrend }"
              @click="updateTrend(false)"
            >仪表</span>
            <span class="toggle-divider">|</span>
            <span
              class="toggle-item"
              :class="{ active: localShowTrend }"
              @click="updateTrend(true)"
            >趋势</span>
          </div>
        </div>
      </div>
    </template>

    <BandwidthDashboard
      v-model:showTrend="localShowTrend"
      :bandwidth-data="bandwidthData"
      :is-running="isRunning"
      @port-click="$emit('port-click', $event)"
    />
  </zx-floating-panel>
</template>

<script setup>
import { computed } from 'vue';
import BandwidthDashboard from './BandwidthDashboard.vue';

const props = defineProps({
  bandwidthData: {
    type: Array,
    default: () => [],
  },
  isRunning: {
    type: Boolean,
    default: false,
  },
  showTrend: {
    type: Boolean,
    default: false,
  },
  position: {
    type: Object,
    default: () => ({ top: '90px', right: '28px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '520px', maxHeight: '430px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '46px', height: '46px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:showTrend', 'port-click']);

const localShowTrend = computed({
  get: () => props.showTrend,
  set: (val) => emit('update:showTrend', val),
});

function updateTrend(val) {
  localShowTrend.value = val;
}
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.panel-title .title-text {
  font-weight: 600;
  color: #e2e8f0;
}

.panel-actions .view-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.toggle-item {
  cursor: pointer;
  transition: color 0.15s ease;
}

.toggle-item.active {
  color: #22d3ee;
  font-weight: 600;
}

.toggle-divider {
  opacity: 0.4;
}

.floating-panel {
  border: 1px solid rgba(148, 163, 184, 0.15);
}
</style>
