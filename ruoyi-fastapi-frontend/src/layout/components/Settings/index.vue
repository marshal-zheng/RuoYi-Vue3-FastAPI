<template>
  <el-drawer v-model="showSettings" :withHeader="false" direction="rtl" size="300px">
    <div class="setting-drawer-title">
      <h3 class="drawer-title">主题风格设置</h3>
    </div>
    <div class="drawer-item">
      <span>ZXUI 主题包</span>
      <span class="comp-style">
        <ZxThemePresetSwitch />
      </span>
    </div>
    <div class="drawer-item">
      <span>暗黑模式</span>
      <span class="comp-style">
        <el-switch
          :model-value="settingsStore.isDark"
          @change="settingsStore.toggleTheme()"
          class="drawer-switch"
        />
      </span>
    </div>
    <el-divider />

    <h3 class="drawer-title">系统布局配置</h3>

    <div class="drawer-item">
      <span>开启 TopNav</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.topNav" @change="topNavChange" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>TopNav 下划线</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.topNavBorder" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>开启 Tags-Views</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.tagsView" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>显示 Header</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.headerVisible" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>显示面包屑</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.breadcrumbVisible" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>显示 Logo</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.sidebarLogo" class="drawer-switch" />
      </span>
    </div>

    <div class="drawer-item">
      <span>动态标题</span>
      <span class="comp-style">
        <el-switch v-model="settingsStore.dynamicTitle" class="drawer-switch" />
      </span>
    </div>

    <el-divider />

    <el-button type="primary" icon="DocumentAdd" @click="saveSetting">保存配置</el-button>
    <el-button plain icon="Refresh" @click="resetSetting">重置配置</el-button>
  </el-drawer>
</template>

<script setup>
import useAppStore from '@/store/modules/app';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';
import ZxThemePresetSwitch from '@/theme/ZxThemePresetSwitch.vue';
import { LAYOUT_SETTINGS_VERSION } from '@/settings';

const { proxy } = getCurrentInstance();
const appStore = useAppStore();
const settingsStore = useSettingsStore();
const permissionStore = usePermissionStore();
const showSettings = ref(false);
const storeSettings = computed(() => settingsStore);

/** 是否需要topnav */
function topNavChange(val) {
  if (!val) {
    appStore.toggleSideBarHide(false);
    permissionStore.setSidebarRouters(permissionStore.defaultRoutes);
  }
}

function saveSetting() {
  proxy.$modal.loading('正在保存到本地，请稍候...');
  let layoutSetting = {
    layoutVersion: LAYOUT_SETTINGS_VERSION,
    topNav: storeSettings.value.topNav,
    tagsView: storeSettings.value.tagsView,
    headerVisible: storeSettings.value.headerVisible,
    breadcrumbVisible: storeSettings.value.breadcrumbVisible,
    sidebarLogo: storeSettings.value.sidebarLogo,
    dynamicTitle: storeSettings.value.dynamicTitle,
    topNavBorder: storeSettings.value.topNavBorder,
  };
  localStorage.setItem('layout-setting', JSON.stringify(layoutSetting));
  setTimeout(proxy.$modal.closeLoading(), 1000);
}
function resetSetting() {
  proxy.$modal.loading('正在清除设置缓存并刷新，请稍候...');
  localStorage.removeItem('layout-setting');
  setTimeout('window.location.reload()', 1000);
}
function openSetting() {
  showSettings.value = true;
}

defineExpose({
  openSetting,
});
</script>

<style scoped>
.setting-drawer-title {
  margin-bottom: 12px;
  color: var(--zx-semantic-text-primary);
  line-height: 22px;
  font-weight: bold;
}

.setting-drawer-title .drawer-title {
  font-size: 14px;
}

.drawer-item {
  color: var(--zx-semantic-text-primary);
  padding: 12px 0;
  font-size: 14px;
}

.drawer-item .comp-style {
  float: right;
  margin: -3px 8px 0px 0px;
}
</style>
