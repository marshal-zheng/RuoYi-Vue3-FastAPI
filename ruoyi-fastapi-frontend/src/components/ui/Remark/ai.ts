import type { ZxTextEditorFieldAIAdapter } from '@zxio/text-editor';
import { generateTextFieldAI, TextFieldAIError } from '@/api/system/textFieldAi';
import { reloadAIContextStatus } from '@/ai-context/status';
import { readRemark } from './contract';

/** Transport only. Context is captured once by the public scope kernel before this adapter is called. */
export function createRemarkAIAdapter(): ZxTextEditorFieldAIAdapter {
  return {
    async generate(request, options) {
      try {
        return await generateTextFieldAI(
          {
            ...request,
            selectedContextIds: [...request.selectedContextIds],
            document: readRemark(request.document),
            selection: readRemark(request.selection),
            candidate: readRemark(request.candidate),
            context: request.context.map((item) => ({
              ...item,
              value: typeof item.value === 'string' ? item.value : [...item.value],
            })),
          },
          options
        );
      } catch (error) {
        if (
          error instanceof TextFieldAIError &&
          ['policy-rejected', 'context-rejected'].includes(error.code)
        ) {
          // Refresh policy, but never replay a request or send new values without a new capture.
          void reloadAIContextStatus();
        }
        throw error;
      }
    },
  };
}
