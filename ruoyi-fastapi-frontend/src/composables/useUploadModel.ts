import { onScopeDispose, ref, watch } from 'vue';
import type { UploadFile, UploadUserFile } from 'element-plus';
import {
  assetContentUrl,
  discardFileAsset,
  getFileAssetMetadata,
  type AssetDescriptor,
} from '@/api/fileAssets';
import { queryScope, scopeRequestOptions, type QueryScope } from '@/queries/context';

export interface AssetUploadFile extends UploadUserFile {
  assetId?: string;
  mediaType?: string;
  unavailable?: boolean;
}

interface UploadModelOptions {
  /** The form value: asset ids in display order (the only persisted contract). */
  value: () => string[] | null | undefined;
  emit: (ids: string[]) => void;
  abort: (file?: Pick<UploadFile, 'uid'>) => void;
}

let uidSeed = Date.now();

const sameIds = (left: readonly string[], right: readonly string[]) =>
  left.length === right.length && left.every((id, index) => id === right[index]);

/**
 * The native upload list owns queued files; the parent receives committed asset ids only.
 * Removing an entry only changes the form. Drafts uploaded by this instance may be discarded
 * best-effort; anything that came from the saved value is never deleted from here.
 */
export function useUploadModel(options: UploadModelOptions) {
  const files = ref<AssetUploadFile[]>([]);
  const sessionDrafts = new Set<string>();
  let metadataController: AbortController | undefined;

  const project = (list: AssetUploadFile[]) =>
    list
      .filter((file) => file.assetId && (file.status ?? 'success') === 'success')
      .map((file) => file.assetId!);

  const describe = async (ids: string[], scope: QueryScope | null) => {
    metadataController?.abort();
    if (!ids.length || !scope) return;
    const controller = new AbortController();
    metadataController = controller;
    try {
      const result = await getFileAssetMetadata(
        ids,
        { signal: controller.signal },
        scopeRequestOptions(scope)
      );
      if (controller.signal.aborted || queryScope.value !== scope) return;
      const byId = new Map<string, AssetDescriptor>(
        result.items.map((item) => [item.assetId, item])
      );
      for (const file of files.value) {
        const descriptor = file.assetId ? byId.get(file.assetId) : undefined;
        if (descriptor) {
          file.name = descriptor.name;
          file.mediaType = descriptor.mediaType;
          file.size = descriptor.size;
        } else if (file.assetId && result.unavailableIds.includes(file.assetId)) {
          file.unavailable = true;
        }
      }
    } catch {
      // Descriptions are cosmetic; the ids and content URLs stay usable.
    }
  };

  watch(
    options.value,
    (input) => {
      const ids = [...(input ?? [])];
      if (sameIds(ids, project(files.value))) return;
      options.abort();
      for (const file of files.value) {
        if (file.url?.startsWith('blob:')) URL.revokeObjectURL(file.url);
      }
      const known = new Map(files.value.filter((f) => f.assetId).map((f) => [f.assetId!, f]));
      files.value = ids.map(
        (id) =>
          known.get(id) ?? {
            uid: ++uidSeed,
            assetId: id,
            name: '',
            status: 'success',
            url: assetContentUrl(id),
          }
      );
      void describe(
        ids.filter((id) => !known.get(id)?.name),
        queryScope.value
      );
    },
    { immediate: true, deep: true }
  );

  const publish = () => {
    const result = project(files.value);
    if (!sameIds(result, options.value() ?? [])) options.emit(result);
  };

  const success = (descriptor: AssetDescriptor, file: UploadFile, currentFiles: UploadFile[]) => {
    if (file.url?.startsWith('blob:')) URL.revokeObjectURL(file.url);
    const target = file as AssetUploadFile;
    target.assetId = descriptor.assetId;
    target.name = descriptor.name;
    target.mediaType = descriptor.mediaType;
    target.size = descriptor.size;
    target.url = descriptor.contentUrl;
    sessionDrafts.add(descriptor.assetId);
    files.value = currentFiles as AssetUploadFile[];
    publish();
  };

  const remove = (file: UploadFile, remainingFiles: UploadFile[]) => {
    options.abort(file);
    const assetId = (file as AssetUploadFile).assetId;
    if (assetId && sessionDrafts.delete(assetId) && queryScope.value) {
      void discardFileAsset(assetId, scopeRequestOptions(queryScope.value)).catch(() => undefined);
    }
    files.value = remainingFiles as AssetUploadFile[];
    publish();
  };

  /** Reorder within the field; only the id order changes (bindings keep their owner). */
  const move = (from: number, to: number) => {
    const list = [...files.value];
    const [item] = list.splice(from, 1);
    list.splice(to, 0, item);
    files.value = list;
    publish();
  };

  watch(queryScope, () => {
    metadataController?.abort();
    sessionDrafts.clear();
  });
  onScopeDispose(() => metadataController?.abort());
  return { files, success, remove, move };
}
