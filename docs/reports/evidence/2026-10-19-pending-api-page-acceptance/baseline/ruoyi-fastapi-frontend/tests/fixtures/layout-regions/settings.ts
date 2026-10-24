import { defineStore } from 'pinia';
export default defineStore('layout-fixture-settings', {
  state: () => ({
    headerVisible: true,
    breadcrumbVisible: true,
    tagsView: false,
    sidebarLogo: true,
    showSettings: true,
    topNav: false,
    topNavBorder: false,
    uniqueOpened: true,
    dynamicTitle: false,
    footerVisible: false,
    footerContent: 'Footer',
  }),
  getters: { isDark: () => false },
  actions: { toggleTheme() {} },
});
