<template>
  <ZxConfigProvider :theme="fixtureTheme">
    <ZxThemePreferenceBridge>
      <main class="table-fixture">
        <h1>表格密度与状态验收</h1>
        <p>本地内存样例；不读写业务数据。用于验证固定列、长文本和行状态。</p>
        <label
          >密度
          <select :value="zxThemePreference.density" aria-label="密度" @change="setDensity">
            <option>compact</option>
            <option>default</option>
            <option>comfortable</option>
          </select></label
        >
        <label
          >尺寸
          <select v-model="size" aria-label="尺寸">
            <option>small</option>
            <option>default</option>
            <option>large</option>
          </select></label
        >
        <label><input v-model="wrapped" type="checkbox" />GridList 包裹</label>
        <label
          >显示比例
          <select :value="displayScale" aria-label="显示比例" @change="setDisplayScale">
            <option :value="100">100%</option>
            <option :value="125">125%</option>
          </select></label
        >
        <ZxGridList v-if="wrapped" :load-data="() => ({ list: rows })" :show-pagination="false">
          <template #table><SampleTable /></template>
        </ZxGridList>
        <SampleTable v-else />
        <h2>VXE 虚拟长表</h2>
        <button type="button" @click="prepareVariableRows">交错行高并定位第 160 行</button>
        <vxe-table
          ref="tableInstance"
          :data="virtualRows"
          :row-config="{ keyField: 'id' }"
          :scroll-y="{ enabled: true, gt: 0 }"
          height="420"
        >
          <vxe-column field="id" title="序号" width="110" />
          <vxe-column field="name" title="名称" width="260" />
          <vxe-column field="detail" title="描述" width="460" />
        </vxe-table>
      </main>
    </ZxThemePreferenceBridge>
  </ZxConfigProvider>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue';
import { ElTable, ElTableColumn, ElTag } from 'element-plus';
import type { VxeTableInstance } from 'vxe-table';
import { ZxButton, ZxConfigProvider, ZxGridList } from '@zxio/zxui';
import ZxThemePreferenceBridge from '@/theme/ZxThemePreferenceBridge';
import {
  setZxThemePreference,
  zxThemeConfig,
  zxThemePreference,
  type ZxThemeDensity,
} from '@/theme/zx-theme-config';

const size = ref<'small' | 'default' | 'large'>('default');
const wrapped = ref(true);
const displayScale = ref<100 | 125>(100);
const fixtureTheme = computed(() => ({
  ...zxThemeConfig.value,
  display: { profile: 'office' as const, scale: displayScale.value },
}));
const tableInstance = ref<VxeTableInstance>();
const virtualRows = Array.from({ length: 5000 }, (_, index) => ({
  id: index + 1,
  name: `虚拟行 ${index + 1}`,
  detail: `用于检查行锚点 ${index + 1}`,
}));
onMounted(() => Object.assign(window, { __zxVxeFixtureTable: tableInstance.value }));
async function prepareVariableRows() {
  const table = tableInstance.value;
  if (!table) return;
  const tall = virtualRows.filter((_, index) => index < 240 && index % 8 === 0);
  const medium = virtualRows.filter((_, index) => index < 240 && index % 8 === 4);
  await table.setRowHeight(tall, 84);
  await table.setRowHeight(medium, 60);
  await table.recalculate(true);
  const top = virtualRows
    .slice(0, 159)
    .reduce((height, row) => height + table.getRowHeight(row), 0);
  await table.scrollTo({ top: top + 12, left: 0 });
}
const rows = Array.from({ length: 12 }, (_, index) => ({
  id: index + 1,
  name: `样例 ${index + 1}`,
  detail: index === 1 ? '多行内容用于检查文本自然增高，不能被固定行高截断。'.repeat(4) : '单行内容',
}));
async function setDensity(event: Event) {
  const select = event.target as HTMLSelectElement;
  await setZxThemePreference({ density: select.value as ZxThemeDensity });
  select.value = zxThemePreference.value.density;
}
function setDisplayScale(event: Event) {
  displayScale.value = Number((event.target as HTMLSelectElement).value) as 100 | 125;
}
const SampleTable = defineComponent({
  setup: () => () =>
    h(
      ElTable,
      {
        data: rows,
        size: size.value,
        stripe: true,
        border: true,
        highlightCurrentRow: true,
        rowKey: 'id',
        maxHeight: 360,
      },
      () => [
        h(ElTableColumn, { type: 'selection', width: 48, fixed: 'left' }),
        h(ElTableColumn, {
          prop: 'name',
          label: '名称',
          width: 160,
          fixed: 'left',
        }),
        h(ElTableColumn, { prop: 'detail', label: '描述', width: 440 }),
        h(
          ElTableColumn,
          { label: '状态', width: 140 },
          { default: () => h(ElTag, {}, () => '可用') }
        ),
        h(
          ElTableColumn,
          { label: '操作', width: 160, fixed: 'right' },
          {
            default: () =>
              h('div', { class: 'op-col__wrap' }, [h(ZxButton, { text: true }, () => '查看')]),
          }
        ),
      ]
    ),
});
</script>

<style scoped>
.table-fixture {
  box-sizing: border-box;
  width: min(800px, 100%);
  margin: 24px auto;
  padding: 20px;
  background: var(--zx-semantic-surface-page);
  color: var(--zx-semantic-text-primary);
}
label {
  display: inline-block;
  margin: 0 16px 16px 0;
}
</style>
