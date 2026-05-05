import { createApp } from 'vue';

import Cookies from 'js-cookie';
import { setupVXETable } from '@/plugins/vxe-table';

import ZXUI from '@zxio/zxui';
import '@zxio/theme-default/theme.css';
import '@zxio/zxui/style';

// Iconify 图标库
import '@iconify/iconify';
import { Icon } from '@iconify/vue';

import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import locale from 'element-plus/es/locale/lang/zh-cn';

import '@/assets/styles/theme.module.css'; // 统一主题源文件
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

import { useDict } from '@/utils/dict';
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
// 富文本组件
import Editor from '@/components/ui/Editor';
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
app.component('Pagination', Pagination);
app.component('FileUpload', FileUpload);
app.component('ImageUpload', ImageUpload);
app.component('ImagePreview', ImagePreview);
app.component('RightToolbar', RightToolbar);
app.component('Editor', Editor);
app.component('Icon', Icon);

app.use(store);
app.use(plugins);
app.use(elementIcons);
app.component('svg-icon', SvgIcon);

directive(app);

// 使用element-plus 并且设置全局的大小
app.use(ElementPlus, {
  locale: locale,
  // 支持 large、default、small
  size: (Cookies.get('size') as 'large' | 'default' | 'small') || 'default',
});

app.use(ZXUI, {
  size: 'default',
  namespace: 'zx',
  // zIndex: 3000
});

setupVXETable(app);

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
