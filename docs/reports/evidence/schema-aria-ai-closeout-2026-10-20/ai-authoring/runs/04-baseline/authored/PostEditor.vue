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

const initial = { ...props.initial };
const save = createPostSave(props.api, props.postId);
const form = ref<SchemaFormInstance | null>(null);
</script>

<template>
  <ZxSchemaForm
    ref="form"
    :initial="initial"
    :create-rules="createPostRules"
    :save="save"
  />
  <div>
    <button type="button" :disabled="!form || form.pending" @click="form?.submit()">
      保存
    </button>
    <button type="button" :disabled="!form || form.pending" @click="form?.reset()">
      恢复
    </button>
  </div>
</template>
