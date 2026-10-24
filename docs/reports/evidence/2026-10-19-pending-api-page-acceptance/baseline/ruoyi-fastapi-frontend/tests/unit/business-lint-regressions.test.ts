import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from '@vue/compiler-sfc';
import { parse as parseJavaScript } from '@babel/parser';
import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import { useSimulationData } from '@/views/project/simulation/composables/useSimulationData';

/** Execute the actual private SFC function with its external boundaries supplied. */
function executeSetupFunction(
  file: string,
  name: string,
  bindings: Record<string, unknown>
): unknown {
  const { descriptor } = parse(readFileSync(file, 'utf8'));
  const source = descriptor.scriptSetup?.content;
  if (!source) throw new Error('Expected a script setup');
  const declaration = parseJavaScript(source, {
    sourceType: 'module',
  }).program.body.find((node) => node.type === 'FunctionDeclaration' && node.id?.name === name);
  if (!declaration || declaration.start === null || declaration.end === null) {
    throw new Error(`Missing setup function: ${name}`);
  }
  const code = source.slice(declaration.start, declaration.end);
  const execute = new Function(...Object.keys(bindings), `${code}; return ${name}();`);
  return execute(...Object.values(bindings));
}

describe('business behavior after lint cleanup', () => {
  it.each([true, false])(
    'register consumes the actual captcha response (enabled=%s)',
    (enabled) => {
      const captchaEnabled = ref(true);
      const codeUrl = ref('');
      const registerForm = ref({ uuid: '' });
      const response = {
        captchaEnabled: enabled,
        img: 'GIF',
        uuid: 'captcha-1',
      };
      executeSetupFunction(resolve('src/views/register.vue'), 'getCode', {
        captchaEnabled,
        codeUrl,
        registerForm,
        getCodeImg: () => ({
          then: (onResolved: (value: typeof response) => void) => onResolved(response),
        }),
      });
      expect(captchaEnabled.value).toBe(enabled);
      expect(codeUrl.value).toBe(enabled ? 'data:image/gif;base64,GIF' : '');
      expect(registerForm.value.uuid).toBe(enabled ? 'captcha-1' : '');
    }
  );

  it('readonly snapshot failure completes its fallback without a second exception', async () => {
    const warning = vi.fn();
    const result = executeSetupFunction(
      resolve('src/views/project/simulation/index.vue'),
      'loadReadonlySimulationSnapshot',
      {
        createSimulationSession: async () => {
          throw new Error('API unavailable');
        },
        projectId: ref(1),
        versionId: ref(2),
        isReadonlySession: ref(false),
        ElMessage: { warning },
      }
    );
    await expect(result).resolves.toBeUndefined();
    expect(warning).toHaveBeenCalledExactlyOnceWith('无法加载只读演示数据');
  });

  const conditionLogics: ('and' | 'or')[] = ['and', 'or'];
  it.each(conditionLogics)(
    'keeps both source and destination port conditions in %s searches',
    (logic) => {
      let data: ReturnType<typeof useSimulationData> | undefined;
      const wrapper = mount({
        setup() {
          data = useSimulationData(ref(null));
          return () => null;
        },
      });
      if (!data) throw new Error('Simulation data was not initialized');
      data.setMessageFilter({
        conditionLogic: logic,
        conditions: [
          { type: 'node', field: 'senderPortId', value: 'CAN-1' },
          { type: 'node', field: 'receiverPortId', value: 'CAN-2' },
        ],
      });
      data.updateMessageData([
        { messageId: 'match', senderPortId: 'CAN-1', receiverPortId: 'CAN-2' },
        { messageId: 'sender-only', senderPortId: 'CAN-1', receiverPortId: 'LAN-2' },
        { messageId: 'other', senderPortId: 'LAN-1', receiverPortId: 'LAN-2' },
      ]);
      expect(data.filteredMessages.value.map((message) => message.messageId)).toEqual(
        logic === 'and' ? ['match'] : ['match', 'sender-only']
      );
      wrapper.unmount();
    }
  );
});
