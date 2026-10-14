import defaultSettings, { LAYOUT_SETTINGS_VERSION } from '@/settings';
import { defineStore } from 'pinia';
import { useDynamicTitle } from '@/utils/dynamicTitle';
import { setZxThemePreference, zxIsDark } from '@/theme/zx-theme-config';

const {
  showSettings,
  topNav,
  topNavBorder,
  tagsView,
  headerVisible,
  breadcrumbVisible,
  sidebarLogo,
  dynamicTitle,
} = defaultSettings;

function getStorageSetting(): Record<string, any> {
  try {
    const raw = localStorage.getItem('layout-setting');
    if (!raw) return {};
    const saved = JSON.parse(raw);
    if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return {};
    if (typeof saved.layoutVersion === 'number' && saved.layoutVersion >= LAYOUT_SETTINGS_VERSION) {
      return saved;
    }

    const migrated = {
      ...saved,
      tagsView,
      layoutVersion: LAYOUT_SETTINGS_VERSION,
    };
    try {
      localStorage.setItem('layout-setting', JSON.stringify(migrated));
    } catch {
      // Keep all in-memory preferences when browser storage cannot be written.
      return migrated;
    }
    return migrated;
  } catch {
    return {};
  }
}

interface SettingsState {
  title: string;
  showSettings: boolean;
  topNav: boolean;
  tagsView: boolean;
  headerVisible: boolean;
  breadcrumbVisible: boolean;
  sidebarLogo: boolean;
  dynamicTitle: boolean;
  topNavBorder: boolean;
}

const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => {
    const storageSetting = getStorageSetting();
    return {
      title: '',
      showSettings: showSettings,
      topNav: storageSetting.topNav === undefined ? topNav : storageSetting.topNav,
      tagsView: typeof storageSetting.tagsView === 'boolean' ? storageSetting.tagsView : tagsView,
      headerVisible:
        typeof storageSetting.headerVisible === 'boolean'
          ? storageSetting.headerVisible
          : headerVisible,
      breadcrumbVisible:
        typeof storageSetting.breadcrumbVisible === 'boolean'
          ? storageSetting.breadcrumbVisible
          : breadcrumbVisible,
      sidebarLogo:
        storageSetting.sidebarLogo === undefined ? sidebarLogo : storageSetting.sidebarLogo,
      dynamicTitle:
        storageSetting.dynamicTitle === undefined ? dynamicTitle : storageSetting.dynamicTitle,
      topNavBorder:
        storageSetting.topNavBorder === undefined ? topNavBorder : storageSetting.topNavBorder,
    };
  },
  getters: {
    isDark: () => zxIsDark.value,
  },
  actions: {
    // 修改布局设置
    changeSetting(data: { key: string; value: any }) {
      const { key, value } = data;
      if (this.hasOwnProperty(key)) {
        (this as any)[key] = value;
      }
    },
    // 设置网页标题
    setTitle(title: string) {
      this.title = title;
      useDynamicTitle();
    },
    // 切换暗黑模式
    toggleTheme() {
      return setZxThemePreference({ mode: this.isDark ? 'light' : 'dark' });
    },
  },
});

export default useSettingsStore;
