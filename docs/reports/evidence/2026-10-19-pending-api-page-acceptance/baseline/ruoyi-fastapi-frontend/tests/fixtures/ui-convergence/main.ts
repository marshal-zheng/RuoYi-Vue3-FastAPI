import { createApp, ref } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import ElementPlus from 'element-plus';
import * as ElementIcons from '@element-plus/icons-vue';
import ZXUI from '@zxio/zxui';
import 'element-plus/dist/index.css';
import '@zxio/zxui/style';
import '@/assets/styles/tailwind.css';
import { bindZxThemeHost } from '@/theme/zx-theme-host';
import { http } from '@/utils/http';
import { setupVXETable } from '@/plugins/vxe-table';
import { parseTime, resetForm, handleTree, selectDictLabel, addDateRange } from '@/utils/ruoyi';
import deployment from './theme-deployment.json';
import type { ThemeRuntimeDeploymentOutput } from '@zxio/theme-compiler/deployment';
import App from './App.vue';
import DictTag from '@/components/ui/DictTag/index.vue';
import Pagination from '@/components/ui/Pagination/index.vue';
import RightToolbar from '@/components/ui/RightToolbar/index.vue';

// Test-only in-memory transport. No authentication, refresh or business request leaves this page.
const fixtureProject = {
  projectId: 1,
  projectName: 'Fixture project',
  projectDesc: 'Fixture description',
  description: 'Fixture description',
};
const fixtureJob = {
  jobId: 1,
  jobName: 'Fixture scheduled job',
  jobGroup: 'fixture',
  jobExecutor: 'fixture',
  invokeTarget: 'fixture.noop',
  cronExpression: '0 0 12 * * ?',
  createTime: '2026-09-22 10:00:00',
  nextValidTime: '2026-09-24 12:00:00',
  status: '0',
  concurrent: '1',
  misfirePolicy: '0',
  jobArgs: 'fixture args',
  jobKwargs: '{fixture: true}',
};
http.axiosInstance.defaults.adapter = async (config) => {
  const url = config.url ?? '';
  const dict = [
    {
      dictLabel: 'Fixture option',
      dictValue: 'fixture',
      label: 'Fixture option',
      value: 'fixture',
    },
  ];
  const rows = [
    {
      ...fixtureProject,
      deviceId: 1,
      deviceName: 'Fixture device',
      name: 'Fixture category',
      categoryId: 1,
    },
  ];
  const data =
    url === '/monitor/job/list'
      ? { items: [fixtureJob], total: 1, page: 1, pageSize: 10 }
      : url === '/monitor/job/1'
        ? { ...fixtureJob }
        : url === '/monitor/jobLog/list'
          ? {
              items: [
                {
                  ...fixtureJob,
                  jobLogId: 7,
                  status: '1',
                  jobTrigger: 'Fixture trigger',
                  jobMessage: 'Fixture log message',
                  exceptionInfo: 'Fixture exception detail',
                },
              ],
              total: 1,
              page: 1,
              pageSize: 10,
            }
          : url === '/project/version/list'
            ? { items: [], total: 0, page: 1, pageSize: 10 }
            : /^\/system\/user\/?$/.test(url)
              ? {
                  posts: [{ postId: 1, postName: 'Fixture post', status: '0' }],
                  roles: [{ roleId: 1, roleName: 'Fixture role', status: '0' }],
                }
              : /Unique/.test(url)
                ? true
                : /dict|options|select|treeselect/.test(url)
                  ? { items: dict }
                  : /list/.test(url)
                    ? { items: rows, total: rows.length, page: 1, pageSize: 10 }
                    : fixtureProject;
  return { data, status: 200, statusText: 'OK', headers: {}, config };
};
const app = createApp(App);
app.use(createPinia());
app.use(
  createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }],
  })
);
app.use(ElementPlus);
app.use(ZXUI);
app.component('DictTag', DictTag);
app.component('Pagination', Pagination);
app.component('RightToolbar', RightToolbar);
for (const [name, component] of Object.entries(ElementIcons)) app.component(name, component);
app.directive('hasPermi', {});
app.config.globalProperties.useDict = (...names: string[]) =>
  Object.fromEntries(
    names.map((name) => [name, ref([{ label: 'Fixture option', value: 'fixture' }])])
  );
Object.assign(app.config.globalProperties, {
  parseTime,
  resetForm,
  handleTree,
  selectDictLabel,
  addDateRange,
  $modal: {
    msgSuccess() {},
    msgError() {},
    msgWarning() {},
    confirm: async () => true,
  },
});
setupVXETable(app);
// JSON imports widen schema/hash literals; the Host validates the fixture at runtime.
bindZxThemeHost(app, deployment as unknown as ThemeRuntimeDeploymentOutput);
app.mount('#app');
