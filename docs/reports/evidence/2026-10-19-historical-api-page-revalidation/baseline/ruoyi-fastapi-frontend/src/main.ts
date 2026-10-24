import { createApp } from 'vue';

// Iconify 图标库
import '@iconify/iconify';
import { Icon } from '@iconify/vue';

import { ElMessageBox } from 'element-plus';
import 'element-plus/dist/index.css';
import locale from 'element-plus/es/locale/lang/zh-cn';

// ZXUI component aliases must follow Element Plus declarations of equal specificity.
import { ZxConfigPlugin } from '@zxio/zxui/config-provider';
import '@zxio/zxui/style';
import { bindZxThemeHost } from '@/theme/zx-theme-host';
import themeDeployment from 'virtual:zxui-theme-deployment';

import '@/assets/styles/index.css'; // global css
import '@/assets/styles/components.less'; // global less (zxui overrides)
import '@/assets/styles/tailwind.css'; // tailwind css

import App from './App';
import store from './store';
import router from './router';
import directive from './directive'; // directive

// 注册指令
import plugins from './plugins'; // plugins
import { download } from '@/utils/request';

// svg图标
import 'virtual:svg-icons-register';
import SvgIcon from '@/components/ui/SvgIcon';
import elementIcons from '@/components/ui/SvgIcon/svgicon';

import './permission'; // permission control
import './utils/auth-feedback-boundary';

import { useDict } from '@/utils/dict';
import { setupQueries } from '@/queries/client';
import DictStatus from '@/components/business/DictStatus/index.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import DictTypeSelect from '@/components/business/DictTypeSelect/index.vue';
import { resolveRuntimeConfig, type RuntimeConfig } from '@/mocks/runtime/mode';
import {
  parseTime,
  resetForm,
  addDateRange,
  handleTree,
  selectDictLabel,
  selectDictLabels,
} from '@/utils/ruoyi';
import { startDevMenuHotSync } from '@/plugins/dev-menu-hot-sync';
import { assertFeedbackRegistry } from '@/utils/feedback/registry';
import { setupAppRuntimeMocks } from '@/mocks/runtime/app-entry';

// 分页组件
import Pagination from '@/components/ui/Pagination';
// 自定义表格工具组件
import RightToolbar from '@/components/ui/RightToolbar';
// 文件上传组件
import FileUpload from '@/components/ui/FileUpload';
// 图片上传组件
import ImageUpload from '@/components/ui/ImageUpload';
// 图片预览组件
import ImagePreview from '@/components/ui/ImagePreview';
// 字典标签组件
import DictTag from '@/components/ui/DictTag';

const app = createApp(App);

// 全局方法挂载
app.config.globalProperties.useDict = useDict;
app.config.globalProperties.download = download;
app.config.globalProperties.parseTime = parseTime;
app.config.globalProperties.resetForm = resetForm;
app.config.globalProperties.handleTree = handleTree;
app.config.globalProperties.addDateRange = addDateRange;
app.config.globalProperties.selectDictLabel = selectDictLabel;
app.config.globalProperties.selectDictLabels = selectDictLabels;

// 全局组件挂载
app.component('DictTag', DictTag);
app.component('DictStatus', DictStatus);
app.component('DictSelect', DictSelect);
app.component('DictTypeSelect', DictTypeSelect);
app.component('Pagination', Pagination);
app.component('FileUpload', FileUpload);
app.component('ImageUpload', ImageUpload);
app.component('ImagePreview', ImagePreview);
app.component('RightToolbar', RightToolbar);
app.component('Icon', Icon);

app.use(store);
setupQueries(app);
app.use(plugins);
app.use(elementIcons);
app.component('svg-icon', SvgIcon);

directive(app);

// The app config and EP feedback services are independent of component registration.
app.use(ElMessageBox);
app.use(ZxConfigPlugin, {
  locale,
  size: 'default',
  namespace: 'zx',
});
bindZxThemeHost(app, themeDeployment);

startDevMenuHotSync();

async function setupRuntimeMocks(runtimeConfig: RuntimeConfig) {
  await setupAppRuntimeMocks(runtimeConfig);

  if (runtimeConfig.mode === 'fallback') {
    // eslint-disable-next-line no-console
    console.info('[Runtime] fallback 模式已启动：真实接口优先，404/网络异常回退到 Mock。');
    return;
  }

  if (runtimeConfig.mode === 'demo-offline') {
    // eslint-disable-next-line no-console
    console.info(
      '[Runtime] demo-offline 模式已启动：单套 typed mock dataset + MSW + IndexedDB store。'
    );
  }
}

// 启动应用（支持 real / fallback / demo-offline 三种运行模式）
async function bootstrap() {
  const runtimeConfig = resolveRuntimeConfig();
  assertFeedbackRegistry();
  await setupRuntimeMocks(runtimeConfig);
  app.use(router);
  app.mount('#app');
}

bootstrap();
