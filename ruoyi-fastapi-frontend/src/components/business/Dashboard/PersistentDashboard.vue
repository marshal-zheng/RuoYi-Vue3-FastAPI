<template>
  <section class="persistent-dashboard" :aria-label="title">
    <div class="persistent-dashboard__bar">
      <slot
        name="controls"
        :begin-settings="beginSettings"
        :settings-ready="ready && !state.pending && !state.conflict"
        :document="document"
        :update-document="update"
      />
      <el-button :disabled="!!state.pending || settingsActive" @click="reload"
        >重新加载布局</el-button
      >
      <el-button
        v-if="editable"
        :disabled="!!state.pending || !!state.conflict || settingsActive"
        @click="reset"
        >恢复默认布局</el-button
      >
      <el-button
        v-if="editable"
        type="primary"
        :disabled="!!state.pending || !!state.conflict || !state.dirty || settingsActive"
        @click="save"
        >保存布局</el-button
      >
      <span role="status" aria-live="polite">{{ status }}</span>
    </div>
    <div v-if="state.error" class="persistent-dashboard__notice" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="state.conflict" class="persistent-dashboard__notice" role="alert">
      <span
        >布局已被其他窗口更新{{
          state.conflict.remote ? `（版本 ${state.conflict.remote.revision}）` : '或删除'
        }}。请选择保留的内容。</span
      >
      <el-button @click="resolve('remote')">采用服务器布局</el-button>
      <el-button @click="resolve('local')">保留本地编辑</el-button>
      <span>保留本地后，需再次保存。</span>
    </div>
    <ZxDashboardDesigner
      ref="designer"
      :inert="settingsActive || undefined"
      :document="document"
      :mode="editable ? mode : 'view'"
      :registry="registry"
      :show-palette="false"
      :panel-chrome="{
        getPanelActions: (_panel, actions) =>
          actions.filter((action) => !['duplicate', 'remove'].includes(action.type)),
      }"
      :grid="{ rowHeight: 32, margin: [12, 12] }"
      locale="zh-CN"
      chrome-variant="card"
      @update:document="update"
      @update:mode="mode = $event"
      @save-request="save"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onScopeDispose, ref, shallowRef } from 'vue';
import { ZxDashboardDesigner } from '@zxio/dashboard/designer';
import { createDashboardPersistence } from '@zxio/dashboard/persistence';
import { createDashboardHttpAdapter, type DashboardScope } from '@/api/dashboard';
import type { DashboardDesignerContext } from '@zxio/dashboard/designer';
import type { DashboardDocument } from '@zxio/dashboard/schema';
import type { DashboardWidgetRegistry } from '@zxio/dashboard/widget';
import '@zxio/dashboard/style';
import { beginPanelSettings, type PanelSettingsSession } from './panel-settings';

const props = withDefaults(
  defineProps<{
    scope: DashboardScope;
    storageKey: string;
    initialDocument: DashboardDocument;
    registry: DashboardWidgetRegistry;
    title: string;
    editable?: boolean;
    settingsActive?: boolean;
  }>(),
  { editable: true }
);
const emit = defineEmits<{ documentChange: [document: DashboardDocument] }>();
defineSlots<{
  controls(props: {
    beginSettings: (panelId: string) => PanelSettingsSession;
    settingsReady: boolean;
    document: DashboardDocument;
    updateDocument: (document: DashboardDocument) => void;
  }): unknown;
}>();
const ready = ref(false);
const designer = ref<Pick<DashboardDesignerContext, 'markSaved'>>();
const mode = ref<'edit' | 'preview' | 'view'>('view');
const controller = createDashboardPersistence({
  key: props.storageKey,
  adapter: createDashboardHttpAdapter(props.scope),
  initialDocument: props.initialDocument,
});
const state = shallowRef(controller.getState());
const document = computed(() => state.value.document ?? props.initialDocument);
const status = computed(() =>
  state.value.pending
    ? '正在同步布局…'
    : state.value.dirty
      ? '布局未保存'
      : `布局已同步${state.value.saved ? ` · 版本 ${state.value.saved.revision}` : ''}`
);
const errorMessage = computed(() =>
  state.value.error instanceof Error ? state.value.error.message : '布局同步失败，请重试'
);
const unsubscribe = controller.subscribe((next) => {
  state.value = next;
});

function update(value: DashboardDocument) {
  controller.setDocument(value);
  emit('documentChange', value);
}
async function markSaved() {
  await nextTick();
  const saved = state.value.saved?.document;
  if (saved) designer.value?.markSaved(saved.panels, saved.layout);
}
async function reload() {
  try {
    await controller.load();
    ready.value = true;
    await markSaved();
    emit('documentChange', document.value);
  } catch {
    /* The controller retains the error for the inline retry flow. */
  }
}
function beginSettings(panelId: string): PanelSettingsSession {
  if (!props.editable || !ready.value) throw new Error('请先成功读取服务器布局');
  const session = beginPanelSettings(controller, () => document.value, props.registry, panelId);
  return {
    panel: session.panel,
    async save(params) {
      await session.save(params);
      await markSaved();
      emit('documentChange', document.value);
    },
  };
}
async function save() {
  if (!props.editable || state.value.pending || state.value.conflict) return;
  try {
    await controller.save();
    await markSaved();
  } catch {
    /* Keep local edits and show the observable error. */
  }
}
function reset() {
  update(props.initialDocument);
}
async function resolve(choice: 'remote' | 'local') {
  controller.resolveConflict(choice);
  if (!state.value.document) controller.setDocument(props.initialDocument);
  await markSaved();
  emit('documentChange', document.value);
}
onMounted(reload);
onScopeDispose(() => {
  unsubscribe();
  controller.dispose();
});
defineExpose({ update, getDocument: () => document.value });
</script>

<style scoped>
.persistent-dashboard {
  min-width: 0;
}
.persistent-dashboard__bar,
.persistent-dashboard__notice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
}
.persistent-dashboard__notice {
  color: var(--zx-semantic-status-warning-on-surface);
}
</style>
