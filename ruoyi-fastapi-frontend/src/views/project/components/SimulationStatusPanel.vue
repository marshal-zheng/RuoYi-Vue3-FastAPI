<template>
  <zx-floating-panel
    v-if="visible"
    title="仿真监控"
    :position="position"
    :size="panelSize"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
  >
    <template #header>
      <div class="simulation-monitor__header">
        <span class="simulation-monitor__title">仿真监控</span>
        <el-badge v-if="alarmStats.total > 0" :value="alarmStats.total" :max="99" type="danger" />
      </div>
    </template>

    <div class="simulation-monitor__body">
      <!-- 仿真进度部分 -->
      <div v-if="narration" class="simulation-monitor__progress">
        <div class="simulation-monitor__progress-header">
          <el-tag :type="badgeType" size="small">
            {{ narration.badge }}
          </el-tag>
          <span class="simulation-monitor__progress-title">{{ narration.title }}</span>
        </div>
        <p class="simulation-monitor__progress-desc">{{ narration.description }}</p>
        <p v-if="narration.busType" class="simulation-monitor__progress-meta">
          <el-tag size="small" effect="plain">{{ narration.busType }}</el-tag>
        </p>
      </div>

      <el-divider v-if="narration && alarms.length > 0" class="simulation-monitor__divider" />

      <!-- 告警信息部分 -->
      <div v-if="alarms.length > 0" class="simulation-monitor__alarms">
        <!-- 告警统计 -->
        <div class="simulation-monitor__alarm-stats">
          <div
            class="simulation-monitor__stat-item"
            :class="{ 'simulation-monitor__stat-item--active': alarmStats.critical > 0 }"
          >
            <div class="simulation-monitor__stat-icon simulation-monitor__stat-icon--critical">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="simulation-monitor__stat-content">
              <div class="simulation-monitor__stat-value">{{ alarmStats.critical || 0 }}</div>
              <div class="simulation-monitor__stat-label">严重</div>
            </div>
          </div>
          <div
            class="simulation-monitor__stat-item"
            :class="{ 'simulation-monitor__stat-item--active': alarmStats.error > 0 }"
          >
            <div class="simulation-monitor__stat-icon simulation-monitor__stat-icon--error">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="simulation-monitor__stat-content">
              <div class="simulation-monitor__stat-value">{{ alarmStats.error || 0 }}</div>
              <div class="simulation-monitor__stat-label">错误</div>
            </div>
          </div>
          <div
            class="simulation-monitor__stat-item"
            :class="{ 'simulation-monitor__stat-item--active': alarmStats.warning > 0 }"
          >
            <div class="simulation-monitor__stat-icon simulation-monitor__stat-icon--warning">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="simulation-monitor__stat-content">
              <div class="simulation-monitor__stat-value">{{ alarmStats.warning || 0 }}</div>
              <div class="simulation-monitor__stat-label">警告</div>
            </div>
          </div>
        </div>

        <!-- 告警列表 -->
        <div class="simulation-monitor__alarm-list">
          <div
            v-for="alarm in displayAlarms"
            :key="alarm.alarmId"
            class="simulation-monitor__alarm-item"
            :class="[`simulation-monitor__alarm-item--${alarm.severity}`]"
          >
            <div class="simulation-monitor__alarm-icon">
              <el-icon>
                <component :is="getSeverityIcon(alarm.severity)" />
              </el-icon>
            </div>
            <div class="simulation-monitor__alarm-content">
              <div class="simulation-monitor__alarm-header">
                <el-tag :type="getSeverityTagType(alarm.severity)" size="small" effect="dark">
                  {{ getSeverityLabel(alarm.severity) }}
                </el-tag>
                <span class="simulation-monitor__alarm-time">
                  {{ formatTime(alarm.timestamp) }}
                </span>
              </div>
              <div class="simulation-monitor__alarm-message">{{ alarm.message }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div v-else-if="!narration" class="simulation-monitor__empty">
        <el-empty description="暂无监控数据" :image-size="60" />
      </div>
    </div>
  </zx-floating-panel>
</template>

<script setup name="SimulationStatusPanel">
import { computed, watch } from 'vue';
import { CircleCloseFilled, WarningFilled, Warning, InfoFilled } from '@element-plus/icons-vue';
import { useAlarmManager } from '../simulation/composables/useAlarmManager';

const props = defineProps({
  narration: {
    type: Object,
    default: null,
  },
  alarms: {
    type: Array,
    default: () => [],
  },
  visible: {
    type: Boolean,
    default: false,
  },
  position: {
    type: Object,
    default: () => ({ top: '40px', left: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '380px', maxHeight: '50vh' }),
  },
  collapsedSize: {
    type: Object,
    default: () => ({ width: '48px', height: '48px' }),
  },
  defaultCollapsed: {
    type: Boolean,
    default: false,
  },
});

// 确保使用 vh 单位的面板尺寸
const panelSize = computed(() => ({
  width: props.size.width || '380px',
  maxHeight: props.size.maxHeight || '50vh',
}));

const alarmManager = useAlarmManager();
const { alarmStats, getSeverityLabel } = alarmManager;

// 同步外部告警数据
watch(
  () => props.alarms,
  (newAlarms) => {
    if (newAlarms && newAlarms.length > 0) {
      alarmManager.addAlarm(newAlarms);
    }
  },
  { immediate: true, deep: true }
);

const badgeType = computed(() => {
  return props.narration?.badge === '完成' ? 'success' : 'primary';
});

// 只显示最新的5条告警
const displayAlarms = computed(() => {
  return alarmManager.filteredAlarms.value.slice(0, 5);
});

function getSeverityIcon(severity) {
  const iconMap = {
    critical: CircleCloseFilled,
    error: WarningFilled,
    warning: Warning,
    info: InfoFilled,
  };
  return iconMap[severity] || InfoFilled;
}

function getSeverityTagType(severity) {
  const typeMap = {
    critical: 'danger',
    error: 'danger',
    warning: 'warning',
    info: 'info',
  };
  return typeMap[severity] || 'info';
}

function formatTime(timestamp) {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
}
</script>

<style lang="less" scoped>
.simulation-monitor__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.simulation-monitor__title {
  font-weight: 600;
  font-size: 14px;
}

.simulation-monitor__body {
  padding: 8px 0;
  max-height: calc(50vh - 60px);
  overflow-y: auto;
}

/* 仿真进度部分 */
.simulation-monitor__progress {
  padding: 8px 0;
}

.simulation-monitor__progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.simulation-monitor__progress-title {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.simulation-monitor__progress-desc {
  margin: 0 0 8px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.simulation-monitor__progress-meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.simulation-monitor__divider {
  margin: 12px 0;
}

/* 告警部分 */
.simulation-monitor__alarms {
  padding: 8px 0;
}

.simulation-monitor__alarm-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.simulation-monitor__stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 6px;
  transition: all 0.2s ease;

  &--active {
    background: #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
}

.simulation-monitor__stat-icon {
  font-size: 18px;

  &--critical {
    color: #991b1b;
  }

  &--error {
    color: #ef4444;
  }

  &--warning {
    color: #eab308;
  }
}

.simulation-monitor__stat-content {
  flex: 1;
}

.simulation-monitor__stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1;
}

.simulation-monitor__stat-label {
  font-size: 10px;
  color: #6b7280;
  margin-top: 2px;
}

.simulation-monitor__alarm-list {
  max-height: 200px;
  overflow-y: auto;
}

.simulation-monitor__alarm-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  margin-bottom: 6px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  border-left-width: 3px;

  &--critical {
    border-left-color: #991b1b;
  }

  &--error {
    border-left-color: #ef4444;
  }

  &--warning {
    border-left-color: #eab308;
  }

  &--info {
    border-left-color: #9ca3af;
  }
}

.simulation-monitor__alarm-icon {
  font-size: 16px;
  padding-top: 2px;
}

.simulation-monitor__alarm-content {
  flex: 1;
  min-width: 0;
}

.simulation-monitor__alarm-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.simulation-monitor__alarm-time {
  margin-left: auto;
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
}

.simulation-monitor__alarm-message {
  font-size: 12px;
  color: #1f2937;
  line-height: 1.4;
  word-break: break-word;
}

.simulation-monitor__empty {
  padding: 20px 0;
}
</style>
