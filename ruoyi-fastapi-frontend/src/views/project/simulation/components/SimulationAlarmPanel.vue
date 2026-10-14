<template>
  <zx-floating-panel
    title="告警信息"
    :showCollapseBtn="false"
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
    class="floating-panel"
  >
    <AlarmPanel
      :alarms="alarms"
      @alarm-click="$emit('alarm-click', $event)"
      @filter-change="$emit('filter-change', $event)"
    />
  </zx-floating-panel>
</template>

<script setup>
import AlarmPanel from './AlarmPanel.vue';

defineProps({
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

<style scoped>
.floating-panel {
  border: 1px solid color-mix(in srgb, var(--zx-semantic-border-default) 15%, transparent);
}
</style>
