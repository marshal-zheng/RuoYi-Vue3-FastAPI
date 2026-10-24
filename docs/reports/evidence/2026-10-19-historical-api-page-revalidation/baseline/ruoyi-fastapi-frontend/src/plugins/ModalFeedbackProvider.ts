import { defineComponent, getCurrentInstance, onUnmounted, watch } from 'vue';
import { useThemeScope } from '@zxio/zxui/theme-provider';
import { useZxFeedback } from '@zxio/zxui/config-provider';
import { createModal } from '@/plugins/modal';
import { bindMessageFeedback } from '@/utils/feedback/message';
import { bindNotificationFeedback } from '@/utils/feedback/notification';

export default defineComponent({
  name: 'ModalFeedbackProvider',
  setup(_, { slots }) {
    const feedback = useZxFeedback();
    if (!feedback.ok) {
      throw new Error(feedback.diagnostics.map(({ code }) => code).join(', '));
    }
    const globals = getCurrentInstance()!.appContext.config.globalProperties;
    const previous = globals.$modal;
    const modal = createModal(feedback.value);
    globals.$modal = modal;
    const scope = useThemeScope();
    if (!scope.ok) throw new Error(scope.diagnostics.map(({ code }) => code).join(', '));
    let unbindMessage: (() => void) | undefined;
    let unbindNotification: (() => void) | undefined;
    watch(
      scope.value,
      (owner) => {
        if (owner && !unbindMessage) {
          unbindMessage = bindMessageFeedback(feedback.value.message);
          unbindNotification = bindNotificationFeedback(feedback.value.notification);
        }
      },
      { immediate: true }
    );
    onUnmounted(() => {
      unbindMessage?.();
      unbindNotification?.();
      if (globals.$modal === modal) globals.$modal = previous;
    });
    return () => slots.default?.();
  },
});
