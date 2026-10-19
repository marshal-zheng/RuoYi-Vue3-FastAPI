<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { cloneDashboardJson } from '@zxio/dashboard/schema';
import { ZxField, ZxNumberTextInput } from '@zxio/schema-form/fields';
import { ZxInput } from '@zxio/zxui/input';
import '@zxio/schema-form/style.css';
import { useTimeSeriesSettings } from './use-time-series-settings';
import type { DashboardJsonObject } from '@zxio/dashboard/schema';

defineOptions({ inheritAttrs: false });
const props = defineProps<{
  params: DashboardJsonObject;
  save: (params: DashboardJsonObject) => Promise<void>;
}>();
const emit = defineEmits<{
  preview: [params: DashboardJsonObject | undefined];
  cancel: [];
  saved: [];
}>();
const { draft, config, raw, messages, valid, edit, editNumber } = useTimeSeriesSettings(
  props.params
);
const pending = ref(false);
const root = ref<HTMLElement>();
onMounted(() => root.value?.focus());
const error = ref('');
let active = true;
watch(
  draft,
  () => {
    if (valid.value) emit('preview', cloneDashboardJson(draft.value));
  },
  { deep: true }
);
onBeforeUnmount(() => {
  active = false;
  emit('preview', undefined);
});
async function submit() {
  if (!valid.value || pending.value) return;
  error.value = '';
  pending.value = true;
  try {
    await props.save(cloneDashboardJson(draft.value));
    if (active) emit('saved');
  } catch (cause) {
    if (active) error.value = cause instanceof Error ? cause.message : '保存失败，请重试';
  } finally {
    if (active) pending.value = false;
  }
}
</script>

<template>
  <aside
    ref="root"
    tabindex="-1"
    v-bind="$attrs"
    class="chart-settings"
    aria-label="CPU 时序图设置"
    @keydown.esc.stop="!pending && emit('cancel')"
  >
    <h2>CPU 时序图设置</h2>
    <p>修改实时预览。隐藏字段保留已确认的值；取消恢复原图表。保存设置也会保存当前布局。</p>
    <form @submit.prevent="submit">
      <fieldset :disabled="pending">
        <ZxField label="显示图表标题" v-slot="{ controlProps }">
          <input
            v-bind="controlProps"
            type="checkbox"
            :checked="config.title.show"
            @change="edit('title', 'show', ($event.target as HTMLInputElement).checked)"
          />
        </ZxField>
        <ZxField v-if="config.title.show" label="图表标题" v-slot="{ controlProps }">
          <ZxInput
            v-bind="controlProps"
            :model-value="config.title.text"
            maxlength="120"
            @update:model-value="edit('title', 'text', $event)"
          />
        </ZxField>
        <ZxField label="显示图例" v-slot="{ controlProps }">
          <input
            v-bind="controlProps"
            type="checkbox"
            :checked="config.legend.show"
            @change="edit('legend', 'show', ($event.target as HTMLInputElement).checked)"
          />
        </ZxField>
        <ZxField v-if="config.legend.show" label="图例位置" v-slot="{ controlProps }">
          <select
            v-bind="controlProps"
            :value="config.legend.position"
            @change="edit('legend', 'position', ($event.target as HTMLSelectElement).value)"
          >
            <option value="top">顶部</option>
            <option value="bottom">底部</option>
          </select>
        </ZxField>
        <ZxField label="显示时间轴" v-slot="{ controlProps }">
          <input
            v-bind="controlProps"
            type="checkbox"
            :checked="config.xAxis.show"
            @change="edit('xAxis', 'show', ($event.target as HTMLInputElement).checked)"
          />
        </ZxField>
        <ZxField label="数值轴名称" v-slot="{ controlProps }">
          <ZxInput
            v-bind="controlProps"
            :model-value="config.yAxis.name"
            maxlength="40"
            @update:model-value="edit('yAxis', 'name', $event)"
          />
        </ZxField>
        <ZxField label="数值轴范围" v-slot="{ controlProps }">
          <select
            v-bind="controlProps"
            :value="config.yAxis.mode"
            @change="edit('yAxis', 'mode', ($event.target as HTMLSelectElement).value)"
          >
            <option value="auto">自动</option>
            <option value="fixed">固定</option>
          </select>
        </ZxField>
        <template v-if="config.yAxis.mode === 'fixed'">
          <ZxField label="最小值" required :messages="messages.min" v-slot="{ controlProps }">
            <ZxNumberTextInput
              v-bind="controlProps"
              :text="raw.min"
              :disabled="pending"
              @edit="editNumber('min', $event.text)"
            />
          </ZxField>
          <ZxField label="最大值" required :messages="messages.max" v-slot="{ controlProps }">
            <ZxNumberTextInput
              v-bind="controlProps"
              :text="raw.max"
              :disabled="pending"
              @edit="editNumber('max', $event.text)"
            />
          </ZxField>
        </template>
      </fieldset>
      <p v-if="!valid" role="status">请修正输入；图表保留上一次有效预览。</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <footer>
        <el-button :disabled="pending" @click="emit('cancel')">取消</el-button>
        <el-button type="primary" native-type="submit" :loading="pending" :disabled="!valid"
          >保存设置</el-button
        >
      </footer>
    </form>
  </aside>
</template>

<style scoped>
.chart-settings {
  padding: 16px;
  border: 1px solid var(--zx-semantic-border-default);
  border-radius: 8px;
  background: var(--zx-semantic-surface-elevated);
}
h2 {
  margin: 0 0 8px;
  font-size: 16px;
}
p {
  font-size: 13px;
  line-height: 1.6;
}
fieldset {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}
select {
  width: 100%;
  min-height: 32px;
  color: inherit;
  background: inherit;
  border: 1px solid var(--zx-semantic-border-default);
  border-radius: 4px;
  padding: 4px 8px;
}
input[type='checkbox'] {
  justify-self: start;
}
footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>
