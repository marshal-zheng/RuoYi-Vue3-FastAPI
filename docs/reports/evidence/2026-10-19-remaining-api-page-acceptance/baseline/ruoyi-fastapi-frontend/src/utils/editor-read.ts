import { onScopeDispose, ref, watch, type Ref } from 'vue';
import { isAbortError, type HttpError } from '@zxio/http';
import { ElMessage } from 'element-plus';
import { presentRequestError } from '@/utils/http';

interface EditorRead {
  signal: AbortSignal;
  isCurrent: () => boolean;
}

/** One editor opening owns its reads, feedback and loading, including deferred tree updates. */
export function useEditorRead(visible: () => boolean, loading: Ref<boolean> = ref(false)) {
  const error = ref('');
  let active: AbortController | undefined;
  let disposed = false;

  const cancel = () => {
    const controller = active;
    active = undefined;
    loading.value = false;
    controller?.abort('editor-opening-ended');
  };
  watch(
    visible,
    (value) => {
      if (!value) cancel();
    },
    { flush: 'sync' }
  );
  onScopeDispose(() => {
    disposed = true;
    cancel();
  });

  const run = async (action: (read: EditorRead) => void | Promise<void>): Promise<void> => {
    cancel();
    if (disposed) return;
    const controller = new AbortController();
    active = controller;
    const isCurrent = () => !disposed && active === controller;
    loading.value = true;
    error.value = '';
    try {
      await action({ signal: controller.signal, isCurrent });
    } catch (failure) {
      if (isCurrent() && !isAbortError(failure)) {
        // A failed parallel read also ends the sibling requests of this opening.
        controller.abort('editor-read-failed');
        error.value = failure instanceof Error ? failure.message : '获取信息失败，请重试';
        const problem = failure as HttpError & { problem?: unknown };
        if (problem?.problem) {
          presentRequestError(problem, {
            ...problem.config,
            silentError: false,
            feedback: { mode: 'auto' },
          });
        } else {
          ElMessage.error(error.value);
        }
      }
      throw failure;
    } finally {
      if (isCurrent()) {
        active = undefined;
        loading.value = false;
      }
    }
  };
  return { loading, error, run, cancel };
}
