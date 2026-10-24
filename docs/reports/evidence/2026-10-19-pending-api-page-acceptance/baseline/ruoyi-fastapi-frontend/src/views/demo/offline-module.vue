<template>
  <div class="offline-module">
    <el-result icon="info" :title="title" :sub-title="description">
      <template #extra>
        <div class="offline-module__actions">
          <el-button type="primary" @click="goProjectList">进入离线可用模块</el-button>
          <el-button @click="goHome">返回首页</el-button>
        </div>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const title = computed(() => `${String(route.meta.title ?? '当前模块')} 暂未开放`);
const description = computed(() => {
  const section = String(route.meta.offlineSection ?? '当前模块');
  return `demo-offline 当前只覆盖首页与工程管理核心链路，${section} 还未接入离线数据与接口模拟，因此此处先保留菜单壳，避免真实环境与离线环境导航结构完全脱节。`;
});

function goProjectList() {
  router.push('/project/project');
}

function goHome() {
  router.push('/index');
}
</script>

<style scoped>
.offline-module {
  min-height: 100cqh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.offline-module__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>
