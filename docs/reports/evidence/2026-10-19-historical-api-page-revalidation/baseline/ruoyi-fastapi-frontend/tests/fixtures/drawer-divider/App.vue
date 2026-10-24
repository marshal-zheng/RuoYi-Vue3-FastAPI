<template>
  <ZxConfigProvider :theme="fixtureTheme" :overlay-layout="commonLayout" :direction="direction">
    <ZxConfigProvider :zx-drawer="upper">
      <ZxConfigProvider :zx-drawer="near" :zx-dialog="near">
        <main id="push-target">Host workspace</main>
        <ZxDrawer
          v-bind="drawer.drawerProps.value"
          v-on="drawer.drawerEvents.value"
          :style="style"
          :with-header="withHeader"
        >
          <div v-if="drawerLayout.bodyScroll === 'none'" data-owned-scroll class="owned-scroll">
            <div data-layout-probe class="long">Content-owned scrolling</div>
          </div>
          <div v-else data-layout-probe :class="{ long: longContent }">
            <p>Drawer content</p>
            <el-input aria-label="Fixture input" />
          </div>
          <template v-if="customFooter" #footer><ZxButton>Custom actions</ZxButton></template>
        </ZxDrawer>
        <ZxDialog
          v-model="dialogVisible"
          title="Dialog appearance"
          :divider="dialogDivider"
          v-bind="dialogLayout"
          :dialog-style="style"
          :height="dialogHeight"
          :footer="footer"
        >
          <div v-if="dialogLayout.bodyScroll === 'none'" data-owned-scroll class="owned-scroll">
            <div data-layout-probe class="long">Content-owned scrolling</div>
          </div>
          <div v-else data-layout-probe :class="{ long: longContent }">Dialog content</div>
        </ZxDialog>
      </ZxConfigProvider>
    </ZxConfigProvider>
  </ZxConfigProvider>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, onMounted } from 'vue';
import { ZxConfigProvider, ZxDrawer, ZxDialog, ZxButton, useDrawer } from '@zxio/zxui';
import { zxThemeConfig, setZxThemePreference } from '@/theme/zx-theme-config';
import type { ZxOverlayLayoutConfig, ZxThemeConfig } from '@zxio/zxui';
const commonLayout = ref<ZxOverlayLayoutConfig>({});
const drawerLayout = ref<ZxOverlayLayoutConfig>({});
const dialogLayout = ref<ZxOverlayLayoutConfig>({});
const axes = ref<Partial<ZxThemeConfig>>({});
const fixtureTheme = computed(() => ({
  ...zxThemeConfig.value,
  ...axes.value,
}));
const direction = ref<'ltr' | 'rtl'>('ltr');
const dialogDivider = ref(true);
const dialogHeight = ref<string>();
const upper = ref<{ divider?: boolean }>({});
const near = ref<{ divider?: boolean }>({});
const local = ref<boolean | undefined>();
const mode = ref<'modal' | 'inline' | 'push'>('modal');
const placement = ref<'left' | 'right' | 'top' | 'bottom'>('right');
const footer = ref(true);
const noTitle = ref(false);
const withHeader = ref(true);
const customFooter = ref(false);
const longContent = ref(true);
const style = ref<Record<string, string>>({});
const dialogVisible = ref(false);
const drawer = useDrawer({
  title: 'Drawer divider',
  size: '600px',
  divider: local,
  mode,
  placement,
  footer,
  noTitle,
  mobileFallback: 'full',
  pushTarget: '#push-target',
  resizable: true,
  paddingInline: computed(() => drawerLayout.value.paddingInline),
  headerPadding: computed(() => drawerLayout.value.headerPadding),
  bodyPadding: computed(() => drawerLayout.value.bodyPadding),
  footerPadding: computed(() => drawerLayout.value.footerPadding),
  bodyScroll: computed(() => drawerLayout.value.bodyScroll),
});
onMounted(() => {
  Object.assign(window, {
    dividerTest: {
      async configure(values: Record<string, unknown>) {
        if ('dialogHeight' in values)
          dialogHeight.value = values.dialogHeight as string | undefined;
        if ('commonLayout' in values)
          commonLayout.value = values.commonLayout as ZxOverlayLayoutConfig;
        if ('drawerLayout' in values)
          drawerLayout.value = values.drawerLayout as ZxOverlayLayoutConfig;
        if ('dialogLayout' in values)
          dialogLayout.value = values.dialogLayout as ZxOverlayLayoutConfig;
        if ('axes' in values) axes.value = values.axes as Partial<ZxThemeConfig>;
        if ('direction' in values) direction.value = values.direction as 'ltr' | 'rtl';
        if ('dialogDivider' in values) dialogDivider.value = values.dialogDivider as boolean;
        if ('local' in values) {
          local.value = values.local as boolean | undefined;
          drawer.updateOptions({ divider: local });
        }
        if ('upper' in values) upper.value = values.upper as { divider?: boolean };
        if ('near' in values) near.value = values.near as { divider?: boolean };
        if ('mode' in values) mode.value = values.mode as typeof mode.value;
        if ('placement' in values) placement.value = values.placement as typeof placement.value;
        if ('footer' in values) footer.value = values.footer as boolean;
        if ('noTitle' in values) noTitle.value = values.noTitle as boolean;
        if ('withHeader' in values) withHeader.value = values.withHeader as boolean;
        if ('customFooter' in values) customFooter.value = values.customFooter as boolean;
        if ('long' in values) longContent.value = values.long as boolean;
        if ('style' in values) style.value = values.style as Record<string, string>;
        await nextTick();
      },
      async open() {
        drawer.open();
        await nextTick();
      },
      async close() {
        drawer.close();
        await nextTick();
      },
      async dialog(value: boolean) {
        dialogVisible.value = value;
        await nextTick();
      },
      async updateDivider(value: boolean | undefined) {
        drawer.updateOptions({ divider: value });
        await nextTick();
      },
      async theme(themeId: string, themeMode: 'light' | 'dark' = 'light') {
        await setZxThemePreference({ themeId, mode: themeMode });
        await nextTick();
      },
    },
  });
});
</script>
<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
}
#push-target {
  min-height: 100%;
}
[data-layout-probe] {
  display: flow-root;
}
.long {
  height: 1600px;
  flex-shrink: 0;
}
.owned-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
</style>
