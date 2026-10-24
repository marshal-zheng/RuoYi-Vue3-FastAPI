<script setup lang="ts">
import { shallowRef } from 'vue';
import { ZxSchemaForm } from '@zxio/schema-form/form-create';
import type { SchemaFormInstance } from '@zxio/schema-form/form-create';
import type { PostApi, PostValues } from './domain';
import { createPostRules, createPostSave } from './post-form';
import '@zxio/schema-form/style.css';

const props = defineProps<{
  initial: PostValues;
  postId?: number;
  api: PostApi;
}>();

const initial = props.initial;
const rules = createPostRules();
const createRules = () => rules;
const save = createPostSave(props.api, props.postId);
const form = shallowRef<SchemaFormInstance<PostValues>>();
</script>

<template>
  <ZxSchemaForm
    ref="form"
    :initial="initial"
    :create-rules="createRules"
    :save="save"
  />
  <button type="button" :disabled="form?.pending" @click="form?.submit()">
    保存
  </button>
  <button type="button" :disabled="form?.pending" @click="form?.reset()">
    恢复
  </button>
</template>
