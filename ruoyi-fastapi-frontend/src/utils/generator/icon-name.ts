import names from '@/icons/element-names.json';

const elementIconNames = new Set(names);

/** Metadata contains names only; it never imports the complete icon implementations. */
export function isElementIconName(value: unknown): value is string {
  return typeof value === 'string' && elementIconNames.has(value);
}
