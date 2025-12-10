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
          <el-badge v-if="alarms?.length" :value="alarms.length" :max="99" type="danger" />
        </div>
        <div class="panel-actions">
          <!-- 可按需添加操作按钮 -->
        </div>
      </div>
    </template>

    <div class="alarm-panel-content">
      <AlarmPanel
        :alarms="alarms"
        @alarm-click="$emit('alarm-click', $event)"
        @filter-change="$emit('filter-change', $event)"
      />
    </div>
  </zx-floating-panel>
</template>

<script setup>
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

::v-deep(.pro-card-header) {
  display: none;
}

@import '../styles/aviation-dark-theme.less';
</style>
