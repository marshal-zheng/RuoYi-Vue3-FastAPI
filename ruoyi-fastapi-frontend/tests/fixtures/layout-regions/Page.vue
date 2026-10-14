<template>
  <el-table v-if="kind === 'native-table'" :data="[{ name: 'Native control' }]">
    <el-table-column prop="name" label="Name" />
  </el-table>
  <ZxContentWrap v-else-if="kind === 'list'" fill data-testid="fixture-list">
    <ZxGridList :load-data="load" fill :show-search="false">
      <template #table="{ grid }"
        ><el-table :data="grid.list"
          ><el-table-column prop="name" label="Name" /></el-table
      ></template>
    </ZxGridList>
  </ZxContentWrap>
  <ContentDetailWrap v-else-if="kind === 'mixed'" :data="summary" fill>
    <ZxTabs :items="tabs" fill />
  </ContentDetailWrap>
  <ContentDetailWrap v-else-if="kind === 'sticky-detail'" :data="summary">
    <div class="long-detail">Natural detail with sticky summary</div>
  </ContentDetailWrap>
  <FormBuilder v-else-if="kind === 'form-builder'" />
  <ZxContentWrap v-else-if="kind === 'editor'" fill>
    <template #header-right><span>Editor tools</span></template>
    <div data-testid="fixture-editor" data-zx-fill>
      <XFlow><XFlowGraph :readonly="true" /></XFlow>
    </div>
  </ZxContentWrap>
  <ZxPageLayout
    v-else-if="kind === 'nested'"
    fill
    scroll="none"
    data-zx-fill="anchor"
  >
    <template #header
      ><div class="fixture-summary">Outer summary</div></template
    >
    <ZxPageLayout fill scroll="none" data-testid="nested-region">
      <template #header><div class="fixture-tools">Tools</div></template>
      <div
        class="editor-canvas"
        data-zx-fill="anchor"
        data-testid="nested-canvas"
      />
    </ZxPageLayout>
  </ZxPageLayout>
  <ZxContentWrap v-else-if="kind === 'sticky'" title="Natural form" show-footer>
    <div class="long-detail">Long form</div>
  </ZxContentWrap>
  <ZxPageLayout v-else data-testid="fixture-detail">
    <h2>Natural detail</h2>
    <div :class="{ 'long-detail': kind === 'detail' }">Detail content</div>
  </ZxPageLayout>
</template>

<script setup lang="ts">
import { defineAsyncComponent, defineComponent, h } from 'vue';
import { ZxContentWrap, ZxGridList, ZxPageLayout, ZxTabs } from '@zxio/zxui';
import ContentDetailWrap from '@/components/ui/ContentDetailWrap/index.vue';
import { XFlow, XFlowGraph } from '@/components/business/ZxFlow';
const FormBuilder = defineAsyncComponent(
  () => import('@/views/tool/build/index.vue'),
);
defineProps<{ kind: string }>();
const load = async () => ({
  items: Array.from({ length: 80 }, (_, i) => ({ name: `Row ${i}` })),
  total: 80,
});
const summary = [
  { label: '名称', value: 'Fixture' },
  { label: '描述', value: 'Summary with a bounded list' },
];
const tabs = [
  {
    key: 'versions',
    label: 'Versions',
    component: defineComponent({
      setup: () => () =>
        h(ZxGridList, { fill: true, loadData: load, showSearch: false }),
    }),
  },
];
</script>

<style scoped>
.long-detail {
  min-height: 1600px;
}
.fixture-summary {
  height: 60px;
}
.fixture-tools {
  height: 30px;
}
.editor-canvas {
  flex: 1 1 0;
  min-height: 0;
  background: var(--el-fill-color-light);
}
</style>
