import { defineStore } from 'pinia';
export default defineStore('layout-fixture-permission', {
  state: () => ({
    routes: [],
    sidebarRouters: [{ path: '/list', meta: { title: '列表', icon: 'list' } }],
    defaultRoutes: [],
    topbarRouters: [],
  }),
  actions: { setSidebarRouters() {} },
});
