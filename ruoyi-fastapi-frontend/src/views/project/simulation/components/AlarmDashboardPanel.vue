<template>
  <section class="simulation-widget-content">
    <header class="simulation-widget-toolbar">
      <div class="panel-header">
        <div class="panel-title">
          <el-badge v-if="alarmBadge" :value="alarmBadge" :max="99" type="danger" />
        </div>
        <div class="panel-actions">
          <!-- 可按需添加操作按钮 -->
        </div>
      </div>
    </header>

    <div class="alarm-panel-content panel-body h-full">
      <AlarmPanel
        :alarms="alarms"
        @alarm-click="$emit('alarm-click', $event)"
        @filter-change="$emit('filter-change', $event)"
        @stats-change="handleStatsChange"
      />
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import AlarmPanel from './AlarmPanel.vue';

defineProps({
  alarms: {
    type: Array,
    default: () => [],
  },
});

const alarmSummary = ref({ total: 0 });

const alarmBadge = computed(() => alarmSummary.value?.total || 0);

const handleStatsChange = (stats) => {
  alarmSummary.value = stats || { total: 0 };
};

defineEmits(['alarm-click', 'filter-change']);
</script>

<style scoped lang="less">
.floating-panel {
  border: 1px solid color-mix(in srgb, var(--zx-semantic-border-default) 15%, transparent);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  color: var(--zx-semantic-text-primary);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--zx-semantic-text-secondary);
  font-size: 12px;
}

.alarm-panel-content {
  flex: 1;
  min-height: 0;
  display: flex;
  height: 100%;
}

:deep(.alarm-panel-content) {
  flex: 1;
  min-height: 0;
}

::v-deep(.pro-card-header) {
  display: none;
}

@import '../styles/aviation-dark-theme.less';
</style>
