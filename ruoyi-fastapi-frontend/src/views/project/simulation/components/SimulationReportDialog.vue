<template>
  <el-dialog
    v-model="visible"
    title="仿真报告"
    width="800px"
    destroy-on-close
    class="simulation-dialog"
  >
    <div class="simulation-report">
      <!-- 摘要信息 -->
      <div class="simulation-report__summary">
        <h3>仿真摘要</h3>
        <div class="simulation-report__summary-grid">
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">开始时间</span>
            <span class="simulation-report__summary-value">{{ summary?.startTime || '-' }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">运行时长</span>
            <span class="simulation-report__summary-value">{{ summary?.duration || '-' }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">报文总数</span>
            <span class="simulation-report__summary-value">{{ summary?.messageCount || 0 }}</span>
          </div>
          <div class="simulation-report__summary-item">
            <span class="simulation-report__summary-label">告警数量</span>
            <span class="simulation-report__summary-value">{{ summary?.alarmCount || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 带宽统计 -->
      <div class="simulation-report__section">
        <h3>带宽统计</h3>
        <el-table :data="summary?.bandwidthStats || []" stripe>
          <el-table-column prop="protocol" label="协议类型" />
          <el-table-column prop="avgBandwidth" label="平均带宽" />
          <el-table-column prop="maxBandwidth" label="峰值带宽" />
          <el-table-column prop="avgLoad" label="平均负载" />
        </el-table>
      </div>

      <!-- 告警汇总 -->
      <div class="simulation-report__section">
        <h3>告警汇总</h3>
        <el-table :data="summary?.alarmStats || []" stripe>
          <el-table-column prop="type" label="告警类型" />
          <el-table-column prop="count" label="数量" />
          <el-table-column prop="level" label="级别">
            <template #default="{ row }">
              <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" @click="handleExport">导出报告</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  sessionId: {
    type: String,
    default: '',
  },
  summary: {
    type: Object,
    default: null,
  },
})

const visible = ref(false)

function open() {
  visible.value = true
}

function getLevelType(level) {
  const map = {
    error: 'danger',
    warning: 'warning',
    info: 'info',
  }
  return map[level] || 'info'
}

function handleExport() {
  // TODO: 报告导出逻辑待实现
}

defineExpose({ open })
</script>

<style lang="less" scoped>
@import '../styles/simulation-dialog-theme.less';

.simulation-report {
  color: @sim-dialog-text-primary;

  &__summary {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: @sim-dialog-text-primary;
    }
  }

  &__summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  &__summary-item {
    .sim-dialog-card();
    padding: 16px;
    text-align: center;
  }

  &__summary-label {
    display: block;
    font-size: 12px;
    color: @sim-dialog-text-secondary;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
  }

  &__summary-value {
    display: block;
    font-size: 18px;
    font-weight: 700;
    color: @sim-dialog-text-white;
  }

  &__section {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 600;
      color: @sim-dialog-text-primary;
    }
  }
}
</style>
