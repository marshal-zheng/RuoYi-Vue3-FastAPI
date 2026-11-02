<template>
  <ZxConfigProvider :theme="zxThemeConfig">
    <main style="padding: 20px; max-width: 1400px; margin: auto">
      <h1>部门资源真实业务验收</h1>
      <p>真实部门列表、两个生产编辑器及两个资源树订阅；使用同一应用客户端。</p>
      <button data-testid="open-both" @click="openBoth">同时打开两个编辑器</button>
      <button data-testid="open-right" @click="right?.open({ deptId })">重新打开右侧</button>
      <p data-testid="opening">{{ opening }}</p>
      <div style="display: flex; gap: 24px">
        <p data-testid="tree-left">树订阅 A：{{ ownLabel(leftTree.data.value) }}</p>
        <p data-testid="tree-right">树订阅 B：{{ ownLabel(rightTree.data.value) }}</p>
      </div>
      <div style="height: 420px"><DeptList /></div>
      <DeptDlg ref="left" class="resource-editor-left" :modal="false" /><DeptDlg
        ref="right"
        class="resource-editor-right"
        :modal="false"
      />
    </main>
  </ZxConfigProvider>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { ZxConfigProvider } from '@zxio/zxui/config-provider';
import { zxThemeConfig } from '@/theme/zx-theme-config';
import type { DeepReadonly } from 'vue';
import { useResourceQuery } from '@zxio/vue-query/resources';
import { dataClient } from '@/queries/client';
import { departmentResource } from '@/queries/system/dept';
import type { MenuTreeNode } from '@/api/system/menu';
import DeptList from '@/views/system/dept/components/DeptList.vue';
import DeptDlg from '@/views/system/dept/components/DeptDlg.vue';
const deptId = Number(new URLSearchParams(location.search).get('id'));
const left = ref<InstanceType<typeof DeptDlg>>();
const right = ref<InstanceType<typeof DeptDlg>>();
const opening = ref('ready');
const leftTree = useResourceQuery(departmentResource, 'userTree', undefined, {
  client: dataClient,
});
const rightTree = useResourceQuery(departmentResource, 'userTree', undefined, {
  client: dataClient,
});
function ownLabel(nodes: DeepReadonly<MenuTreeNode[]> | undefined): string {
  for (const node of nodes ?? []) {
    if (node.id === deptId) return node.label;
    const child = ownLabel(node.children);
    if (child) return child;
  }
  return '';
}
async function openBoth() {
  opening.value = 'loading';
  try {
    await Promise.all([left.value?.open({ deptId }), right.value?.open({ deptId })]);
    opening.value = 'loaded';
  } catch {
    opening.value = 'failed';
  }
}
</script>

<style>
.resource-editor-left {
  width: 46vw !important;
  margin-left: 2vw !important;
}
.resource-editor-right {
  width: 46vw !important;
  margin-left: 52vw !important;
}
</style>
