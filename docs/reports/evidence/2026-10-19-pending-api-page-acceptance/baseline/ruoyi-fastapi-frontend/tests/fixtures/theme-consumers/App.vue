<template>
  <ZxConfigProvider :theme="zxThemeConfig">
    <main>
      <h1>主题消费验收</h1>
      <p>内存样例，不读写业务数据。原始图数据和正文颜色应保持不变。</p>
      <label
        >主题
        <select :value="zxThemePreference.themeId" aria-label="主题" @change="changeTheme">
          <option v-for="t in ZX_THEME_PACKAGE_CHOICES" :key="t.id" :value="t.id">
            {{ t.label }}
          </option>
        </select></label
      >
      <button
        @click="
          setZxThemePreference({
            mode: zxThemePreference.mode === 'dark' ? 'light' : 'dark',
          })
        "
      >
        切换明暗
      </button>
      <label
        >密度
        <select :value="zxThemePreference.density" aria-label="密度" @change="changeDensity">
          <option>compact</option>
          <option>default</option>
          <option>comfortable</option>
        </select>
      </label>
      <label
        >VXE 尺寸
        <select v-model="tableSize" aria-label="VXE 尺寸">
          <option value="">default</option>
          <option>medium</option>
          <option>small</option>
          <option>mini</option>
        </select>
      </label>
      <button @click="checkData">检查图数据</button>
      <button @click="contentBaseline = JSON.stringify([quill, rich])">记录正文基线</button>
      <button @click="checkContent">检查正文</button>
      <output data-testid="content-integrity">{{ contentIntegrity }}</output>
      <details>
        <summary>正文序列化证据</summary>
        <pre data-testid="content-baseline">{{ contentBaseline }}</pre>
        <pre data-testid="content-current">{{ JSON.stringify([quill, rich]) }}</pre>
      </details>
      <output data-testid="data-integrity">{{ unchanged }}</output>
      <section class="graph">
        <XFlow
          ><XFlowGraph :readonly="true" @ready="ready"
            ><XFlowGrid :size="14" type="mesh" /><XFlowBackground /></XFlowGraph
        ></XFlow>
      </section>
      <section>
        <h2>VXE 表格与编辑</h2>
        <button @click="lastRow">滚到末行</button>
        <button @click="firstRow">回到首行</button>
        <button @click="scrollReceipt = JSON.stringify(tableRef?.getScrollData())">
          读取滚动状态
        </button>
        <output data-testid="scroll-receipt">{{ scrollReceipt }}</output>
        <vxe-table
          ref="tableRef"
          data-testid="density-table"
          :size="tableSize"
          show-overflow="title"
          :virtual-y-config="{ enabled: true, gt: 20 }"
          :row-config="{ keyField: 'id' }"
          :data="rows"
          border
          stripe
          height="240"
          :edit-config="{ trigger: 'click', mode: 'cell' }"
          :menu-config="{
            body: { options: [[{ code: 'inspect', name: '查看样例' }]] },
          }"
          ><vxe-column type="checkbox" width="50" fixed="left" /><vxe-column
            field="name"
            title="名称"
            :edit-render="{ name: 'input' }" /><vxe-column field="detail" title="描述"
        /></vxe-table>
      </section>
      <section>
        <h2>嵌套紧凑密度</h2>
        <ZxConfigProvider :theme="{ density: 'compact' }">
          <vxe-table
            data-testid="nested-table"
            :data="rows.slice(0, 2)"
            show-overflow="title"
            border
          >
            <vxe-column field="name" title="名称" />
          </vxe-table>
        </ZxConfigProvider>
      </section>
      <section>
        <h2>Quill 公告编辑器</h2>
        <QuillEditor v-model="quill" type="base64" :height="130" />
      </section>
      <section>
        <h2>wangEditor 编辑器</h2>
        <RichEditor
          v-model="rich"
          height="300px"
          :show-toolbar="true"
          :editor-config="{ readOnly: false }"
        />
      </section>
    </main>
  </ZxConfigProvider>
</template>
<script setup lang="ts">
import { ref, shallowRef } from 'vue';
import { ZxConfigProvider } from '@zxio/zxui';
import type { VxeTableInstance, VxeTablePropTypes } from 'vxe-table';
import type { Graph } from '@antv/x6';
import { XFlow, XFlowGraph, XFlowGrid, XFlowBackground } from '@/components/business/ZxFlow';
import QuillEditor from '@/components/ui/Editor/index.vue';
import RichEditor from '@/components/ui/RichEditor/src/Editor.vue';
import { zxThemeConfig, zxThemePreference, setZxThemePreference } from '@/theme/zx-theme-config';
import { ZX_THEME_PACKAGE_CHOICES } from '@/theme/zx-theme-packages';
const graph = shallowRef<Graph>();
let original = '';
const unchanged = ref('等待图形');
const tableRef = shallowRef<VxeTableInstance>();
const tableSize = ref<VxeTablePropTypes.Size>('');
const scrollReceipt = ref('');
const contentBaseline = ref('');
const contentIntegrity = ref('尚未记录基线');
const rows = ref(
  Array.from({ length: 200 }, (_, index) => ({
    id: index + 1,
    name: index === 0 ? '可编辑字段' : index === 1 ? '第二行' : `字段 ${index + 1}`,
    detail: index === 0 ? '单击名称编辑；右键显示菜单' : `虚拟滚动样例 ${index + 1}`,
  }))
);
function checkContent() {
  contentIntegrity.value =
    contentBaseline.value === JSON.stringify([quill.value, rich.value])
      ? '正文未变化'
      : '正文有变化';
}
async function lastRow() {
  await tableRef.value?.scrollToRow(rows.value[rows.value.length - 1]);
}
async function firstRow() {
  await tableRef.value?.scrollTo({ top: 0 });
}
function changeDensity(e: Event) {
  setZxThemePreference({
    density: (e.target as HTMLSelectElement).value as 'compact' | 'default' | 'comfortable',
  });
}
const quill = ref('<p>默认正文 <span style="color: rgb(255, 0, 0);">用户指定红色</span></p>');
const rich = ref('<p>只读正文 <span style="color: rgb(255, 0, 0);">用户指定红色</span></p>');
function ready(value: Graph) {
  graph.value = value;
  value.fromJSON({
    nodes: [
      {
        id: 'sample',
        shape: 'rect',
        x: 60,
        y: 35,
        width: 220,
        height: 65,
        label: '业务颜色保持原值',
        attrs: { body: { fill: '#247a55' }, label: { fill: '#ffffff' } },
      },
    ],
  });
  original = JSON.stringify(value.toJSON());
  checkData();
}
function checkData() {
  unchanged.value =
    JSON.stringify(graph.value?.toJSON()) === original ? '图数据未变化' : '图数据有变化';
}
function changeTheme(e: Event) {
  setZxThemePreference({ themeId: (e.target as HTMLSelectElement).value });
}
</script>
<style scoped>
main {
  max-width: 1000px;
  padding: 24px;
  margin: auto;
  color: var(--zx-semantic-text-primary);
  background: var(--zx-semantic-surface-page);
}
.graph {
  height: 150px;
  margin-block: 16px;
}
section {
  margin-block: 16px;
}
button,
select {
  margin-inline: 8px;
}
</style>
