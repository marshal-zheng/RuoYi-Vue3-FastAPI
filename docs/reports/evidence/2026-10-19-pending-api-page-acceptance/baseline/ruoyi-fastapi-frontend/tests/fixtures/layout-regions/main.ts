import modal from '@/plugins/modal';
import { createApp, h, nextTick } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory, RouterView } from 'vue-router';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import ZXUI from '@zxio/zxui';
import '@zxio/zxui/style';
import '@/assets/styles/index.css';
import '@/assets/styles/tailwind.css';
import Layout from '@/layout/index.vue';
import Page from './Page.vue';
import useSettings from '@/store/modules/settings';
import useAppStore from '@/store/modules/app';

const kinds = [
  'list',
  'native-table',
  'detail',
  'short-detail',
  'mixed',
  'editor',
  'nested',
  'sticky',
  'sticky-detail',
  'iframe',
  'form-builder',
  'route-override',
];
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Layout,
      children: kinds.map((kind) => ({
        path: kind,
        component: Page,
        props: { kind },
        meta: {
          title: kind,
          ...(kind === 'iframe' ? { link: 'about:blank' } : {}),
          ...(kind === 'route-override'
            ? {
                layout: {
                  headerVisible: false,
                  tagsView: false,
                  breadcrumbVisible: false,
                },
              }
            : {}),
        },
      })),
    },
  ],
});
const app = createApp({ render: () => h(RouterView) });
app.use(createPinia()).use(router).use(ElementPlus).use(ZXUI);
app.component('svg-icon', { render: () => h('span') });
app.config.globalProperties.$modal = { ...modal, loading() {}, closeLoading() {} };
await router.isReady();
app.mount('#app');
document.documentElement.style.setProperty('--base-sidebar-width', '220px');
const settings = useSettings();
const appStore = useAppStore();
Object.assign(window, {
  layoutTest: {
    settings,
    appStore,
    async configure(values: Record<string, boolean>) {
      Object.assign(settings, values);
      await nextTick();
    },
    async page(kind: string) {
      await router.push(`/${kind}`);
      await nextTick();
    },
  },
});
