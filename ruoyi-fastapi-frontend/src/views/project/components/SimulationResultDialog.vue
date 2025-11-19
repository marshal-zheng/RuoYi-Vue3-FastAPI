<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <template #header>
      <div class="simulation-dialog__header">
        <span>多总线仿真结果</span>
        <el-tag type="success" size="small">示意仿真</el-tag>
      </div>
    </template>

    <div v-if="simulationResult" class="simulation-summary">
      <el-descriptions :column="2" size="small" border>
        <el-descriptions-item label="设备数量">
          {{ simulationResult.summary.deviceCount }}
        </el-descriptions-item>
        <el-descriptions-item label="连线数量">
          {{ simulationResult.summary.connectionCount }}
        </el-descriptions-item>
        <el-descriptions-item label="覆盖总线">
          <el-space wrap>
            <el-tag
              v-for="bus in simulationResult.summary.busCoverage"
              :key="bus.name"
              size="small"
              :type="bus.active ? 'success' : 'info'"
              :effect="bus.active ? 'dark' : 'plain'"
            >
              {{ bus.name }}<span v-if="!bus.active">（未使用）</span>
            </el-tag>
          </el-space>
        </el-descriptions-item>
        <el-descriptions-item label="仿真时间">
          {{ simulationResult.summary.generatedAt }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-tabs v-model="simulationTab" class="simulation-tabs">
      <el-tab-pane label="仿真过程" name="timeline">
        <el-empty v-if="!simulationResult?.timeline?.length" description="暂无仿真数据" />
        <el-timeline class="p-4" v-else>
          <el-timeline-item
            v-for="item in simulationResult.timeline"
            :key="item.id"
            :timestamp="item.timestamp"
            :type="item.busTypeTag"
          >
            <p class="simulation-timeline__title">{{ item.title }}</p>
            <p class="simulation-timeline__desc">{{ item.description }}</p>
          </el-timeline-item>
        </el-timeline>
      </el-tab-pane>
      <el-tab-pane label="总线通信设计文件" name="design">
        <div class="simulation-file__header">
          <el-button
            type="primary"
            link
            @click="
              downloadSimulationFile(
                simulationResult.designFile.name,
                simulationResult.designFile.content
              )
            "
          >
            下载设计文件
          </el-button>
        </div>
        <pre class="simulation-file__viewer">{{ simulationResult.designFile.content }}</pre>
      </el-tab-pane>
      <el-tab-pane label="接口控制文件" name="icd">
        <div class="simulation-file__header">
          <el-button
            type="primary"
            link
            @click="
              downloadSimulationFile(
                simulationResult.icdFile.name,
                simulationResult.icdFile.content
              )
            "
          >
            下载接口控制文件
          </el-button>
        </div>
        <pre class="simulation-file__viewer">{{ simulationResult.icdFile.content }}</pre>
      </el-tab-pane>
    </el-tabs>
  </ZxDialog>
</template>

<script setup name="SimulationResultDialog">
import { ref } from 'vue';
import { useDialog } from '@zxio/zxui';

const simulationResult = ref(null);
const simulationTab = ref('timeline');

const dialog = useDialog({
  title: '多总线仿真结果',
  width: '75%',
  footer: false,
});

function open(payload) {
  simulationResult.value = payload || null;
  simulationTab.value = 'timeline';
  dialog.open();
}

function close() {
  dialog.close();
}

function downloadSimulationFile(filename, content) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || 'simulation.txt';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

defineExpose({
  open,
  close,
});
</script>

<style scoped lang="less">
.simulation-dialog__header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.simulation-summary {
  margin-bottom: 16px;
}

.simulation-tabs {
  .el-tab-pane {
    min-height: 240px;
  }
}

.simulation-file__header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.simulation-file__viewer {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  max-height: 280px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.simulation-timeline__title {
  font-weight: 600;
  margin-bottom: 4px;
}

.simulation-timeline__desc {
  color: #606266;
  margin: 0;
  font-size: 12px;
}
</style>
