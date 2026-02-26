<template>
  <div
    v-if="visible"
    class="fixed z-50 min-w-40 bg-slate-800 border border-slate-600/50 rounded-lg shadow-xl overflow-hidden backdrop-blur-sm"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
    @click.stop
  >
    <div
      class="px-4 py-2.5 text-xs font-semibold text-slate-400 bg-slate-900/50 border-b border-slate-700/50"
    >
      故障注入
    </div>
    <div class="py-2">
      <div
        v-for="item in menuItems"
        :key="item.type"
        class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-300 cursor-pointer transition-colors hover:bg-primary-500/20 hover:text-primary-400"
        @click="handleClick(item)"
      >
        <el-icon class="text-slate-500"><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </div>
    </div>
  </div>

  <!-- 参数配置对话框 -->
  <el-dialog v-model="showParamsDialog" :title="currentFault?.label" width="400px" append-to-body>
    <el-form :model="faultParams" label-width="100px">
      <el-form-item
        v-for="param in currentFault?.params || []"
        :key="param.name"
        :label="param.label"
      >
        <el-input-number
          v-if="param.type === 'number'"
          v-model="faultParams[param.name]"
          :min="param.min"
          :max="param.max"
        />
        <el-input v-else v-model="faultParams[param.name]" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showParamsDialog = false">取消</el-button>
      <el-button type="primary" @click="confirmInject">确认注入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { Link, Warning, CircleClose, Delete, Timer } from '@element-plus/icons-vue';
import { FaultType, FAULT_TYPE_CONFIG } from '../composables/useFaultInjection';

const emit = defineEmits(['inject', 'clear']);

const visible = ref(false);
const position = ref({ x: 0, y: 0 });
const target = ref(null);
const showParamsDialog = ref(false);
const currentFault = ref(null);
const faultParams = ref({});

const iconMap = {
  Disconnect: Link,
  Link,
  Warning,
  CircleClose,
  Delete,
  Timer,
};

const menuItems = computed(() => {
  if (!target.value) return [];

  const targetType = target.value.type;
  return Object.entries(FAULT_TYPE_CONFIG)
    .filter(([, config]) => config.targetType === targetType)
    .map(([type, config]) => ({
      type,
      label: config.label,
      icon: iconMap[config.icon] || Warning,
      params: config.params,
    }));
});

function show(event, targetInfo) {
  position.value = { x: event.clientX, y: event.clientY };
  target.value = targetInfo;
  visible.value = true;
}

function hide() {
  visible.value = false;
  target.value = null;
}

function handleClick(item) {
  currentFault.value = item;

  if (item.params && item.params.length > 0) {
    faultParams.value = {};
    item.params.forEach((param) => {
      faultParams.value[param.name] = param.default;
    });
    showParamsDialog.value = true;
  } else {
    confirmInject();
  }

  hide();
}

function confirmInject() {
  emit('inject', {
    type: currentFault.value.type,
    targetId: target.value?.target?.id,
    targetType: target.value?.type,
    params: { ...faultParams.value },
  });

  showParamsDialog.value = false;
  currentFault.value = null;
  faultParams.value = {};
}

function handleClickOutside() {
  if (visible.value) {
    hide();
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

defineExpose({ show, hide });
</script>
