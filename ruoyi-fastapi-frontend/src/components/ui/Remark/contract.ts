import { BASIC_RICH_TEXT_LIMITS, validateBasicRichTextDocument } from '@zxio/text-editor/core';
import type { RemarkDocumentInput } from '@/api/_generated/types.gen';

export type RemarkValue =
  | (Omit<RemarkDocumentInput, 'annotations' | 'assets'> & { annotations: []; assets: [] })
  | null;
export const REMARK_LIMITS = BASIC_RICH_TEXT_LIMITS;

/** Generated API types are narrowed through the library's public content policy. */
export function readRemark(value: unknown): RemarkValue {
  return validateBasicRichTextDocument(value ?? null, REMARK_LIMITS) as RemarkValue;
}
export function remarkSummary(value: string, length = 160): string {
  const segments = [...new Intl.Segmenter('zh', { granularity: 'grapheme' }).segment(value)];
  return segments.length > length
    ? segments
        .slice(0, length)
        .map((part) => part.segment)
        .join('') + '…'
    : value;
}
