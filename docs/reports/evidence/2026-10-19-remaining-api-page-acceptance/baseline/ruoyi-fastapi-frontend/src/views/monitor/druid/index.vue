<template>
  <div class="p-4">
    <h2 class="mb-4">MSW Mock 测试 (模式: {{ mockMode }})</h2>
    <el-button type="primary" @click="testMock">测试 Mock 接口</el-button>
    <el-button type="success" @click="testReal">测试真实接口 (用户列表)</el-button>
    <pre
      v-if="result"
      class="mt-4 p-4 bg-zx-surface-card-fill text-zx-surface-card-on-text rounded"
      >{{ result }}</pre
    >
  </div>
</template>

<script setup>
import { ref } from 'vue';
import request from '@/utils/request';
import { resolveRuntimeConfig } from '@/mocks/runtime/mode';

const mockMode = resolveRuntimeConfig().mode;
const result = ref('');

async function testMock() {
  const data = await request({ url: '/test/mock', method: 'get' });
  result.value = JSON.stringify(data, null, 2);
}

async function testReal() {
  const data = await request({
    url: '/system/user/list',
    method: 'get',
    params: { page: 1, pageSize: 5 },
  });
  result.value = JSON.stringify(data, null, 2);
}
</script>
