<template>
  <ZxContentWrap title="数据库监控" data-testid="database-monitor" fill>
    <template #header-right>
      <ZxButton :loading="loading" @click="refresh">刷新监控数据</ZxButton>
    </template>
    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
    <div v-loading="loading" class="database-monitor">
      <el-descriptions v-if="pool" title="数据库连接池" :column="2" border>
        <el-descriptions-item label="状态">{{ pool.message }}</el-descriptions-item>
        <el-descriptions-item label="使用率">{{ pool.usageRate }}%</el-descriptions-item>
        <el-descriptions-item label="常驻连接数">{{ pool.poolSize }}</el-descriptions-item>
        <el-descriptions-item label="使用中连接">{{ pool.checkedOut }}</el-descriptions-item>
        <el-descriptions-item label="最大容量">{{ pool.totalCapacity }}</el-descriptions-item>
        <el-descriptions-item label="可用容量">{{ pool.available }}</el-descriptions-item>
      </el-descriptions>
      <el-descriptions v-if="stats" title="查询统计（本次服务启动以来）" :column="2" border>
        <el-descriptions-item label="查询次数">{{ stats.totalQueries }}</el-descriptions-item>
        <el-descriptions-item label="慢查询次数">{{ stats.slowQueries }}</el-descriptions-item>
        <el-descriptions-item label="慢查询比例">{{ stats.slowQueryRate }}</el-descriptions-item>
        <el-descriptions-item label="平均耗时">{{ stats.avgTimeMs }} ms</el-descriptions-item>
        <el-descriptions-item label="最大耗时">{{ stats.maxTimeMs }} ms</el-descriptions-item>
        <el-descriptions-item label="N+1 检测次数">{{
          stats.nPlusOneDetected
        }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </ZxContentWrap>
</template>

<script setup lang="ts">
import { onMounted, onScopeDispose, ref, shallowRef } from 'vue';
import { getDatabasePoolHealth, getDatabaseQueryStats } from '@/api/monitor/database';
import type { DatabasePoolHealth, DatabaseQueryStats } from '@/api/monitor/database';

const pool = shallowRef<DatabasePoolHealth>();
const stats = shallowRef<DatabaseQueryStats>();
const error = ref('');
const loading = ref(false);
const controller = new AbortController();
async function refresh() {
  if (loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    const [health, queries] = await Promise.all([
      getDatabasePoolHealth(controller.signal),
      getDatabaseQueryStats(controller.signal),
    ]);
    if (controller.signal.aborted) return;
    pool.value = health;
    stats.value = queries;
  } catch (failure) {
    if (!controller.signal.aborted)
      error.value = failure instanceof Error ? failure.message : '数据库监控加载失败，请重试';
  } finally {
    loading.value = false;
  }
}
onMounted(refresh);
onScopeDispose(() => controller.abort());
</script>

<style scoped>
.database-monitor {
  display: grid;
  gap: 24px;
}
</style>
