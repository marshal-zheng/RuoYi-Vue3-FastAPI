import { ref, watch } from 'vue';
import type { UploadFile, UploadUserFile } from 'element-plus';
import type { UploadedResource } from './useAuthenticatedUpload';

type ModelValue = string | Array<string | UploadUserFile> | undefined;

/** The native upload file list owns queued files; the parent receives committed paths only. */
export function useUploadModel(
  value: () => ModelValue,
  emit: (event: 'update:modelValue', value: string) => void,
  abort: (file?: Pick<UploadFile, 'uid'>) => void,
  displayUrl: (url: string) => string = (url) => url,
  modelUrl: (url: string) => string = (url) => url
) {
  const files = ref<UploadUserFile[]>([]);
  const project = (list: UploadUserFile[]) =>
    list
      .filter(
        (file) =>
          file.url &&
          !file.url.startsWith('blob:') &&
          !['ready', 'uploading', 'fail'].includes(file.status || '')
      )
      .map((file) => modelUrl(file.url!))
      .join(',');
  const normalize = (input: ModelValue) => {
    const list = Array.isArray(input) ? input : input ? input.split(',') : [];
    return list.map(
      (item): UploadUserFile =>
        typeof item === 'string'
          ? { name: item, url: displayUrl(item), status: 'success' }
          : { ...item, url: item.url ? displayUrl(item.url) : undefined }
    );
  };
  watch(
    value,
    (input) => {
      const next = normalize(input);
      if (project(next) === project(files.value)) return;
      abort();
      for (const file of files.value) {
        if (file.url?.startsWith('blob:')) URL.revokeObjectURL(file.url);
      }
      files.value = next;
    },
    { immediate: true, deep: true }
  );
  const publish = () => {
    const result = project(files.value);
    if (result !== project(normalize(value()))) emit('update:modelValue', result);
  };
  const success = (resource: UploadedResource, file: UploadFile, currentFiles: UploadFile[]) => {
    if (file.url?.startsWith('blob:')) URL.revokeObjectURL(file.url);
    file.url = displayUrl(resource.fileName);
    files.value = currentFiles;
    publish();
  };
  const remove = (file: UploadFile, remainingFiles: UploadFile[]) => {
    abort(file);
    files.value = remainingFiles;
    publish();
  };
  return { files, success, remove };
}
