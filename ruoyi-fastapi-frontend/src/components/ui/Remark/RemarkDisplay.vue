<template>
  <span v-if="result.error" role="alert">备注读取失败</span>
  <span v-else-if="!result.document">无备注</span>
  <span v-else-if="summary" :title="result.text">{{ remarkSummary(result.text) }}</span>
  <!-- HTML comes only from the library's safe-html renderer after A-profile admission. -->
  <!-- eslint-disable vue/no-v-html -->
  <div v-else class="zx-text-editor__prose" v-html="result.html" />
  <!-- eslint-enable vue/no-v-html -->
</template>
<script setup lang="ts">
import { computed } from 'vue';
import { renderDocumentToHTML, renderDocumentToText } from '@zxio/text-editor';
import { validateBasicRichTextDocument } from '@zxio/text-editor/core';
import '@zxio/text-editor/style.css';
import { remarkSummary } from './contract';
const props = defineProps<{ value: unknown; text?: string; summary?: boolean }>();
const result = computed(() => {
  try {
    const document = validateBasicRichTextDocument(props.value ?? null);
    return {
      document,
      html:
        document && !props.summary ? renderDocumentToHTML(document, { profile: 'safe-html' }) : '',
      text: props.text ?? (document ? renderDocumentToText(document) : ''),
      error: false,
    };
  } catch {
    return { document: null, html: '', text: '', error: true };
  }
});
</script>
