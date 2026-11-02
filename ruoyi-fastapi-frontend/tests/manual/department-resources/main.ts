import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import locale from 'element-plus/es/locale/lang/zh-cn';
import { ZxConfigPlugin } from '@zxio/zxui/config-provider';
import 'element-plus/dist/index.css';
import '@zxio/zxui/style';
import themeDeployment from 'virtual:zxui-theme-deployment';
import store from '@/store';
import { setupQueries } from '@/queries/client';
import { bindZxThemeHost } from '@/theme/zx-theme-host';
import plugins from '@/plugins';
import directive from '@/directive';
import { useDict } from '@/utils/dict';
import { handleTree } from '@/utils/ruoyi';
import DictTag from '@/components/ui/DictTag';
import DictStatus from '@/components/business/DictStatus/index.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import useUserStore from '@/store/modules/user';
import App from './Acceptance.vue';

// This separate development entry deliberately installs no runtime mock transport.
const app = createApp(App);
app.use(store);
app.use(plugins);
directive(app);
app.config.globalProperties.useDict = useDict;
app.config.globalProperties.handleTree = handleTree;
app.component('DictTag', DictTag);
app.component('DictStatus', DictStatus);
app.component('DictSelect', DictSelect);
setupQueries(app);
app.use(ElementPlus, { locale });
app.use(ZxConfigPlugin, { namespace: 'zx', locale });
bindZxThemeHost(app, themeDeployment);
// Restore the fresh browser-owned login before mounting the real components.
await useUserStore().getInfo();
app.mount('#app');
