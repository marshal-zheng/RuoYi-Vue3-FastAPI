<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <template #header>
      <div class="flex items-center gap-2.5 font-semibold text-base">
        <el-icon :size="20" class="text-primary"><Monitor /></el-icon>
        <span>健康自检报告</span>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <span class="text-xs text-gray-400">检查时间: {{ formatTime(report?.timestamp) }}</span>
        <div class="flex gap-2">
          <el-button @click="handleRecheck">
            <el-icon><Refresh /></el-icon>
            重新检查
          </el-button>
          <el-button type="primary" @click="dialog.close()">确定</el-button>
        </div>
      </div>
    </template>

    <!-- 检查结果汇总 -->
    <div
      class="flex items-center gap-4 p-5 rounded-lg mb-5"
      :class="summaryBgClass"
    >
      <div :class="summaryIconClass">
        <el-icon :size="32">
          <component :is="summaryIcon" />
        </el-icon>
      </div>
      <div class="flex-1">
        <div class="text-base font-semibold text-gray-800 mb-1">{{ summaryTitle }}</div>
        <div class="text-sm text-gray-500">{{ summaryDesc }}</div>
      </div>
      <div class="flex gap-4">
        <div class="flex flex-col items-center min-w-[50px]">
          <span class="text-2xl font-bold text-green-500">{{ report?.passedChecks || 0 }}</span>
          <span class="text-xs text-gray-400">通过</span>
        </div>
        <div class="flex flex-col items-center min-w-[50px]">
          <span class="text-2xl font-bold text-amber-500">{{ report?.warningChecks || 0 }}</span>
          <span class="text-xs text-gray-400">警告</span>
        </div>
        <div class="flex flex-col items-center min-w-[50px]">
          <span class="text-2xl font-bold text-red-500">{{ report?.errorChecks || 0 }}</span>
          <span class="text-xs text-gray-400">错误</span>
        </div>
      </div>
    </div>

    <!-- 检查项详情 -->
    <div class="max-h-[400px] overflow-y-auto">
      <el-collapse v-model="activeCategories">
        <el-collapse-item
          v-for="(items, category) in groupedItems"
          :key="category"
          :name="category"
        >
          <template #title>
            <div class="flex items-center justify-between w-full pr-3">
              <span class="font-medium">{{ category }}</span>
              <div class="flex gap-1.5">
                <el-tag
                  v-if="getCategoryStats(items).error > 0"
                  type="danger"
                  size="small"
                  effect="dark"
                >
                  {{ getCategoryStats(items).error }} 错误
                </el-tag>
                <el-tag
                  v-if="getCategoryStats(items).warning > 0"
                  type="warning"
                  size="small"
                  effect="dark"
                >
                  {{ getCategoryStats(items).warning }} 警告
                </el-tag>
                <el-tag
                  v-if="getCategoryStats(items).success > 0"
                  type="success"
                  size="small"
                  effect="plain"
                >
                  {{ getCategoryStats(items).success }} 通过
                </el-tag>
              </div>
            </div>
          </template>

          <div class="flex flex-col gap-2 py-2">
            <div
              v-for="item in items"
              :key="item.id"
              class="flex gap-3 p-3 rounded-md"
              :class="getItemBgClass(item.status)"
            >
              <div class="shrink-0 mt-0.5" :class="getItemIconClass(item.status)">
                <el-icon :size="18">
                  <component :is="getStatusIcon(item.status)" />
                </el-icon>
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-800 mb-1">{{ item.name }}</div>
                <div class="text-sm text-gray-600 break-words">{{ item.message }}</div>
                <div
                  v-if="item.suggestion"
                  class="flex items-start gap-1 mt-2 p-2 text-xs text-blue-600 bg-blue-50 rounded"
                >
                  <el-icon class="shrink-0 mt-0.5"><InfoFilled /></el-icon>
                  <span>{{ item.suggestion }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </ZxDialog>
</template>

<script setup name="HealthCheckDialog">
import { ref, computed } from 'vue';
import {
  Monitor,
  CircleCheckFilled,
  WarningFilled,
  CircleCloseFilled,
  InfoFilled,
  Refresh,
} from '@element-plus/icons-vue';
import { useDialog } from '@zxio/zxui';
import { useHealthCheck } from '../composables/useHealthCheck';

const { groupItemsByCategory } = useHealthCheck();

const report = ref(null);
const activeCategories = ref([]);

const emit = defineEmits(['recheck']);

const dialog = useDialog({
  title: '健康自检报告',
  width: '680px',
  showCancel: false,
  footer: false,
});

// 汇总背景样式
const summaryBgClass = computed(() => {
  if (!report.value) return 'bg-gray-50';
  if (report.value.healthy) return 'bg-gradient-to-r from-green-50 to-emerald-50';
  if (report.value.canSimulate) return 'bg-gradient-to-r from-amber-50 to-yellow-50';
  return 'bg-gradient-to-r from-red-50 to-rose-50';
});

// 汇总图标样式
const summaryIconClass = computed(() => {
  if (!report.value) return 'text-gray-400';
  if (report.value.healthy) return 'text-green-500';
  if (report.value.canSimulate) return 'text-amber-500';
  return 'text-red-500';
});

// 汇总图标
const summaryIcon = computed(() => {
  if (!report.value) return CircleCheckFilled;
  if (report.value.healthy) return CircleCheckFilled;
  if (report.value.canSimulate) return WarningFilled;
  return CircleCloseFilled;
});

// 汇总标题
const summaryTitle = computed(() => {
  if (!report.value) return '检查中...';
  if (report.value.healthy) return '健康检查通过';
  if (report.value.canSimulate) return '检查完成，存在警告';
  return '检查未通过';
});

// 汇总描述
const summaryDesc = computed(() => {
  if (!report.value) return '';
  if (report.value.healthy) {
    return '所有配置检查均已通过，可以安全执行仿真';
  }
  if (report.value.canSimulate) {
    return '存在一些配置警告，但不影响仿真执行';
  }
  return '存在配置错误，请根据建议修复后再执行仿真';
});

// 分组检查项
const groupedItems = computed(() => {
  if (!report.value?.items) return {};
  return groupItemsByCategory(report.value.items);
});

// 获取分类统计
function getCategoryStats(items) {
  return {
    success: items.filter((i) => i.status === 'success').length,
    warning: items.filter((i) => i.status === 'warning').length,
    error: items.filter((i) => i.status === 'error').length,
  };
}

// 获取状态图标
function getStatusIcon(status) {
  switch (status) {
    case 'success':
      return CircleCheckFilled;
    case 'warning':
      return WarningFilled;
    case 'error':
      return CircleCloseFilled;
    default:
      return InfoFilled;
  }
}

// 获取检查项背景样式
function getItemBgClass(status) {
  switch (status) {
    case 'success':
      return 'bg-gray-50';
    case 'warning':
      return 'bg-amber-50 border-l-[3px] border-amber-400';
    case 'error':
      return 'bg-red-50 border-l-[3px] border-red-400';
    default:
      return 'bg-gray-50';
  }
}

// 获取检查项图标样式
function getItemIconClass(status) {
  switch (status) {
    case 'success':
      return 'text-green-500';
    case 'warning':
      return 'text-amber-500';
    case 'error':
      return 'text-red-500';
    default:
      return 'text-gray-400';
  }
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// 打开对话框
function open(healthReport) {
  report.value = healthReport;
  // 默认展开有问题的分类
  if (healthReport?.items) {
    const categories = [...new Set(healthReport.items.map((i) => i.category))];
    activeCategories.value = categories.filter((cat) => {
      const items = healthReport.items.filter((i) => i.category === cat);
      return items.some((i) => i.status !== 'success');
    });
    // 如果全部通过，展开所有
    if (activeCategories.value.length === 0) {
      activeCategories.value = categories;
    }
  }
  dialog.open();
}

// 关闭对话框
function close() {
  dialog.close();
}

// 重新检查
function handleRecheck() {
  emit('recheck');
}

defineExpose({
  open,
  close,
});
</script>
