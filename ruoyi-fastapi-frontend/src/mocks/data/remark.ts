import type { RemarkDocumentInput } from '@/api/_generated/types.gen';
/** Explicit plain-text mock fixture boundary, never an API string fallback. */
export function mockRemark(text: string, key: string): RemarkDocumentInput | null {
  if (text === '') return null;
  return {
    version: 2,
    body: {
      format: 'json',
      content: {
        type: 'doc',
        content: text.split('\n').map((line, i) => ({
          type: 'paragraph',
          attrs: { textAlign: null, blockId: `blk_${key}${i}` },
          ...(line ? { content: [{ type: 'text' as const, text: line }] } : {}),
        })),
      },
    },
    assets: [],
    annotations: [],
    meta: { schemaVersion: 'stable-block-identity/v2' },
  };
}
