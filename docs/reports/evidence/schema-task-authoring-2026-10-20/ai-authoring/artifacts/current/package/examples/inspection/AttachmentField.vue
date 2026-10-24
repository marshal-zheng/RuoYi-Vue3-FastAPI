<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ZxUpload } from '@zxio/zxui/upload'
import { equal } from '@zxio/schema-form'

import type {
  UploadFile,
  UploadFiles,
  UploadRequestOptions,
} from 'element-plus'
import type { Attachment } from './model'
import type { FieldEditState, FieldMessage } from '@zxio/schema-form/fields'
import type { ZxUploadInstance } from '@zxio/zxui/upload'

defineOptions({ inheritAttrs: false })
const props = defineProps<{
  modelValue: Attachment[]
  disabled?: boolean
  messages?: readonly FieldMessage[]
  upload: (file: File, signal: AbortSignal) => Promise<Attachment>
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: Attachment[]): void
  (e: 'edit-state', state: FieldEditState): void
}>()
let uid = 1
let alive = true
const requests = new Map<number, AbortController>()
const files = ref<UploadFiles>(
  props.modelValue.map((file) => ({
    name: file.name,
    status: 'success',
    uid: uid++,
    response: file,
  }))
)
const error = ref('')
const root = ref<HTMLElement>()
const uploader = ref<ZxUploadInstance>()
defineExpose({
  focus: () => root.value?.querySelector<HTMLButtonElement>('button')?.focus(),
})
function report() {
  emit('edit-state', {
    pending: requests.size > 0,
    blocking: requests.size
      ? [{ severity: 'error', message: '请等待附件上传完成' }]
      : [],
  })
}
function committed() {
  return files.value
    .filter((file) => file.status === 'success')
    .map((file) => file.response as Attachment)
}
function publish() {
  if (alive && !equal(committed(), props.modelValue))
    emit('update:modelValue', committed())
}
async function removed() {
  // ElUpload emits remove before its passive file-list model reaches this field.
  await nextTick()
  publish()
}
function cancel(uid: number) {
  const controller = requests.get(uid)
  if (!controller) return
  requests.delete(uid)
  controller.abort()
  uploader.value?.abort?.({ uid })
  report()
}
function cancelAll() {
  const controllers = [...requests.values()]
  requests.clear()
  controllers.forEach((controller) => controller.abort())
  uploader.value?.abort?.()
  report()
}
async function request(options: UploadRequestOptions) {
  cancel(options.file.uid)
  const controller = new AbortController()
  requests.set(options.file.uid, controller)
  report()
  error.value = ''
  const active = () => alive && requests.get(options.file.uid) === controller
  const finish = () => {
    if (requests.get(options.file.uid) !== controller) return
    requests.delete(options.file.uid)
    report()
  }
  // ElUpload attaches these callbacks to the returned Promise. AbortSignal is
  // cooperative, so retired requests must not reach a new file with the same UID.
  const onSuccess = options.onSuccess
  const onError = options.onError
  options.onSuccess = (value) => {
    if (!active()) return
    try {
      onSuccess(value)
    } finally {
      finish()
    }
  }
  options.onError = (failure) => {
    if (!active()) return
    try {
      onError(failure)
    } finally {
      finish()
    }
  }
  return props.upload(options.file, controller.signal)
}
function remove(file: UploadFile) {
  cancel(file.uid)
  return true
}
watch(
  () => props.modelValue,
  (value) => {
    if (equal(value, committed())) return
    cancelAll()
    error.value = ''
    files.value = value.map((file) => ({
      name: file.name,
      status: 'success',
      uid: uid++,
      response: file,
    }))
  }
)
onBeforeUnmount(() => {
  alive = false
  cancelAll()
})
</script>

<template>
  <div ref="root" v-bind="$attrs" data-attachments>
    <ZxUpload
      ref="uploader"
      v-model="files"
      :disabled="disabled"
      :http-request="request"
      :before-remove="remove"
      :allow-preview="false"
      :allow-download="false"
      accept=".txt,.png,.jpg,.pdf"
      :max-size="5 * 1024 * 1024"
      button-text="上传巡检附件"
      tip-text="试点使用内存服务，附件不发送到外部服务器"
      @change="publish"
      @remove="removed"
      @error="error = '附件处理失败，请重试'"
    />
    <p v-if="error" role="alert">{{ error }}</p>
    <ul v-if="messages?.length" role="alert">
      <li v-for="(message, index) in messages" :key="index">
        {{ message.message }}
      </li>
    </ul>
  </div>
</template>
