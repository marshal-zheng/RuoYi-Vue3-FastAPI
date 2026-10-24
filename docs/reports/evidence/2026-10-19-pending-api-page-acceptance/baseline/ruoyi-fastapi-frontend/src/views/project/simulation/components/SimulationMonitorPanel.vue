<template>
  <zx-floating-panel
    v-if="visible"
    :showCollapseBtn="false"
    title="告警信息"
    :position="position"
    :size="size"
    :collapsed-size="collapsedSize"
    :default-collapsed="defaultCollapsed"
  >
    <template #header>
      <div class="flex items-center gap-2">
        <span class="font-semibold text-sm">告警信息</span>
        <el-badge v-if="alarmStats.total > 0" :value="alarmStats.total" :max="99" type="danger" />
      </div>
    </template>

    <div class="simulation-monitor-panel py-2 max-h-[calc(70vh-60px)] overflow-y-auto">
      <!-- 告警统计 -->
      <div v-if="alarmStats.total > 0" class="flex gap-2 mb-3">
        <div
          class="flex-1 flex items-center gap-2 p-2 rounded transition-all"
          :class="{
            'bg-zx-surface-card-fill shadow-zx-surface-card-depth': alarmStats.critical > 0,
          }"
        >
          <div class="text-lg text-red-700">
            <el-icon><CircleCloseFilled /></el-icon>
          </div>
          <div class="flex-1">
            <div class="text-base font-semibold text-zx-text-primary leading-none">
              {{ alarmStats.critical || 0 }}
            </div>
            <div class="text-[10px] text-zx-text-secondary mt-0.5">严重</div>
          </div>
        </div>
        <div
          class="flex-1 flex items-center gap-2 p-2 rounded transition-all"
          :class="{ 'bg-zx-surface-card-fill shadow-zx-surface-card-depth': alarmStats.error > 0 }"
        >
          <div class="text-lg text-red-500">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div class="flex-1">
            <div class="text-base font-semibold text-zx-text-primary leading-none">
              {{ alarmStats.error || 0 }}
            </div>
            <div class="text-[10px] text-zx-text-secondary mt-0.5">错误</div>
          </div>
        </div>
        <div
          class="flex-1 flex items-center gap-2 p-2 rounded transition-all"
          :class="{
            'bg-zx-surface-card-fill shadow-zx-surface-card-depth': alarmStats.warning > 0,
          }"
        >
          <div class="text-lg text-yellow-500">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="flex-1">
            <div class="text-base font-semibold text-zx-text-primary leading-none">
              {{ alarmStats.warning || 0 }}
            </div>
            <div class="text-[10px] text-zx-text-secondary mt-0.5">警告</div>
          </div>
        </div>
      </div>

      <!-- 告警列表 -->
      <div v-if="alarmStats.total > 0" class="max-h-[300px] overflow-y-auto">
        <div
          v-for="alarm in displayAlarms"
          :key="alarm.alarmId"
          class="flex gap-2 p-2 mb-1.5 border rounded border-l-[3px]"
          :class="{
            'border-l-red-700': alarm.severity === 'critical',
            'border-l-red-500': alarm.severity === 'error',
            'border-l-yellow-500': alarm.severity === 'warning',
            'border-l-zx-status-info-on-surface': alarm.severity === 'info',
          }"
        >
          <div class="text-base pt-0.5">
            <el-icon>
              <component :is="getSeverityIcon(alarm.severity)" />
            </el-icon>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 mb-1">
              <el-tag :type="getSeverityTagType(alarm.severity)" size="small" effect="dark">
                {{ getSeverityLabel(alarm.severity) }}
              </el-tag>
              <span class="ml-auto text-[11px] text-zx-text-secondary whitespace-nowrap">
                {{ formatTime(alarm.timestamp) }}
              </span>
            </div>
            <div class="text-xs text-zx-text-primary leading-snug break-words">
              {{ alarm.message }}
            </div>
          </div>
        </div>
      </div>

      <!-- 无告警提示 -->
      <div v-else class="py-5">
        <el-empty description="暂无告警信息" :image-size="60" />
      </div>
    </div>
  </zx-floating-panel>
</template>

<script setup>
import { computed, watch } from 'vue';
import { CircleCloseFilled, WarningFilled, Warning, InfoFilled } from '@element-plus/icons-vue';
import { useAlarmManager } from '../composables/useAlarmManager';

const props = defineProps({
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
    default: () => ({ bottom: '30px', left: '30px' }),
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

// 显示所有告警
const displayAlarms = computed(() => {
  return alarmManager.filteredAlarms.value;
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

<style scoped lang="less">
@import './SimulationMonitorPanel.less';
</style>
