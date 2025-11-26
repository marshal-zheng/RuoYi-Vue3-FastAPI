<template>
  <zx-floating-panel
    v-if="narration"
    title="仿真进度"
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="false"
  >
    <template #header>
      <div class="simulation-status-panel__header">
        <el-tag :type="badgeType" size="small">
          {{ narration.badge }}
        </el-tag>
        <span class="simulation-status-panel__title">仿真进度</span>
      </div>
    </template>
    <div class="simulation-status-panel__content">
      <p class="simulation-status-panel__main-title">{{ narration.title }}</p>
      <p class="simulation-status-panel__desc">{{ narration.description }}</p>
      <p v-if="narration.busType" class="simulation-status-panel__meta">
        <el-tag size="small" effect="plain">{{ narration.busType }}</el-tag>
      </p>
    </div>
  </zx-floating-panel>
</template>

<script setup name="SimulationStatusPanel">
import { computed } from 'vue';

const props = defineProps({
  narration: {
    type: Object,
    default: null,
  },
  position: {
    type: Object,
    default: () => ({ top: '40px', left: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '360px', maxHeight: '240px' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
});

const badgeType = computed(() => {
  return props.narration?.badge === '完成' ? 'success' : 'primary';
});
</script>

<style lang="less" scoped>
.simulation-status-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.simulation-status-panel__title {
  font-weight: 600;
  font-size: 14px;
}

.simulation-status-panel__content {
  padding: 12px 0;
}

.simulation-status-panel__main-title {
  font-weight: 600;
  margin: 0 0 8px;
  font-size: 14px;
  color: #1f2937;
}

.simulation-status-panel__desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.simulation-status-panel__meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
