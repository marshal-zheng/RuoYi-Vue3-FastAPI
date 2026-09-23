<template>
  <ZxConfigProvider :theme="zxThemeConfig">
    <main class="fixture-shell">
      <h1>独立组件验收 fixture</h1>
      <p>使用真实业务组件与公开主题 Host；所有业务数据为内存样例，不连接业务服务。</p>
      <div class="fixture-controls">
        <label
          >验收组件
          <select v-model="caseId" aria-label="验收组件">
            <option v-for="item in cases" :key="item.id" :value="item.id">
              {{ item.id }} {{ item.title }}
            </option>
          </select></label
        >
        <button @click="openFixture">打开当前组件</button>
        <button @click="closeFixture">关闭当前组件</button>
        <label
          >模式
          <select :value="zxThemePreference.mode" aria-label="模式" @change="setMode">
            <option>light</option>
            <option>dark</option>
          </select></label
        >
        <label
          >密度
          <select :value="zxThemePreference.density" aria-label="密度" @change="setDensity">
            <option>compact</option>
            <option>default</option>
            <option>comfortable</option>
          </select></label
        >
      </div>
      <p data-testid="fixture-case">
        {{ selected.id }} · {{ selected.title }} ·
        {{ selected.hint || '通过上方按钮调用组件公开 open 或 modelValue。' }}
      </p>
      <section
        class="component-stage"
        :style="
          ['C04b', 'N02', 'N03', 'N05'].includes(caseId)
            ? { height: '600px', display: 'flex', flexDirection: 'column' }
            : {}
        "
      >
        <component
          :is="selected.component"
          :key="caseId"
          ref="fixtureRef"
          v-bind="fixtureProps"
          v-on="fixtureEvents"
        />
      </section>
      <details open>
        <summary>FormGrid 实际容器降列</summary>
        <label
          >容器宽度
          <select v-model.number="containerWidth" aria-label="容器宽度">
            <option :value="1100">1100</option>
            <option :value="650">650</option>
            <option :value="320">320</option>
          </select></label
        >
        <div
          data-testid="limited-container"
          :style="{ width: `${containerWidth}px`, maxWidth: '100%' }"
        >
          <el-form :model="probeModel" v-bind="probe.formProps">
            <FormGrid v-bind="probe.layoutProps" data-testid="responsive-grid">
              <el-form-item label="长标签验证字段一"
                ><ZxInput v-model="probeModel.first"
              /></el-form-item>
              <el-form-item label="第二个字段"
                ><ZxInput v-model="probeModel.second"
              /></el-form-item>
              <el-form-item label="第三个字段"><ZxInput v-model="probeModel.third" /></el-form-item>
              <el-form-item label="整行说明" data-form-full
                ><ZxInput v-model="probeModel.notes" type="textarea"
              /></el-form-item>
            </FormGrid>
          </el-form>
        </div>
      </details>
      <output data-testid="event-log">{{ events.join('\n') || '尚无组件输出事件' }}</output>
    </main>
  </ZxConfigProvider>
</template>
<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  nextTick,
  reactive,
  ref,
  watch,
  type Component,
} from 'vue';
import { ZxConfigProvider, ZxInput } from '@zxio/zxui';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import {
  setZxThemePreference,
  zxThemeConfig,
  zxThemePreference,
  type ZxThemeMode,
  type ZxThemeDensity,
} from '@/theme/zx-theme-config';
const lazy = (loader: () => Promise<{ default: Component }>) => defineAsyncComponent(loader);
const cases = [
  {
    id: 'N02',
    title: 'VersionList create branch',
    component: lazy(() => import('./VersionListFixture.vue')),
    hint: '源码派生fixture仅增测试expose，实际新增按钮已注释，不是生产页面通过。',
  },
  {
    id: 'N03',
    title: 'VersionList edit branch',
    component: lazy(() => import('./VersionListFixture.vue')),
    hint: '源码派生fixture把样例数据交既有versionDialog.open，原编辑分支无生产入口。',
  },
  {
    id: 'N04',
    title: 'VersionDetailDialog',
    component: lazy(() => import('@/views/project/components/VersionDetailDialog.vue')),
    hint: '公开open传样例版本，不证明当前VersionList有详情按钮。',
  },
  {
    id: 'N05',
    title: 'Monitor job detail',
    component: lazy(() => import('@/views/monitor/job/index.vue')),
    hint: '真实Job页面组件+内存任务行，通过行内详情按钮打开；不执行任务。',
  },
  {
    id: 'N06',
    title: 'Monitor job log detail',
    component: lazy(() => import('@/views/monitor/job/log.vue')),
    hint: '真实JobLog页面组件+内存失败日志行，通过详情按钮打开。',
  },
  {
    id: 'N01',
    title: 'UserFormDialog narrow viewport',
    component: lazy(() => import('@/views/system/user/components/UserFormDialog.vue')),
    hint: '真实用户表单；仅内存部门/岗位/角色样例，不创建用户。',
  },
  {
    id: 'F01',
    title: 'DagMatrixView',
    component: lazy(() => import('@/components/business/Dag/components/DagMatrixView.vue')),
    hint: '点击样例节点行的编辑；搜索栏也可直接输入。',
  },
  {
    id: 'F02',
    title: 'DagMatrixViewSimple',
    component: lazy(() => import('@/components/business/Dag/components/DagMatrixViewSimple.vue')),
    hint: '点击样例节点行的编辑；搜索栏也可直接输入。',
  },
  {
    id: 'F03',
    title: 'DagSearchInput',
    component: lazy(() => import('@/components/business/Dag/components/DagSearchInput.vue')),
  },
  {
    id: 'F04',
    title: 'DeviceClazzDialog',
    component: lazy(() => import('@/components/business/Device/DeviceClazzDialog.vue')),
  },
  {
    id: 'F05',
    title: 'Device ExportDialog',
    component: lazy(() => import('@/components/business/Device/ExportDialog.vue')),
  },
  {
    id: 'F06',
    title: 'Device NodeEditDrawer',
    component: lazy(() => import('@/components/business/Device/NodeEditDrawer.vue')),
  },
  {
    id: 'F07',
    title: 'Project ExportDialog',
    component: lazy(() => import('@/views/project/components/ExportDialog.vue')),
  },
  {
    id: 'F08',
    title: 'ProjectEditDialog',
    component: lazy(() => import('@/views/project/components/ProjectEditDialog.vue')),
  },
  {
    id: 'F09',
    title: 'ProtocolConfigDrawer',
    component: lazy(() => import('@/views/project/components/ProtocolConfigDrawer.vue')),
  },
  {
    id: 'F10',
    title: 'ThemeValidation',
    component: lazy(() => import('@/components/ui/ThemeValidation/index.vue')),
  },
  {
    id: 'F11',
    title: 'ImageUpload preview',
    component: lazy(() => import('@/components/ui/ImageUpload/index.vue')),
    hint: '悬停样例图片，点击预览图标；不要执行上传。',
  },
  {
    id: 'F12',
    title: 'RightToolbar transfer',
    component: lazy(() => import('@/components/ui/RightToolbar/index.vue')),
    hint: '点击显隐列按钮。',
  },
  {
    id: 'C01',
    title: 'CategoryFormDialog',
    component: lazy(() => import('@/components/business/Device/CategoryFormDialog.vue')),
  },
  {
    id: 'C02',
    title: 'DeviceCloneDialog',
    component: lazy(() => import('@/components/business/Device/DeviceCloneDialog.vue')),
  },
  {
    id: 'C03',
    title: 'ProtocolFormDrawer',
    component: lazy(() => import('@/components/business/Protocol/ProtocolFormDrawer.vue')),
  },
  {
    id: 'C04a',
    title: 'Legacy ProjectDlg',
    component: lazy(() => import('@/views/system/project/components/ProjectDlg.vue')),
  },
  {
    id: 'C04b',
    title: 'Legacy ProjectList',
    component: lazy(() => import('@/views/system/project/components/ProjectList.vue')),
    hint: '点击内存样例工程的详情。',
  },
  {
    id: 'G01',
    title: 'GeneratedForm SFC',
    component: lazy(() => import('./GeneratedForm.vue')),
  },
];
const caseId = ref('F01');
const selected = computed(() => cases.find((item) => item.id === caseId.value)!);
const fixtureRef = ref<{
  open?: (...args: unknown[]) => unknown;
  openEdit?: (...args: unknown[]) => unknown;
  close?: () => unknown;
}>();
const visible = ref(false);
const events = ref<string[]>([]);
const record = (name: string, value: unknown) =>
  events.value.push(`${caseId.value} ${name}: ${JSON.stringify(value)}`);
const graphData = {
  nodes: [
    {
      id: 'fixture-node',
      type: 'root-node',
      properties: {
        content: { label: 'Fixture node', description: 'Fixture note' },
      },
    },
  ],
  edges: [],
};
const fixtureProps = computed(() => {
  switch (caseId.value) {
    case 'N02':
    case 'N03':
      return { projectId: 1 };
    case 'N01':
      return {
        deptOptions: [{ id: 1, label: 'Fixture department' }],
        statusOptions: [
          { label: '正常', value: '0' },
          { label: '停用', value: '1' },
        ],
        sexOptions: [{ label: '未知', value: '2' }],
      };
    case 'F01':
    case 'F02':
      return { graphData, readonly: false };
    case 'F03':
      return { placeholder: 'Fixture 节点搜索' };
    case 'F05':
    case 'F07':
      return {
        modelValue: visible.value,
        projectData: { projectId: 1, projectName: 'Fixture project' },
      };
    case 'F06':
      return {
        modelValue: visible.value,
        nodeData: {
          data: {
            name: 'Fixture node',
            deviceType: 'Fixture type',
            model: 'Fixture model',
            manufacturer: 'Fixture maker',
            version: '1',
            remark: 'Fixture note',
          },
        },
      };
    case 'F11':
      return { modelValue: [{ name: 'fixture.svg', url: '/fixture.svg' }] };
    case 'F12':
      return {
        columns: [
          { key: 0, label: 'Fixture column', visible: true },
          { key: 1, label: 'Fixture extra', visible: false },
        ],
        showColumnsType: 'transfer',
      };
    case 'G01':
      return { modelValue: visible.value };
    default:
      return {};
  }
});
const fixtureEvents = computed(() =>
  caseId.value === 'F03'
    ? { search: (value: unknown) => record('search', value) }
    : ['F05', 'F06', 'F07', 'G01'].includes(caseId.value)
      ? {
          'update:modelValue': (value: boolean) => {
            visible.value = value;
          },
          ...(caseId.value === 'G01'
            ? { confirm: (value: unknown) => record('confirm', value) }
            : {}),
        }
      : {}
);
watch(caseId, () => {
  visible.value = false;
  events.value = [];
});
async function openFixture() {
  await nextTick();
  if (['F05', 'F06', 'F07', 'G01'].includes(caseId.value)) visible.value = true;
  else if (caseId.value === 'N03')
    fixtureRef.value?.openEdit?.({
      versionId: 1,
      versionNumber: 'v1.0.0',
      versionName: 'Fixture version',
      description: 'Fixture version description',
    });
  else if (caseId.value === 'N04')
    fixtureRef.value?.open?.({
      versionId: 1,
      versionNumber: 'v1.0.0',
      versionName: 'Fixture version',
      description: 'Fixture version description',
      isLocked: '1',
      lockedBy: 'Fixture operator',
      lockedTime: '2026-09-22 10:00:00',
      createBy: 'Fixture creator',
      createTime: '2026-09-21 10:00:00',
    });
  else if (caseId.value === 'C02')
    fixtureRef.value?.open?.({ deviceId: 1, deviceName: 'Fixture device' });
  else if (caseId.value === 'F09')
    fixtureRef.value?.open?.({
      interfaceId: 1,
      interfaceName: 'Fixture port',
      interfaceType: 'CAN',
      protocolType: 'CAN',
      description: 'Fixture notes',
    });
  else fixtureRef.value?.open?.();
}
function closeFixture() {
  visible.value = false;
  fixtureRef.value?.close?.();
}
function setMode(event: Event) {
  setZxThemePreference({
    mode: (event.target as HTMLSelectElement).value as ZxThemeMode,
  });
}
function setDensity(event: Event) {
  setZxThemePreference({
    density: (event.target as HTMLSelectElement).value as ZxThemeDensity,
  });
}
const containerWidth = ref(1100);
const probeModel = reactive({ first: '', second: '', third: '', notes: '' });
const probe = useFormDialog({ columns: 3 });
</script>
<style>
body {
  margin: 0;
}
.fixture-shell {
  padding: 16px;
  color: var(--el-text-color-primary);
  background: var(--el-bg-color);
  min-height: 100vh;
}
.fixture-shell h1 {
  font: 600 20px sans-serif;
}
.fixture-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
.fixture-controls select,
.fixture-controls button {
  min-height: 32px;
}
.component-stage {
  margin: 16px 0;
  min-height: 120px;
}
.fixture-shell details {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color);
}
.fixture-shell output {
  display: block;
  white-space: pre-wrap;
  margin-top: 16px;
}
</style>
