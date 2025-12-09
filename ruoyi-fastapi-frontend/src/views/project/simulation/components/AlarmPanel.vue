<template>
  <div class="flex flex-col h-full">
    <!-- 头部 -->
    <div class="pro-card-header flex justify-between items-center">
      <div class="flex items-center gap-2">
        <el-icon class="text-amber-500"><Bell /></el-icon>
        <span class="text-sm font-semibold text-slate-200">告警信息</span>
        <el-badge v-if="alarmStats.total > 0" :value="alarmStats.total" :max="99" type="danger" />
      </div>
      <el-button link size="small" :disabled="alarms.length === 0" @click="handleClearAll" class="!text-slate-400 hover:!text-slate-200">
        清空
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 gap-3 p-3 border-b border-slate-700/50 bg-slate-900/50">
      <div
        class="flex flex-col items-center py-3 rounded-md transition-all duration-200 border"
        :class="alarmStats.critical > 0 ? 'bg-danger-500/10 border-danger-500/30' : 'bg-slate-800/50 border-slate-700/50'"
      >
        <span class="text-xl font-bold tabular-nums" :class="alarmStats.critical > 0 ? 'text-danger-400' : 'text-slate-500'">
          {{ alarmStats.critical || 0 }}
        </span>
        <span class="text-xs text-slate-400 uppercase tracking-wider mt-1">严重</span>
      </div>
      <div
        class="flex flex-col items-center py-3 rounded-md transition-all duration-200 border"
        :class="alarmStats.error > 0 ? 'bg-danger-500/10 border-danger-500/20' : 'bg-slate-800/50 border-slate-700/50'"
      >
        <span class="text-xl font-bold tabular-nums" :class="alarmStats.error > 0 ? 'text-danger-300' : 'text-slate-500'">
          {{ alarmStats.error || 0 }}
        </span>
        <span class="text-xs text-slate-400 uppercase tracking-wider mt-1">错误</span>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="flex-1 overflow-y-auto p-3 bg-slate-900/30">
      <template v-if="filteredAlarms.length > 0">
        <div
          v-for="alarm in filteredAlarms"
          :key="alarm.alarmId"
          class="flex gap-3 p-3 mb-2 rounded-md cursor-pointer transition-all duration-200 border"
          :class="[
            alarm.read 
              ? 'bg-slate-800/30 hover:bg-slate-800/50 border-slate-700/30' 
              : 'bg-primary-500/8 hover:bg-primary-500/15 border-primary-500/20 shadow-sm',
          ]"
          @click="handleAlarmClick(alarm)"
        >
          <div
            class="w-1 shrink-0 rounded-full"
            :class="{
              'bg-danger-500 shadow-[0_0_8px_rgba(245,108,108,0.4)]': alarm.severity === 'critical',
              'bg-danger-400': alarm.severity === 'error',
              'bg-amber-500': alarm.severity === 'warning',
              'bg-slate-500': alarm.severity === 'info',
            }"
          ></div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-center mb-1.5">
              <span class="text-xs font-medium text-slate-300">{{ getAlarmTypeLabel(alarm.alarmType) }}</span>
              <span class="text-xs text-slate-500 font-mono">{{ formatTime(alarm.timestamp) }}</span>
            </div>
            <div class="text-xs text-slate-400 line-clamp-2 leading-relaxed">{{ alarm.message }}</div>
          </div>
        </div>
      </template>
      <div v-else class="flex flex-col items-center justify-center h-full text-slate-500">
        <el-icon class="text-4xl mb-3 text-emerald-500"><CircleCheck /></el-icon>
        <span class="text-sm font-medium">暂无告警</span>
        <span class="text-xs text-slate-600 mt-1">系统运行正常</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, CircleCheck } from '@element-plus/icons-vue'
import { useAlarmManager } from '../composables/useAlarmManager'

const props = defineProps({
  alarms: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['alarm-click', 'filter-change'])

const alarmManager = useAlarmManager()
const { filteredAlarms, alarmStats, getAlarmTypeLabel, clearAllAlarms, markAsRead } = alarmManager

watch(
  () => props.alarms,
  (newAlarms) => {
    if (newAlarms && newAlarms.length > 0) {
      alarmManager.addAlarm(newAlarms)
    }
  },
  { immediate: true, deep: true }
)

function formatTime(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function handleAlarmClick(alarm) {
  markAsRead(alarm.alarmId)
  emit('alarm-click', alarm)
}

function handleClearAll() {
  ElMessageBox.confirm('确定要清空所有告警吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      clearAllAlarms()
      ElMessage.success('已清空所有告警')
    })
    .catch(() => {})
}
</script>
