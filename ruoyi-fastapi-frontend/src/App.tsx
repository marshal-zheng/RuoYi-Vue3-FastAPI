import { defineComponent } from 'vue';
import { RouterView } from 'vue-router';
import { ElConfigProvider } from 'element-plus';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import { ZxConfigProvider } from '@zxio/zxui';
import { zxThemeConfig } from '@/theme/zx-theme-config';

export default defineComponent({
  name: 'App',
  setup() {
    return () => (
      <ElConfigProvider locale={zhCn}>
        <ZxConfigProvider theme={zxThemeConfig.value}>
          <RouterView />
        </ZxConfigProvider>
      </ElConfigProvider>
    );
  },
});
