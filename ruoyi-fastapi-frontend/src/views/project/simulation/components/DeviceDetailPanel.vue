<template>
  <div class="pro-card-body">
    <div class="flex justify-between items-center mb-4 pb-3 border-b border-zx-border-default/30">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 bg-zx-accent rounded-full"></div>
        <span class="text-sm font-semibold text-zx-text-primary tracking-wide">设备详情</span>
      </div>
      <button
        class="flex items-center justify-center w-6 h-6 rounded-md border border-zx-border-default/50 bg-zx-surface-card-fill/50 text-zx-text-secondary hover:text-zx-text-primary hover:bg-zx-surface-field-fill hover:border-zx-border-default transition-all duration-200"
        @click="$emit('close')"
      >
        <el-icon :size="14"><Close /></el-icon>
      </button>
    </div>
    <div class="flex flex-col gap-3">
      <div
        class="flex justify-between items-center py-2 px-3 rounded-md bg-zx-surface-card-fill/30 border border-zx-border-default/30"
      >
        <span class="text-xs text-zx-text-secondary uppercase tracking-wider">设备名称</span>
        <span class="text-sm text-zx-text-primary font-medium">{{
          node?.name || node?.label || '-'
        }}</span>
      </div>
      <div
        class="flex justify-between items-center py-2 px-3 rounded-md bg-zx-surface-card-fill/30 border border-zx-border-default/30"
      >
        <span class="text-xs text-zx-text-secondary uppercase tracking-wider">设备类型</span>
        <span class="text-sm text-zx-text-primary font-medium">{{ node?.deviceType || '-' }}</span>
      </div>
      <div
        class="flex justify-between items-center py-2 px-3 rounded-md bg-zx-surface-card-fill/30 border border-zx-border-default/30"
      >
        <span class="text-xs text-zx-text-secondary uppercase tracking-wider">总线类型</span>
        <span class="text-sm text-zx-text-primary font-medium">{{ node?.busType || '-' }}</span>
      </div>
      <div v-if="node?.ports?.length" class="mt-3">
        <div class="flex items-center gap-2 mb-3">
          <div class="h-px flex-1 bg-zx-surface-field-fill/50"></div>
          <span class="text-xs text-zx-text-secondary uppercase tracking-wider font-medium">端口列表</span>
          <div class="h-px flex-1 bg-zx-surface-field-fill/50"></div>
        </div>
        <div class="flex flex-col gap-2">
          <div
            v-for="port in node.ports"
            :key="port.id"
            class="flex justify-between items-center py-2 px-3 rounded-md bg-zx-surface-card-fill/40 border border-zx-border-default/40 hover:bg-zx-surface-card-fill/60 hover:border-zx-border-default/50 transition-all duration-200 cursor-pointer group"
          >
            <span class="text-xs text-zx-text-primary font-medium group-hover:text-zx-text-primary">{{
              port.interfaceName || port.id
            }}</span>
            <span class="text-xs text-zx-accent-on-surface font-mono group-hover:text-zx-accent-on-surface">{{
              port.interfaceType
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue';

defineProps({
  node: {
    type: Object,
    default: null,
  },
});

defineEmits(['close']);
</script>
