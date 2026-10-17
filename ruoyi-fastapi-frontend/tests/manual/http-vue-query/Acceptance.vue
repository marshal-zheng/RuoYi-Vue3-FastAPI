<template>
  <ZxConfigProvider :theme="zxThemeConfig">
    <main>
      <h1>共享字典真实 API 验收</h1>
      <p>使用当前登录会话、应用 QueryClient、真实领域组件与真实 API。此页不安装 HTTP mock。</p>
      <p role="status">{{ sessionStatus }}；scope={{ queryScope?.key ?? '未建立' }}</p>
      <p v-if="actionError" role="alert">{{ actionError }}</p>
      <div class="controls">
        <button :disabled="!queryScope" @click="endQuerySession">结束查询会话范围</button>
        <button :disabled="!!queryScope" @click="restoreQueryScope">恢复当前登录用户范围</button>
      </div>
      <fieldset :disabled="!queryScope || busy">
        <legend>受控多行样本</legend>
        <label>字典类型（逗号分隔）<input v-model="typeInput" aria-label="字典类型" /></label>
        <div class="controls">
          <button @click="runRows(false)">8 行同类型（复用缓存）</button>
          <button @click="runRows(false, true)">3 类型 9 行（复用缓存）</button>
          <button @click="runRows(true)">清字典缓存并冷启 8 行</button>
          <button @click="runRows(true, true)">清字典缓存并冷启 3 类型 9 行</button>
          <button @click="addRow">新增同类型一行</button>
          <button :disabled="rows.length < 2" @click="rows.shift()">卸载第一行</button>
          <button data-testid="refresh-active" @mousedown.prevent @click="refresh">
            刷新活跃字典
          </button>
        </div>
      </fieldset>
      <fieldset :disabled="!queryScope || writing || !writeFixtureReady">
        <legend>临时验收项真实写入（仅改标签）</legend>
        <p>
          dictType={{ qaType || '未指定' }}；dictId={{ qaDictId ?? '未指定' }}；dictCode={{
            qaItemId ?? '未指定'
          }}
        </p>
        <label>新标签<input v-model="writeLabel" aria-label="临时项新标签" /></label>
        <button data-testid="write-qa-label" @mousedown.prevent @click="writeQaLabel">
          保存临时项标签
        </button>
        <output data-testid="write-status">{{ writeStatus }}</output>
      </fieldset>
      <p>行数={{ rows.length }}；活跃类型数={{ activeTypes.length }}；测量={{ runLabel }}</p>
      <p>
        已完成字典请求资源条目={{ resourceCount }}（失败/中止及精确请求数以浏览器 Network 为准）
      </p>
      <table aria-label="真实字典消费者">
        <thead>
          <tr>
            <th>行 / 类型</th>
            <th>DictSelect</th>
            <th>DictAutocomplete</th>
            <th>useDict → DictTag</th>
            <th>公共状态 / 提交值</th>
          </tr>
        </thead>
        <tbody>
          <DictRow
            v-for="row in rows"
            :key="row.id"
            :row-id="row.id"
            :dict-type="row.type"
            @mounted="onRowMounted"
          />
        </tbody>
      </table>
      <h2>原生 Query 状态</h2>
      <table aria-label="原生 Query 状态">
        <thead>
          <tr>
            <th>queryKey</th>
            <th>status</th>
            <th>fetchStatus</th>
            <th>选项数</th>
            <th>订阅数</th>
            <th>错误</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="query in snapshots" :key="query.key">
            <td>{{ query.key }}</td>
            <td>{{ query.status }}</td>
            <td>{{ query.fetchStatus }}</td>
            <td>{{ query.count }}</td>
            <td>{{ query.observers }}</td>
            <td>{{ query.error }}</td>
          </tr>
        </tbody>
      </table>
      <h2>当前操作 performance marks（毫秒）</h2>
      <p>
        start → mount / nextTick / rAF 是渲染时序；首次 data-ready 与 ready-paint
        单独记录。数据就绪不等于网络完成。
      </p>
      <table aria-label="渲染指标">
        <thead>
          <tr>
            <th>mark</th>
            <th>距操作开始 ms</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="mark in marks" :key="mark.name">
            <td>{{ mark.name }}</td>
            <td>{{ mark.ms.toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </main>
  </ZxConfigProvider>
</template>
<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { ZxConfigProvider } from '@zxio/zxui';
import { queryClient } from '@/queries/client';
import { endQuerySession, queryScope } from '@/queries/context';
import { dictCommands, dictKeys } from '@/queries/system/dict';
import { getData } from '@/api/system/dict/data';
import { getType } from '@/api/system/dict/type';
import useUserStore from '@/store/modules/user';
import { zxThemeConfig } from '@/theme/zx-theme-config';
import DictRow from './DictRow.vue';

const user = useUserStore();
// Writes require an explicitly supplied disposable fixture; the default page only reads.
const fixtureParams = new URLSearchParams(window.location.search);
const qaType = fixtureParams.get('type')?.trim() ?? '';
function positiveId(value: string | null): number | null {
  if (!value || !/^[1-9]\d*$/.test(value)) return null;
  const id = Number(value);
  return Number.isSafeInteger(id) ? id : null;
}
const qaDictId = positiveId(fixtureParams.get('dictId'));
const qaItemId = positiveId(fixtureParams.get('itemId'));
const writeFixtureReady =
  qaType.startsWith('codex_') && qaType.length > 6 && qaDictId !== null && qaItemId !== null;
const typeInput = ref(
  writeFixtureReady
    ? `${qaType},sys_normal_disable,sys_user_sex`
    : 'sys_normal_disable,sys_user_sex,sys_yes_no'
);
const writeLabel = ref('验收选项乙');
const writeStatus = ref(
  writeFixtureReady ? '尚未写入' : '写入已禁用：请通过 URL 指定 codex_ 临时类型、dictId 与 itemId'
);
const writing = ref(false);
const rows = ref<{ id: number; type: string }[]>([]);
const busy = ref(false);
const sessionStatus = ref('正在恢复当前登录会话');
const actionError = ref('');
const revision = ref(0);
const marks = ref<{ name: string; ms: number }[]>([]);
const runLabel = ref('尚未开始');
const resourceCount = ref(0);
let nextRow = 0;
let run = 0;
let startedAt = 0;
let readyRecorded = false;
let settledRecorded = false;
let mountedRecorded = false;
let resourceObserver: PerformanceObserver | undefined;
const activeTypes = computed(() => [...new Set(rows.value.map((row) => row.type))]);
const snapshots = computed(() => {
  void revision.value;
  return queryClient
    .getQueryCache()
    .getAll()
    .filter(
      (query) =>
        query.queryKey[0] === 'ruoyi' &&
        query.queryKey[1] === queryScope.value?.key &&
        query.queryKey[2] === 'dict-data'
    )
    .map((query) => ({
      key: JSON.stringify(query.queryKey),
      type: String(query.queryKey[3]),
      status: query.state.status,
      fetchStatus: query.state.fetchStatus,
      hasData: query.state.data !== undefined,
      count: Array.isArray(query.state.data) ? query.state.data.length : '—',
      observers: query.getObserversCount(),
      error: query.state.error instanceof Error ? query.state.error.message : '',
    }));
});
function record(name: string): void {
  if (!startedAt || marks.value.some((mark) => mark.name === name)) return;
  const at = performance.now();
  performance.mark(`dict-qa:${run}:${name}`);
  marks.value.push({ name, ms: at - startedAt });
}
function begin(label: string): number {
  run++;
  runLabel.value = `${run}: ${label}`;
  marks.value = [];
  readyRecorded = false;
  settledRecorded = false;
  mountedRecorded = false;
  resourceCount.value = 0;
  startedAt = performance.now();
  performance.mark(`dict-qa:${run}:start`);
  return run;
}
async function renderMarks(id: number): Promise<void> {
  await nextTick();
  if (id !== run) return;
  record('nextTick');
  requestAnimationFrame(() => {
    if (id === run) record('rAF');
  });
  checkReady();
}
function onRowMounted(): void {
  if (!mountedRecorded) {
    mountedRecorded = true;
    record('first-row-mounted');
  }
}
function checkReady(): void {
  const active = snapshots.value.filter((query) => activeTypes.value.includes(query.type));
  if (!activeTypes.value.length || active.length !== activeTypes.value.length) return;
  if (!readyRecorded && active.every((query) => query.hasData)) {
    readyRecorded = true;
    record('data-ready');
    const id = run;
    void nextTick().then(() =>
      requestAnimationFrame(() => {
        if (id === run) record('ready-paint');
      })
    );
  }
  if (!settledRecorded && active.every((query) => query.fetchStatus === 'idle')) {
    settledRecorded = true;
    record(active.some((query) => query.status === 'error') ? 'error-settled' : 'network-settled');
  }
}
watch([snapshots, activeTypes], checkReady, { flush: 'post' });
const unsubscribe = queryClient.getQueryCache().subscribe(() => revision.value++);
function types(): string[] {
  return [
    ...new Set(
      typeInput.value
        .split(',')
        .map((type) => type.trim())
        .filter(Boolean)
    ),
  ];
}
async function runRows(cold = false, grouped = false): Promise<void> {
  const choices = types();
  if (!choices.length || !queryScope.value) return;
  busy.value = true;
  rows.value = [];
  await nextTick();
  if (cold) {
    const filters = { queryKey: dictKeys.all(queryScope.value) };
    await queryClient.cancelQueries(filters);
    queryClient.removeQueries(filters);
  }
  const id = begin(`${cold ? 'cold' : 'cache'} ${grouped ? 'grouped' : 'same-type'}`);
  const selected = grouped ? choices.slice(0, 3) : choices.slice(0, 1);
  rows.value = Array.from({ length: grouped ? selected.length * 3 : 8 }, (_, index) => ({
    id: ++nextRow,
    type: selected[index % selected.length],
  }));
  busy.value = false;
  await renderMarks(id);
}
async function addRow(): Promise<void> {
  const type = rows.value[0]?.type ?? types()[0];
  if (!type) return;
  const id = begin('add-row');
  rows.value.push({ id: ++nextRow, type });
  await renderMarks(id);
}
async function refresh(): Promise<void> {
  if (!queryScope.value) return;
  const id = begin('invalidate-active');
  const pending = queryClient.invalidateQueries({ queryKey: dictKeys.all(queryScope.value) });
  await renderMarks(id);
  await pending;
}
async function restoreQueryScope(): Promise<void> {
  actionError.value = '';
  try {
    await user.getInfo();
    sessionStatus.value = `当前用户 ${user.name}（真实 getInfo 已建立 scope）`;
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : String(error);
  }
}
async function writeQaLabel(): Promise<void> {
  const scope = queryScope.value;
  const label = writeLabel.value.trim();
  if (!scope || !label || writing.value || !writeFixtureReady || !qaDictId || !qaItemId) return;
  writing.value = true;
  writeStatus.value = '正在读取临时项并提交标签';
  actionError.value = '';
  const id = begin('write-qa-label');
  try {
    const [type, item] = await Promise.all([getType(qaDictId), getData(qaItemId)]);
    if (
      queryScope.value?.key !== scope.key ||
      type.dictId !== qaDictId ||
      type.dictType !== qaType ||
      item.dictCode !== qaItemId ||
      item.dictType !== qaType
    )
      throw new Error('会话或临时验收项不匹配，已阻止写入');
    await dictCommands.updateItem({ scope, input: { ...item, dictLabel: label } });
    record('write-success');
    writeStatus.value = `标签已提交：${label}；后台读取状态见原生 Query`;
    await renderMarks(id);
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : String(error);
    writeStatus.value = '标签写入未成功';
  } finally {
    writing.value = false;
  }
}
onMounted(async () => {
  resourceObserver = new PerformanceObserver((entries) => {
    resourceCount.value += entries
      .getEntries()
      .filter(
        (entry) => entry.startTime >= startedAt && entry.name.includes('/system/dict/data/type/')
      ).length;
  });
  resourceObserver.observe({ type: 'resource' });
  try {
    if (!user.token && !(await user.restoreSession()))
      throw new Error('请先在同源 RuoYi 页面登录后重试');
    await user.getInfo();
    sessionStatus.value = `当前用户 ${user.name}（真实 getInfo 已建立 scope）`;
    await runRows();
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : String(error);
    sessionStatus.value = '登录会话初始化失败';
  }
});
onBeforeUnmount(() => {
  unsubscribe();
  resourceObserver?.disconnect();
});
</script>
<style scoped>
main {
  padding: 24px;
  color: var(--zx-text-primary);
  background: var(--zx-bg-color);
  font-family: sans-serif;
}
fieldset {
  margin-block: 16px;
}
input {
  min-width: 430px;
  padding: 6px;
}
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
button {
  padding: 6px 10px;
  cursor: pointer;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-block: 16px;
}
th,
td {
  text-align: left;
  border: 1px solid var(--zx-border-color);
  padding: 8px;
  vertical-align: top;
}
td:nth-child(2),
td:nth-child(3) {
  min-width: 180px;
}
output {
  display: block;
  font-size: 12px;
  margin-top: 6px;
  overflow-wrap: anywhere;
}
</style>
