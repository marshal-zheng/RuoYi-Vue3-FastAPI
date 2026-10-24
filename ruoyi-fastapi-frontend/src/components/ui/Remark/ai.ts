import type { ZxTextEditorDocument, ZxTextEditorFieldAIAdapter } from '@zxio/text-editor';
import { generateRemarkAI, type RemarkAiRequest } from '@/api/system/remarkAi';
import { readRemark } from './contract';

export type RemarkAIScene = RemarkAiRequest['scene'];
export type RemarkAIContextSource = () => Readonly<Record<string, unknown>>;

// This is a business context contract, not a serialization of the whole form.
const contextKeys = {
  user: ['userName', 'nickName', 'deptName', 'postNames', 'roleNames', 'status'],
  role: ['roleName', 'roleKey', 'menuNames', 'status'],
  post: ['postName', 'postCode', 'status'],
  dictType: ['dictName', 'dictType', 'status'],
  dictData: ['dictName', 'dictType', 'dictLabel', 'dictValue', 'status'],
  config: ['configName', 'configKey', 'configType'],
  genTable: ['tableName', 'tableComment', 'className', 'functionAuthor'],
} as const satisfies Record<RemarkAIScene, readonly string[]>;

export function captureRemarkAIContext(
  scene: RemarkAIScene,
  source: Readonly<Record<string, unknown>>
): Record<string, string | string[]> {
  const context: Record<string, string | string[]> = {};
  for (const key of contextKeys[scene]) {
    const value = source[key];
    if (typeof value === 'string' && value.trim()) context[key] = value.trim();
    else if (Array.isArray(value) && value.every((item) => typeof item === 'string')) {
      const items = value.map((item: string) => item.trim()).filter(Boolean);
      if (items.length) context[key] = items;
    }
  }
  return context;
}

export function createRemarkAIAdapter(
  scene: RemarkAIScene,
  context: RemarkAIContextSource
): ZxTextEditorFieldAIAdapter {
  return {
    async generate(request, options) {
      const result = await generateRemarkAI(
        {
          scene,
          instruction: request.instruction,
          target: request.target,
          document: readRemark(request.document),
          selection: readRemark(request.selection),
          candidate: readRemark(request.candidate),
          context: captureRemarkAIContext(scene, context()),
        },
        options
      );
      // The API adapter admits the result through the same public document validator.
      return result as ZxTextEditorDocument | null;
    },
  };
}
