<template>
  <ZxContentWrap title="系统接口" fill>
    <template #header-right>
      <ZxButton @click="documentKey++">重新加载文档</ZxButton>
    </template>
    <iframe
      :key="documentKey"
      title="API 接口文档"
      :srcdoc="documentHtml"
      class="api-document"
      data-zx-fill
    />
  </ZxContentWrap>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import swaggerScriptUrl from 'swagger-ui-dist/swagger-ui-bundle.js?url';
import swaggerCssUrl from 'swagger-ui-dist/swagger-ui.css?url';

const documentKey = ref(0);
const apiBase = new URL(
  (import.meta.env.VITE_APP_BASE_API || '/api').replace(/\/$/, ''),
  window.location.origin
).href;
const jsValue = (value: string) => JSON.stringify(value).replace(/</g, '\\u003c');
// Keep Swagger's document and styles in its own frame; serve both assets locally.
const documentHtml = `<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><title>API 接口文档</title>
<link rel="stylesheet" href=${jsValue(swaggerCssUrl)}>
</head><body><div id="swagger-ui" role="status">正在加载接口文档…</div>
<script src=${jsValue(swaggerScriptUrl)}>${'<'}/script>
<script>
fetch(${jsValue(apiBase + '/openapi.json')}, { credentials: 'same-origin' })
  .then(response => { if (!response.ok) throw new Error('文档请求失败'); return response.json(); })
  .then(spec => {
    spec.servers = [{ url: ${jsValue(apiBase)} }];
    SwaggerUIBundle({ spec, dom_id: '#swagger-ui', layout: 'BaseLayout',
      deepLinking: false, validatorUrl: null, docExpansion: 'none' });
  })
  .catch(() => { document.getElementById('swagger-ui').textContent = '接口文档加载失败，请点击重新加载文档重试。'; });
${'<'}/script></body></html>`;
</script>

<style scoped>
.api-document {
  width: 100%;
  min-height: 0;
  border: 0;
}
</style>
