import { useAIContextStatusProvider } from '@/ai-context/status';
import { defineComponent } from 'vue';
import { RouterView } from 'vue-router';
import { ElConfigProvider } from 'element-plus';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import { ZxConfigProvider } from '@zxio/zxui/config-provider';
import { zxThemeConfig } from '@/theme/zx-theme-config';
import ModalFeedbackProvider from '@/plugins/ModalFeedbackProvider';

export default defineComponent({
  name: 'App',
  setup() {
    useAIContextStatusProvider();
    const overlayDividers = { divider: true };
    return () => (
      <ElConfigProvider locale={zhCn}>
        <ZxConfigProvider
          theme={zxThemeConfig.value}
          zxDialog={overlayDividers}
          zxDrawer={overlayDividers}
          modal={overlayDividers}
          message={{ appearance: 'surface' }}
          notification={{ appearance: 'surface' }}
          zxSearch={{ buttonPlacement: 'inside' }}
        >
          <ModalFeedbackProvider>
            <RouterView />
          </ModalFeedbackProvider>
        </ZxConfigProvider>
      </ElConfigProvider>
    );
  },
});
