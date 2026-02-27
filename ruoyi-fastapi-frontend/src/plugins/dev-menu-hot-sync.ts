import { getDevMenuSignature } from '@/api/system/devMenuSync';
import { devMenuSyncPollIntervalMs, isDevMenuSyncEnabled } from '@/config/devMenuSync';
import usePermissionStore from '@/store/modules/permission';
import { getToken } from '@/utils/auth';

let timer: number | null = null;
let inFlight = false;
let latestSignature: string | null = null;

async function pollSignature() {
  if (inFlight) {
    return;
  }
  if (!getToken()) {
    latestSignature = null;
    return;
  }
  inFlight = true;
  try {
    const payload = await getDevMenuSignature();
    const nextSignature = payload?.signature;
    if (!nextSignature) {
      return;
    }
    if (!latestSignature) {
      latestSignature = nextSignature;
      return;
    }
    if (latestSignature === nextSignature) {
      return;
    }
    latestSignature = nextSignature;
    const permissionStore = usePermissionStore();
    await permissionStore.reloadDynamicRoutes('signature_changed');
  } catch (error) {
    console.warn('[dev-menu-hot-sync] signature poll failed, retry next cycle', error);
  } finally {
    inFlight = false;
  }
}

export function startDevMenuHotSync(): void {
  if (!isDevMenuSyncEnabled || timer !== null) {
    return;
  }
  latestSignature = null;
  void pollSignature();
  timer = window.setInterval(() => {
    void pollSignature();
  }, devMenuSyncPollIntervalMs);
  console.info('[dev-menu-hot-sync] enabled, poll interval:', devMenuSyncPollIntervalMs);
}

export function stopDevMenuHotSync(): void {
  if (timer !== null) {
    window.clearInterval(timer);
    timer = null;
  }
  inFlight = false;
  latestSignature = null;
}
