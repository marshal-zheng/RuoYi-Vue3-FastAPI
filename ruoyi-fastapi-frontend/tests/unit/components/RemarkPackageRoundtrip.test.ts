// @vitest-environment happy-dom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { ZxTextEditor, ZxTextEditorField, renderDocumentToHTML } from '@zxio/text-editor';
import { validateBasicRichTextDocument } from '@zxio/text-editor/core';
import { createRemarkFieldTestHost } from '../../helpers/remark-field-public';

const fixtures = resolve(process.cwd(), '../shared/remarks/remark-a-v1');
const manifest = JSON.parse(readFileSync(resolve(fixtures, 'manifest.json'), 'utf8')) as {
  vectors: { file: string; normalized?: unknown }[];
};
const legalVectors = manifest.vectors.filter(({ file }) => file.startsWith('valid/'));
let host: ReturnType<typeof createRemarkFieldTestHost>;

beforeEach(() => {
  host = createRemarkFieldTestHost('remark-public-roundtrip');
  host.attach();
});
afterEach(() => host.dispose());

describe('public remark package acceptance, JSON persistence, re-edit and safe rendering', () => {
  it.each(legalVectors)('$file', async ({ file, normalized }) => {
    const fixture = JSON.parse(readFileSync(resolve(fixtures, file), 'utf8'));
    const canonical = validateBasicRichTextDocument(fixture);
    if (normalized !== undefined) expect(canonical).toEqual(normalized);
    let saved = JSON.parse(JSON.stringify(canonical));
    for (let opening = 0; opening < 2; opening++) {
      const wrapper = mount(ZxTextEditorField, {
        attachTo: document.body,
        props: { modelValue: saved },
        global: host.global,
      });
      try {
        await flushPromises();
        const editor = wrapper.findComponent(ZxTextEditor);
        expect(editor.exists()).toBe(true);
        const document = editor.vm.$.exposed!.getDocument();
        // Empty documents receive an ephemeral editor block ID; normalization restores null.
        const edited = validateBasicRichTextDocument(document);
        expect(edited).toEqual(canonical);
        const html = edited ? renderDocumentToHTML(edited, { profile: 'safe-html' }) : '';
        expect(html).not.toMatch(/<\s*script\b|javascript\s*:/i);
        saved = JSON.parse(JSON.stringify(edited));
      } finally {
        wrapper.unmount();
      }
    }
  });
});
