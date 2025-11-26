<template>
  <transition name="fade-slide">
    <zx-floating-panel
      v-if="visible"
      title="告警信息"
      :position="position"
      :size="size"
      :collapsed-size="collapsedSize"
      :default-collapsed="defaultCollapsed"
    >
      <template #header>
        <div class="alarm-panel__header">
          <span class="alarm-panel__title">告警信息</span>
          <transition name="badge-bounce">
            <el-badge :value="alarmStats.total" :max="99" type="danger" :key="alarmStats.total" />
          </transition>
        </div>
      </template>

      <template #actions>
        <el-button
          size="small"
          icon="Delete"
          :disabled="alarms.length === 0"
          @click="handleClearAll"
        >
          清空
        </el-button>
        <el-button
          type="primary"
          size="small"
          icon="Download"
          :disabled="alarms.length === 0"
          @click="handleExport"
        >
          导出
        </el-button>
      </template>

      <div class="alarm-panel__content">
        <div class="alarm-stats">
          <div class="stat-card" :class="{ active: alarmStats.critical > 0 }">
            <div class="stat-icon critical">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ alarmStats.critical || 0 }}</div>
              <div class="stat-label">严重</div>
            </div>
          </div>
          <div class="stat-card" :class="{ active: alarmStats.error > 0 }">
            <div class="stat-icon error">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ alarmStats.error || 0 }}</div>
              <div class="stat-label">错误</div>
            </div>
          </div>
          <div class="stat-card" :class="{ active: alarmStats.warning > 0 }">
            <div class="stat-icon warning">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ alarmStats.warning || 0 }}</div>
              <div class="stat-label">警告</div>
            </div>
          </div>
          <div class="stat-card" :class="{ active: alarmStats.info > 0 }">
            <div class="stat-icon info">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ alarmStats.info || 0 }}</div>
              <div class="stat-label">信息</div>
            </div>
          </div>
        </div>

        <div class="alarm-filters">
          <el-select
            v-model="filterSeverity"
            placeholder="严重程度"
            clearable
            size="small"
            style="width: 120px"
          >
            <el-option label="全部" value="" />
            <el-option label="严重" value="critical" />
            <el-option label="错误" value="error" />
            <el-option label="警告" value="warning" />
            <el-option label="信息" value="info" />
          </el-select>
          <el-select
            v-model="filterType"
            placeholder="告警类型"
            clearable
            size="small"
            style="width: 140px; margin-left: 8px"
          >
            <el-option label="全部" value="" />
            <el-option
              v-for="type in alarmTypes"
              :key="type"
              :label="getAlarmTypeLabel(type)"
              :value="type"
            />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索告警"
            clearable
            size="small"
            style="width: 200px; margin-left: 8px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="alarm-list" style="height: 280px">
          <transition name="fade" mode="out-in">
            <SkeletonLoader v-if="isLoading" type="card" key="loading" />
            <el-empty
              v-else-if="filteredAlarms.length === 0"
              description="暂无告警信息"
              key="empty"
            />
            <div v-else class="alarm-items" key="list">
              <transition-group name="alarm-list" tag="div">
                <div
                  v-for="alarm in filteredAlarms"
                  :key="alarm.alarmId"
                  class="alarm-item"
                  :class="[`severity-${alarm.severity}`, { unread: !alarm.read }]"
                  @click="handleAlarmClick(alarm)"
                >
                  <div class="alarm-icon">
                    <el-icon>
                      <component :is="getSeverityIcon(alarm.severity)" />
                    </el-icon>
                  </div>
                  <div class="alarm-content">
                    <div class="alarm-header">
                      <el-tag :type="getSeverityTagType(alarm.severity)" size="small" effect="dark">
                        {{ getSeverityLabel(alarm.severity) }}
                      </el-tag>
                      <el-tag size="small" effect="plain">
                        {{ getAlarmTypeLabel(alarm.alarmType) }}
                      </el-tag>
                      <span class="alarm-time">{{ formatTime(alarm.timestamp) }}</span>
                    </div>
                    <div class="alarm-message">{{ alarm.message }}</div>
                    <div
                      v-if="alarm.affectedNodes && alarm.affectedNodes.length > 0"
                      class="alarm-nodes"
                    >
                      <span class="nodes-label">受影响节点:</span>
                      <el-tag
                        v-for="(node, index) in alarm.affectedNodes"
                        :key="index"
                        size="small"
                        type="info"
                        effect="plain"
                      >
                        {{ node }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </transition-group>
            </div>
          </transition>
        </div>
      </div>
    </zx-floating-panel>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  CircleCloseFilled,
  WarningFilled,
  Warning,
  InfoFilled,
  Search,
} from '@element-plus/icons-vue';
import { useAlarmManager } from '../composables/useAlarmManager';
import SkeletonLoader from './SkeletonLoader.vue';

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
    default: () => ({ top: '100px', left: '30px' }),
  },
  size: {
    type: Object,
    default: () => ({ width: '380px', maxHeight: '500px' }),
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

const emit = defineEmits(['alarm-click', 'export', 'clear']);

const isLoading = ref(false);
const visible = computed(() => props.alarms && props.alarms.length > 0);

const alarmManager = useAlarmManager();
const {
  filteredAlarms,
  alarmStats,
  alarmTypes,
  filterSeverity,
  filterType,
  searchKeyword,
  getSeverityLabel,
  getAlarmTypeLabel,
  exportAlarms,
  clearAllAlarms,
  markAsRead,
} = alarmManager;

// 同步外部告警数据（去重处理已在 useAlarmManager 中实现）
watch(
  () => props.alarms,
  (newAlarms) => {
    if (newAlarms && newAlarms.length > 0) {
      isLoading.value = true;
      setTimeout(() => {
        alarmManager.addAlarm(newAlarms);
        isLoading.value = false;
      }, 250);
    }
  },
  { immediate: true, deep: true }
);

/**
 * 获取严重程度图标
 */
function getSeverityIcon(severity) {
  const iconMap = {
    critical: CircleCloseFilled,
    error: WarningFilled,
    warning: Warning,
    info: InfoFilled,
  };
  return iconMap[severity] || InfoFilled;
}

/**
 * 获取严重程度标签类型
 */
function getSeverityTagType(severity) {
  const typeMap = {
    critical: 'danger',
    error: 'danger',
    warning: 'warning',
    info: 'info',
  };
  return typeMap[severity] || 'info';
}

/**
 * 格式化时间
 */
function formatTime(timestamp) {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
}

/**
 * 处理告警点击
 */
function handleAlarmClick(alarm) {
  markAsRead(alarm.alarmId);
  emit('alarm-click', alarm);
}

/**
 * 清空所有告警
 */
function handleClearAll() {
  ElMessageBox.confirm('确定要清空所有告警吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      clearAllAlarms();
      emit('clear');
      ElMessage.success('已清空所有告警');
    })
    .catch(() => {});
}

/**
 * 导出告警数据
 */
function handleExport() {
  const csvContent = exportAlarms('csv');

  // 下载文件
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `simulation_alarms_${new Date().getTime()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  ElMessage.success('导出成功');
  emit('export', csvContent);
}
</script>

<style lang="less" scoped>
.alarm-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alarm-panel__title {
  font-weight: 600;
  font-size: 14px;
}

.alarm-panel__content {
  padding: 8px 0;
}

.alarm-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  transition: all 0.3s;

  &.active {
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

.stat-icon {
  font-size: 24px;

  &.critical {
    color: #c03639;
  }

  &.error {
    color: #f56c6c;
  }

  &.warning {
    color: #e6a23c;
  }

  &.info {
    color: #909399;
  }
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.alarm-filters {
  display: flex;
  margin-bottom: 16px;
}

.alarm-list {
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.alarm-items {
  padding: 8px;
}

.alarm-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  &.unread {
    background: #f0f9ff;
    border-left: 3px solid #409eff;
  }

  &.severity-critical {
    border-left-color: #c03639;
  }

  &.severity-error {
    border-left-color: #f56c6c;
  }

  &.severity-warning {
    border-left-color: #e6a23c;
  }

  &.severity-info {
    border-left-color: #909399;
  }
}

.alarm-icon {
  font-size: 20px;
  padding-top: 2px;
}

.alarm-content {
  flex: 1;
}

.alarm-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.alarm-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.alarm-message {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.5;
}

.alarm-nodes {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nodes-label {
  font-size: 12px;
  color: #909399;
}

/* Transition animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.badge-bounce-enter-active {
  animation: badge-bounce 0.5s ease;
}

@keyframes badge-bounce {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.alarm-list-enter-active,
.alarm-list-leave-active {
  transition: all 0.4s ease;
}

.alarm-list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.alarm-list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.alarm-list-move {
  transition: transform 0.4s ease;
}
</style>
