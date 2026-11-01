import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus, { ElMessageBox } from 'element-plus';
import ZXUI from '@zxio/zxui';
import 'element-plus/dist/index.css';
import '@zxio/zxui/style';
import { createShortcutRuntime } from '@zxio/keybindings/core';
import { createShortcutPlugin } from '@zxio/keybindings/vue';
import { setupQueries } from '@/queries/client';
import { setQuerySession } from '@/queries/context';
import useUserStore from '@/store/modules/user';
import { bindZxThemeHost } from '@/theme/zx-theme-host';
import deployment from 'virtual:zxui-theme-deployment';
import DictTag from '@/components/ui/DictTag/index.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import DictStatus from '@/components/business/DictStatus/index.vue';
import { parseTime, resetForm } from '@/utils/ruoyi';
import App from './App.vue';
import './transport';
import 'virtual:svg-icons-register';
import { createRouter, createMemoryHistory } from 'vue-router';
import { download } from '@/utils/request';
import { useDict } from '@/utils/dict';
const app = createApp(App);
app.use(createPinia());
app.use(
  createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: { render: () => null } }],
  })
);
app.use(ElementPlus);
app.use(ZXUI);
app.use(
  createShortcutPlugin(
    createShortcutRuntime({ appId: 'table-render-business-preview', platform: 'mac' })
  )
);
setupQueries(app);
useUserStore().permissions = ['*:*:*'];
useUserStore().roles = ['admin'];
setQuerySession(1, ['admin'], ['*:*:*']);
app.component('DictTag', DictTag);
app.component('DictSelect', DictSelect);
app.component('DictStatus', DictStatus);
app.directive('hasPermi', {});
app.config.globalProperties.useDict = useDict;
Object.assign(app.config.globalProperties, {
  download,
  parseTime,
  resetForm,
  $modal: { confirm: (message: string) => ElMessageBox.confirm(message) },
});
bindZxThemeHost(app, deployment);
app.mount('#app');
