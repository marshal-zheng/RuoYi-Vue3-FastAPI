<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    class="simulation-drawer"
  >
    <div class="flex flex-col h-full">
      <!-- 事件列表 -->
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="event in displayEvents"
          :key="event.eventId"
          class="event-card p-4 mb-3 rounded-lg transition-colors"
          :class="event.status === 'triggered' ? 'triggered' : ''"
        >
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold text-slate-100">{{ event.name }}</span>
            <el-tag :type="getStatusType(event.status)" size="small">
              {{ getStatusText(event.status) }}
            </el-tag>
          </div>
          <div class="text-xs text-slate-400 mb-3 space-y-1">
            <div>条件: {{ getConditionText(event.condition) }}</div>
            <div>动作: {{ getActionText(event.action) }}</div>
          </div>
          <div class="flex gap-2">
            <el-button
              size="small"
              type="primary"
              @click="$emit('trigger', event.eventId)"
            >
              <el-icon class="mr-1"><VideoPlay /></el-icon>
              触发
            </el-button>
            <el-button size="small" @click="handleEdit(event)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="$emit('delete', event.eventId)"
            >
              删除
            </el-button>
          </div>
        </div>

        <div
          v-if="!hasEvents"
          class="flex flex-col items-center justify-center py-12 text-slate-500"
        >
          <el-icon class="text-5xl mb-3"><Lightning /></el-icon>
          <span class="text-sm">暂无事件配置</span>
          <span class="text-xs mt-2"
            >点击下方按钮添加事件，可配置设备间发送指令等动作</span
          >
        </div>
      </div>

      <!-- 添加按钮 -->
      <el-button type="primary" class="mt-4" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加事件
      </el-button>
    </div>

    <!-- 事件表单对话框 -->
    <EventFormDialog
      ref="eventFormDialogRef"
      :nodes="nodes"
      @submit="handleFormSubmit"
    />
  </ZxDrawer>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { Lightning, Plus, VideoPlay } from "@element-plus/icons-vue";
import { useDrawer } from "@zxio/zxui";
import EventFormDialog from "./EventFormDialog.vue";
import {
  commandTypeLabels,
  eventStatusMap,
} from "./eventOptions";
import {
  CONDITION_TYPE_CONFIG,
  ACTION_TYPE_CONFIG,
} from "../composables/useEventTrigger";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  events: {
    type: Array,
    default: () => [],
  },
  nodes: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  "update:visible",
  "create",
  "edit",
  "delete",
  "trigger",
]);

const eventFormDialogRef = ref(null);

const drawer = useDrawer({
  title: "事件触发配置",
  size: "450px",
  placement: "right",
  showContinue: false,
  onOpen: () => emit("update:visible", true),
  onClose: () => emit("update:visible", false),
});

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      drawer.open();
    } else {
      drawer.close();
    }
  },
  { immediate: true },
);

// 计算节点选项（用于显示）
const nodeOptions = computed(() => {
  if (!props.nodes || props.nodes.length === 0) {
    return [];
  }
  return props.nodes.map((node) => ({
    id: node.id,
    label: node.data?.label || node.data?.name || node.label || node.id,
  }));
});

const displayEvents = computed(() =>
  Array.isArray(props.events) ? props.events : [],
);
const hasEvents = computed(() => displayEvents.value.length > 0);

function getStatusType(status) {
  return eventStatusMap[status]?.type || "info";
}

function getStatusText(status) {
  return eventStatusMap[status]?.label || status;
}

function getConditionText(condition) {
  if (!condition) return "手动触发";
  if (condition.type === "manual") return "手动触发";
  const config = CONDITION_TYPE_CONFIG[condition.type];
  if (!config) return condition.type;

  const value = condition.value || {};
  if (condition.type === "time") {
    return `${config.label}: ${value.time || 0}秒`;
  }
  if (condition.type === "message_count") {
    return `${config.label}: ${value.count || 0}条`;
  }
  if (condition.type === "bandwidth_threshold") {
    return `${config.label}: ${value.threshold || 0}%`;
  }
  return `${config.label}: ${JSON.stringify(value)}`;
}

function getActionText(action) {
  if (!action) return "-";
  const config = ACTION_TYPE_CONFIG[action.type];
  if (!config) return action.type;

  const params = action.params || {};
  if (action.type === "send_command" || action.type === "send_message") {
    const cmdLabel =
      commandTypeLabels[params.commandType] || params.commandType || "";
    const sourceLabel = getNodeLabel(params.sourceNodeId);
    const targetLabel = getNodeLabel(params.targetNodeId);
    if (sourceLabel && targetLabel) {
      if (action.type === "send_command") {
        return `${sourceLabel} → ${targetLabel}: ${cmdLabel}`;
      }
      return `${sourceLabel} → ${targetLabel}`;
    }
    return `${config.label}${cmdLabel ? ": " + cmdLabel : ""}`;
  }
  return config.label;
}

function getNodeLabel(nodeId) {
  if (!nodeId) return "";
  const node = nodeOptions.value.find((n) => n.id === nodeId);
  return node?.label || nodeId;
}

function handleAdd() {
  eventFormDialogRef.value?.open();
}

function handleEdit(event) {
  eventFormDialogRef.value?.open(event);
}

function handleFormSubmit(eventId, config) {
  if (eventId) {
    emit("edit", eventId, config);
  } else {
    emit("create", config);
  }
}
</script>

<style lang="less" scoped>
@import "../styles/simulation-dialog-theme.less";

.event-card {
  .sim-dialog-card();

  &.triggered {
    background: linear-gradient(
      180deg,
      var(--sim-success-bg, rgba(34, 197, 94, 0.2)),
      rgba(34, 197, 94, 0.1)
    );
    border-color: var(--sim-success-border, rgba(34, 197, 94, 0.4));
  }
}
</style>
