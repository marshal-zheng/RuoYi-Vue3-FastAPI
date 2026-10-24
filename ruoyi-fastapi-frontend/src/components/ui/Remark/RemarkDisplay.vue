<template>
  <span v-if="result.error" role="alert">备注读取失败</span>
  <span v-else-if="!result.document">无备注</span>
  <span v-else-if="summary" :title="result.text">{{ remarkSummary(result.text) }}</span>
  <!-- The library view renders the admitted document through its safe-html policy. -->
  <ZxTextEditorView v-else :document="result.document" />
</template>
<script setup lang="ts">
import { computed } from 'vue';
import { ZxTextEditorView, renderDocumentToText } from '@zxio/text-editor';
import { validateBasicRichTextDocument } from '@zxio/text-editor/core';
import '@zxio/text-editor/style.css';
import { remarkSummary } from './contract';
const props = defineProps<{ value: unknown; text?: string; summary?: boolean }>();
const result = computed(() => {
  try {
    const document = validateBasicRichTextDocument(props.value ?? null);
    return {
      document,
      text: props.text ?? (document ? renderDocumentToText(document) : ''),
      error: false,
    };
  } catch {
    return { document: null, text: '', error: true };
  }
});
</script>
