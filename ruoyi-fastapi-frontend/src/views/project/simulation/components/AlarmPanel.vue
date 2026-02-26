<template>
  <div
    class="flex flex-col h-full min-h-0 bg-gradient-to-b from-[#000000] to-[#050505] rounded-lg overflow-hidden alarm-panel-content"
  >
    <!-- 统计卡片区域 -->
    <div class="stat-cards-area p-3 border-b border-white/10">
      <div class="grid grid-cols-4 gap-2">
        <div
          v-for="card in statCards"
          :key="card.key"
          class="stat-card flex items-center gap-1.5 p-2 bg-black/90 rounded-md border transition-all duration-300"
          :class="card.borderClass"
        >
          <div
            class="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 text-white/90"
            :class="card.iconClass"
          >
            <ZxIcon :icon="card.icon" :size="14" />
          </div>
          <div class="flex flex-col min-w-0">
            <span class="text-[11px] text-white/80 font-semibold tracking-wide">{{
              card.label
            }}</span>
            <span
              class="text-[13px] font-semibold font-mono text-white/80"
              :class="card.valueClass"
            >
              {{ card.value }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 告警列表区域 -->
    <div class="alarm-list-area flex-1 flex flex-col min-h-0 px-3 pb-3 overflow-hidden">
      <div class="alarm-list-header flex justify-between items-center py-2">
        <span class="text-[11px] text-white/70 uppercase tracking-wider">告警列表</span>
        <el-button
          v-if="filteredAlarms.length > 0"
          link
          size="small"
          class="!text-[11px] !text-white/40 hover:!text-white/80"
          @click="handleClearAll"
        >
          清空
        </el-button>
      </div>

      <div class="flex-1 min-h-0">
        <RecycleScroller
          v-if="filteredAlarms.length > 0"
          class="alarm-virtual-scroller alarm-scroll"
          :items="filteredAlarms"
          :item-size="70"
          key-field="alarmId"
        >
          <template #default="{ item: alarm }">
            <div
              class="alarm-item flex gap-2 px-2.5 py-1 mb-1.5 bg-black/80 rounded-md border cursor-pointer transition-all duration-200"
              :class="[
                alarm.severity === 'critical' ? 'critical' : '',
                alarm.severity === 'error' ? 'error' : '',
                alarm.severity === 'warning' ? 'warning' : '',
                !alarm.read && alarm.severity === 'critical'
                  ? 'bg-red-500/10 border-red-500/30'
                  : !alarm.read
                    ? 'bg-blue-500/[0.08] border-blue-500/20'
                    : 'border-white/10',
              ]"
              @click="handleAlarmClick(alarm)"
            >
              <div
                class="w-[3px] flex-shrink-0 rounded-sm"
                :class="{
                  'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]': alarm.severity === 'critical',
                  'bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.4)]': alarm.severity === 'error',
                  'bg-amber-500': alarm.severity === 'warning',
                  'bg-slate-500': alarm.severity === 'info',
                }"
              ></div>
              <div class="flex-1 min-w-0">
                <div class="flex justify-between items-center mb-1">
                  <div class="flex items-center gap-1.5">
                    <span class="alarm-text text-[11px] font-semibold text-white/90">{{
                      getAlarmTypeLabel(alarm.alarmType)
                    }}</span>
                    <span class="reason-pill" :style="getReasonStyle(alarm.alarmType)">
                      {{ getReasonLabel(alarm.alarmType) }}
                    </span>
                  </div>
                  <span class="alarm-time text-[10px] text-white/50 font-mono">{{
                    formatTime(alarm.timestamp)
                  }}</span>
                </div>
                <div class="alarm-text text-[11px] text-white/80 leading-relaxed line-clamp-2">
                  {{ alarm.message }}
                </div>
              </div>
            </div>
          </template>
        </RecycleScroller>
        <div v-else class="flex flex-col items-center justify-center h-full py-8">
          <div class="text-emerald-500 mb-3 animate-float">
            <svg viewBox="0 0 48 48" fill="none" class="w-12 h-12">
              <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="2" opacity="0.3" />
              <path
                d="M16 24l6 6 12-12"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <div class="text-sm font-semibold text-white/80 mb-1">暂无告警</div>
          <div class="text-[11px] text-white/40 mb-4">系统运行正常</div>
          <div
            class="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full"
          >
            <span
              class="w-1.5 h-1.5 bg-emerald-500 rounded-full shadow-[0_0_6px_#10b981] animate-pulse"
            ></span>
            <span class="text-[10px] text-emerald-500">监控中</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue';
import { RecycleScroller } from 'vue-virtual-scroller';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAlarmManager } from '../composables/useAlarmManager';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

const props = defineProps({
  alarms: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['alarm-click', 'filter-change', 'stats-change']);

const alarmManager = useAlarmManager();
const { filteredAlarms, alarmStats, getAlarmTypeLabel, clearAllAlarms, markAsRead } = alarmManager;

const reasonMap = {
  collision: { label: '冲突', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  multi_connection: { label: '冲突', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  packet_loss: { label: '丢包', color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  bandwidth_limit: { label: '带宽限速', color: '#22d3ee', bg: 'rgba(34,211,238,0.12)' },
  congestion: { label: '超载', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  bandwidth_exceed: { label: '超载', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  bandwidth_overflow: { label: '超载', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  value_overflow: { label: '超载', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  disconnect: { label: '链路断开', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  link_down: { label: '链路断开', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  device_failure: { label: '链路断开', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)' },
  delay: { label: '延迟注入', color: '#a855f7', bg: 'rgba(168,85,247,0.12)' },
  payload_corrupt: { label: '数据篡改', color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  noise_frame: { label: '噪声帧', color: '#eab308', bg: 'rgba(234,179,8,0.12)' },
  error_frame: { label: '错误帧', color: '#f43f5e', bg: 'rgba(244,63,94,0.12)' },
};

const toneMap = {
  red: {
    border: 'border-white/5',
    borderActive: 'border-red-500/30 bg-red-500/[0.08]',
    icon: 'bg-gradient-to-br from-red-500/50 to-red-600/50',
    iconActive: 'bg-gradient-to-br from-red-500 to-red-600 shadow-[0_0_8px_rgba(239,68,68,0.4)]',
    value: 'text-white/70',
    valueActive: 'text-red-500 animate-pulse',
  },
  orange: {
    border: 'border-white/5',
    borderActive: 'border-orange-500/30 bg-orange-500/[0.08]',
    icon: 'bg-gradient-to-br from-orange-400/80 to-orange-600/80',
    iconActive:
      'bg-gradient-to-br from-orange-500 to-orange-600 shadow-[0_0_6px_rgba(249,115,22,0.4)]',
    value: 'text-white/70',
    valueActive: 'text-orange-500',
  },
  amber: {
    border: 'border-white/5',
    borderActive: 'border-amber-500/30 bg-amber-500/[0.08]',
    icon: 'bg-gradient-to-br from-amber-400/80 to-amber-600/80',
    iconActive: 'bg-gradient-to-br from-amber-400 to-amber-600',
    value: 'text-white/70',
    valueActive: 'text-amber-500',
  },
  violet: {
    border: 'border-white/5',
    borderActive: 'border-white/5',
    icon: 'bg-gradient-to-br from-violet-500 to-violet-600',
    iconActive: 'bg-gradient-to-br from-violet-500 to-violet-600',
    value: 'text-white/70',
    valueActive: 'text-white/70',
  },
};

const statConfigs = [
  { key: 'critical', label: '严重', icon: 'mdi:alert-octagon', tone: 'red' },
  { key: 'error', label: '错误', icon: 'mdi:alert-circle-outline', tone: 'orange' },
  { key: 'warning', label: '警告', icon: 'mdi:alert-outline', tone: 'amber' },
  { key: 'total', label: '总计', icon: 'mdi:clipboard-list-outline', tone: 'violet' },
];

const statCards = computed(() => {
  const stats = alarmStats.value || {};
  return statConfigs.map((item) => {
    const value = stats[item.key] || 0;
    const tone = toneMap[item.tone];
    const active = item.key !== 'total' && value > 0;
    return {
      ...item,
      value,
      borderClass: active ? tone.borderActive : tone.border,
      iconClass: active ? tone.iconActive : tone.icon,
      valueClass: active ? tone.valueActive : tone.value,
    };
  });
});

watch(
  () => props.alarms,
  (newAlarms) => {
    if (newAlarms && newAlarms.length > 0) {
      alarmManager.addAlarm(newAlarms);
    }
  },
  { immediate: true, deep: true }
);

watch(
  alarmStats,
  (stats) => {
    emit('stats-change', stats);
  },
  { immediate: true }
);

function formatTime(timestamp) {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function handleAlarmClick(alarm) {
  markAsRead(alarm.alarmId);
  emit('alarm-click', alarm);
}

function handleClearAll() {
  ElMessageBox.confirm('确定要清空所有告警吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      clearAllAlarms();
      ElMessage.success('已清空所有告警');
    })
    .catch(() => {});
}

function getReasonLabel(alarmType) {
  const key = (alarmType || '').toLowerCase();
  return reasonMap[key]?.label || '告警';
}

function getReasonStyle(alarmType) {
  const key = (alarmType || '').toLowerCase();
  const reason = reasonMap[key] || { color: '#cbd5e1', bg: 'rgba(148,163,184,0.12)' };
  return {
    color: reason.color,
    backgroundColor: reason.bg,
    borderColor: reason.color,
  };
}
</script>

<style scoped>
@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.reason-pill {
  padding: 2px 6px;
  font-size: 10px;
  border-radius: 999px;
  border: 1px solid transparent;
  line-height: 1.2;
}

.alarm-virtual-scroller {
  height: 100%;
  width: 100%;
  overflow-y: auto;
}

.alarm-item {
  min-height: 54px;
}

.alarm-virtual-scroller {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
}

.alarm-virtual-scroller::-webkit-scrollbar {
  width: 6px;
}

.alarm-virtual-scroller::-webkit-scrollbar-track {
  background: transparent;
}

.alarm-virtual-scroller::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.25);
  border-radius: 6px;
}
</style>
