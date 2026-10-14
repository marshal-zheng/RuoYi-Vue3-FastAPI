<template>
  <ZxPageLayout class="app-main" data-zx-surface="canvas" fill>
    <router-view v-slot="{ Component, route }">
      <transition name="fade-transform">
        <!-- <keep-alive :include="tagsViewStore.cachedViews"> -->
        <component v-if="!route.meta.link" :is="Component" :key="route.fullPath" />
        <!-- </keep-alive> -->
      </transition>
    </router-view>
    <iframe-toggle />
    <template v-if="settingsStore.footerVisible" #footer><copyright /></template>
  </ZxPageLayout>
</template>

<script setup>
import { ZxPageLayout } from '@zxio/zxui';
import useSettingsStore from '@/store/modules/settings';
import copyright from './Copyright/index';
import iframeToggle from './IframeToggle/index';
import useTagsViewStore from '@/store/modules/tagsView';

const route = useRoute();
const settingsStore = useSettingsStore();

onMounted(() => {
  addIframe();
});

watchEffect(() => {
  addIframe();
});

function addIframe() {
  if (route.meta.link) {
    useTagsViewStore().addIframeView(route);
  }
}
</script>

<style lang="less" scoped>
.app-main {
  position: relative;
  min-width: 0;
}
</style>

<style lang="less">
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background-color: var(--zx-semantic-fill-scrollbar-track);
}

::-webkit-scrollbar-thumb {
  background-color: var(--zx-semantic-fill-scrollbar-thumb);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: var(--zx-semantic-fill-scrollbar-thumb-hover);
}
</style>
