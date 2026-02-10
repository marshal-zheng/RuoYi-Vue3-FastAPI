import defaultSettings from '@/settings';
import { useDark, useToggle } from '@vueuse/core';
import { useDynamicTitle } from '@/utils/dynamicTitle';

const isDark = useDark();
const toggleDark = useToggle(isDark);

const {
  sideTheme,
  showSettings,
  topNav,
  topNavBorder,
  tagsView,
  fixedHeader,
  sidebarLogo,
  dynamicTitle,
} = defaultSettings;

const storageSetting = JSON.parse(localStorage.getItem('layout-setting') || '{}');

interface SettingsState {
  title: string;
  theme: string;
  sideTheme: string;
  showSettings: boolean;
  topNav: boolean;
  tagsView: boolean;
  fixedHeader: boolean;
  sidebarLogo: boolean;
  dynamicTitle: boolean;
  topNavBorder: boolean;
  isDark: boolean;
}

const useSettingsStore = defineStore('settings', {
  state: (): SettingsState => ({
    title: '',
    theme: storageSetting.theme || '#0052D9',
    sideTheme: storageSetting.sideTheme || sideTheme,
    showSettings: showSettings,
    topNav: storageSetting.topNav === undefined ? topNav : storageSetting.topNav,
    tagsView: storageSetting.tagsView === undefined ? tagsView : storageSetting.tagsView,
    fixedHeader:
      storageSetting.fixedHeader === undefined ? fixedHeader : storageSetting.fixedHeader,
    sidebarLogo:
      storageSetting.sidebarLogo === undefined ? sidebarLogo : storageSetting.sidebarLogo,
    dynamicTitle:
      storageSetting.dynamicTitle === undefined ? dynamicTitle : storageSetting.dynamicTitle,
    topNavBorder:
      storageSetting.topNavBorder === undefined ? topNavBorder : storageSetting.topNavBorder,
    isDark: isDark.value,
  }),
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
      this.isDark = !this.isDark;
      toggleDark();
    },
  },
});

export default useSettingsStore;
