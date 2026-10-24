<script setup lang="ts">
import { ref } from 'vue';
import { ZxSchemaForm } from '@zxio/schema-form/form-create';
import type { SchemaFormInstance } from '@zxio/schema-form/form-create';
import '@zxio/schema-form/style.css';
import type { PostApi, PostValues } from './domain';
import { createPostRules, createPostSave } from './post-form';

const props = defineProps<{
  initial: PostValues;
  postId?: number;
  api: PostApi;
}>();

const form = ref<SchemaFormInstance<PostValues>>();
const save = createPostSave(props.api, props.postId);
</script>

<template>
  <ZxSchemaForm
    ref="form"
    :initial="props.initial"
    :create-rules="createPostRules"
    :save="save"
    :columns="2"
  />
  <button type="button" :disabled="form?.pending" @click="form?.submit()">
    保存
  </button>
  <button type="button" :disabled="form?.pending" @click="form?.reset()">
    恢复
  </button>
</template>
