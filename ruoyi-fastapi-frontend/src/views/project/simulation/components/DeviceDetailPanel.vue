<template>
  <div class="pro-card-body">
    <div class="flex justify-between items-center mb-4 pb-3 border-b border-slate-700/30">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 bg-primary-500 rounded-full"></div>
        <span class="text-sm font-semibold text-slate-200 tracking-wide">设备详情</span>
      </div>
      <button
        class="flex items-center justify-center w-6 h-6 rounded-md border border-slate-600/50 bg-slate-800/50 text-slate-400 hover:text-slate-200 hover:bg-slate-700 hover:border-slate-500 transition-all duration-200"
        @click="$emit('close')"
      >
        <el-icon :size="14"><Close /></el-icon>
      </button>
    </div>
    <div class="flex flex-col gap-3">
      <div class="flex justify-between items-center py-2 px-3 rounded-md bg-slate-800/30 border border-slate-700/30">
        <span class="text-xs text-slate-400 uppercase tracking-wider">设备名称</span>
        <span class="text-sm text-slate-100 font-medium">{{ node?.name || node?.label || '-' }}</span>
      </div>
      <div class="flex justify-between items-center py-2 px-3 rounded-md bg-slate-800/30 border border-slate-700/30">
        <span class="text-xs text-slate-400 uppercase tracking-wider">设备类型</span>
        <span class="text-sm text-slate-100 font-medium">{{ node?.deviceType || '-' }}</span>
      </div>
      <div class="flex justify-between items-center py-2 px-3 rounded-md bg-slate-800/30 border border-slate-700/30">
        <span class="text-xs text-slate-400 uppercase tracking-wider">总线类型</span>
        <span class="text-sm text-slate-100 font-medium">{{ node?.busType || '-' }}</span>
      </div>
      <div v-if="node?.ports?.length" class="mt-3">
        <div class="flex items-center gap-2 mb-3">
          <div class="h-px flex-1 bg-slate-700/50"></div>
          <span class="text-xs text-slate-500 uppercase tracking-wider font-medium">端口列表</span>
          <div class="h-px flex-1 bg-slate-700/50"></div>
        </div>
        <div class="flex flex-col gap-2">
          <div
            v-for="port in node.ports"
            :key="port.id"
            class="flex justify-between items-center py-2 px-3 rounded-md bg-slate-800/40 border border-slate-700/40 hover:bg-slate-800/60 hover:border-slate-600/50 transition-all duration-200 cursor-pointer group"
          >
            <span class="text-xs text-slate-200 font-medium group-hover:text-slate-100">{{ port.interfaceName || port.id }}</span>
            <span class="text-xs text-primary-400 font-mono group-hover:text-primary-300">{{ port.interfaceType }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue'

defineProps({
  node: {
    type: Object,
    default: null,
  },
})

defineEmits(['close'])
</script>
