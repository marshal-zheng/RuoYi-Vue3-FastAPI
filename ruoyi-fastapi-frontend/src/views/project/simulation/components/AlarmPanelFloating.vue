<template>
  <zx-floating-panel
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
    class="alarm-panel-floating floating-panel shadow-lg"
    theme="dark"
  >
    <template #header>
      <div class="panel-header">
        <div class="panel-title">
          <span class="title-text">告警</span>
          <el-badge v-if="alarmBadge" :value="alarmBadge" :max="99" type="danger" />
        </div>
        <div class="panel-actions">
          <!-- 可按需添加操作按钮 -->
        </div>
      </div>
    </template>

    <div class="alarm-panel-content panel-body h-full" style="height: 350px">
      <AlarmPanel
        :alarms="alarms"
        @alarm-click="$emit('alarm-click', $event)"
        @filter-change="$emit('filter-change', $event)"
        @stats-change="handleStatsChange"
      />
    </div>
  </zx-floating-panel>
</template>

<script setup>
import { computed, ref } from 'vue';
import AlarmPanel from './AlarmPanel.vue';

const props = defineProps({
  alarms: {
    type: Array,
    default: () => [],
  },
  position: {
    type: Object,
    default: () => ({ top: '550px', right: '28px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '320px', maxHeight: '420px' }),
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

const alarmSummary = ref({ total: 0 });

const alarmBadge = computed(() => alarmSummary.value?.total || 0);

const handleStatsChange = (stats) => {
  alarmSummary.value = stats || { total: 0 };
};

defineEmits(['alarm-click', 'filter-change']);
</script>

<style scoped lang="less">
.floating-panel {
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  color: #e2e8f0;
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
  color: #94a3b8;
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
