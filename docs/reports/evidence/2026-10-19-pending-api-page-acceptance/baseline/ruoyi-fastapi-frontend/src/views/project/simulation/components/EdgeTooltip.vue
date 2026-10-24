<template>
  <div
    v-if="edge"
    class="fixed z-50 p-3 bg-zx-surface-card-fill border border-zx-border-default/50 rounded-lg shadow-zx-surface-overlay-depth pointer-events-none backdrop-blur-sm"
    :style="{ left: position.x + 10 + 'px', top: position.y + 10 + 'px' }"
  >
    <div class="flex justify-between gap-6 text-xs leading-relaxed">
      <span class="text-zx-text-secondary">协议类型</span>
      <span class="text-zx-text-primary font-medium">{{ bandwidthData?.protocolType || '-' }}</span>
    </div>
    <div class="flex justify-between gap-6 text-xs leading-relaxed">
      <span class="text-zx-text-secondary">实时带宽</span>
      <span class="text-zx-text-primary font-medium">{{
        formatBandwidth(bandwidthData?.bandwidthMbps)
      }}</span>
    </div>
    <div class="flex justify-between gap-6 text-xs leading-relaxed">
      <span class="text-zx-text-secondary">负载率</span>
      <span class="font-medium" :class="getLoadClass(bandwidthData?.loadPercent)">
        {{ bandwidthData?.loadPercent?.toFixed(1) || 0 }}%
      </span>
    </div>
    <div class="flex justify-between gap-6 text-xs leading-relaxed">
      <span class="text-zx-text-secondary">报文数量</span>
      <span class="text-zx-text-primary font-medium">{{ bandwidthData?.messageCount || 0 }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  edge: {
    type: Object,
    default: null,
  },
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },
  bandwidthData: {
    type: Object,
    default: null,
  },
});

function formatBandwidth(mbps) {
  if (!mbps) return '0 Mbps';
  if (mbps >= 1000) return `${(mbps / 1000).toFixed(2)} Gbps`;
  return `${mbps.toFixed(2)} Mbps`;
}

function getLoadClass(percent) {
  if (!percent) return 'text-zx-text-primary';
  if (percent > 95) return 'text-danger-400';
  if (percent > 80) return 'text-warning-400';
  return 'text-success-400';
}
</script>
