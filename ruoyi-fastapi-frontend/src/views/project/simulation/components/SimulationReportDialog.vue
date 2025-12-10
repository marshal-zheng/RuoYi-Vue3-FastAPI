<template>
  <el-dialog
    v-model="visible"
    title="仿真报告"
    width="800px"
    destroy-on-close
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
.simulation-report {
  color: #e2e8f0;
  background: #0b1220;

  &__summary {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: #e2e8f0;
    }
  }

  &__summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  &__summary-item {
    padding: 16px;
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.28);
  }

  &__summary-label {
    display: block;
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
  }

  &__summary-value {
    display: block;
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
  }

  &__section {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 12px;
      font-size: 16px;
      font-weight: 600;
      color: #e2e8f0;
    }

    :deep(.el-table) {
      background: rgba(15, 23, 42, 0.75);
      color: #e2e8f0;
      border-radius: 8px;
    }

    :deep(.el-table th) {
      background: rgba(30, 41, 59, 0.9);
      color: #cbd5e1;
    }

    :deep(.el-table tr) {
      background: rgba(15, 23, 42, 0.6);
    }

    :deep(.el-table__body tr:hover > td) {
      background: rgba(59, 130, 246, 0.08);
    }
  }
}
</style>
