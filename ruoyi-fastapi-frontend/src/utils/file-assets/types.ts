import registry from './types.generated.json';

/** Registered file type id (backend `modules/file_assets/domain/types.py`, exported as JSON). */
export type FileTypeId = keyof typeof registry.types;

export const IMAGE_TYPE_IDS = registry.imageTypeIds as FileTypeId[];
export const OFFICE_BASELINE_TYPE_IDS = registry.officeBaselineTypeIds as FileTypeId[];
export const MAX_IMAGE_BYTES = registry.maxImageBytes;
export const MAX_ATTACHMENT_BYTES = registry.maxAttachmentBytes;

const types = registry.types as Record<
  string,
  { extensions: string[]; mediaType: string; family: string }
>;

const extensionOf = (name: string): string => {
  const dot = name.lastIndexOf('.');
  return dot > 0 ? name.slice(dot).toLowerCase() : '';
};

/** `accept` attribute derived from the same field declaration the server validates against. */
export function acceptFor(typeIds: readonly string[]): string {
  return typeIds.flatMap((typeId) => types[typeId]?.extensions ?? []).join(',');
}

/** Human readable extension list for upload hints, e.g. `pdf/docx`. */
export function describeTypes(typeIds: readonly string[]): string {
  return typeIds
    .flatMap((typeId) => types[typeId]?.extensions ?? [])
    .map((extension) => extension.slice(1))
    .join('/');
}

/** Client-side precheck only; the server re-validates name, extension, MIME and content. */
export function isAllowedFileName(name: string, typeIds: readonly string[]): boolean {
  const extension = extensionOf(name);
  return (
    Boolean(extension) && typeIds.some((typeId) => types[typeId]?.extensions.includes(extension))
  );
}

export function isImageMediaType(mediaType: string | undefined): boolean {
  return Boolean(
    mediaType && Object.values(types).some((t) => t.family === 'image' && t.mediaType === mediaType)
  );
}
