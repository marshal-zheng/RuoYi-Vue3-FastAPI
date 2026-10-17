import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import locale from 'element-plus/es/locale/lang/zh-cn';
import ZXUI from '@zxio/zxui';
import 'element-plus/dist/index.css';
import '@zxio/zxui/style';
import themeDeployment from 'virtual:zxui-theme-deployment';
import store from '@/store';
import { setupQueries } from '@/queries/client';
import { bindZxThemeHost } from '@/theme/zx-theme-host';
import App from './Acceptance.vue';

// This separate development entry deliberately installs no runtime mock transport.
const app = createApp(App);
app.use(store);
setupQueries(app);
app.use(ElementPlus, { locale });
app.use(ZXUI, { namespace: 'zx' });
bindZxThemeHost(app, themeDeployment);
app.mount('#app');
