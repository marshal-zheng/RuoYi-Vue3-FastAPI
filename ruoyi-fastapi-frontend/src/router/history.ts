import { createWebHashHistory, createWebHistory, type RouterHistory } from 'vue-router';

import { resolveRuntimeConfig } from '@/demo/runtime/mode';

function resolveRouterBase(): string | undefined {
  const base = import.meta.env.BASE_URL;
  if (!base || base === '.' || base === './') {
    return undefined;
  }
  return base;
}

export function isHashRouteMode(): boolean {
  return resolveRuntimeConfig().mode === 'demo-offline';
}

export function createAppHistory(): RouterHistory {
  const base = resolveRouterBase();
  if (isHashRouteMode()) {
    return base ? createWebHashHistory(base) : createWebHashHistory();
  }
  return base ? createWebHistory(base) : createWebHistory();
}
