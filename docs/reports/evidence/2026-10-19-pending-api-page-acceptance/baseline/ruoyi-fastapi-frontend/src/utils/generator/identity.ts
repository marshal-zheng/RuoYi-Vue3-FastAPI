/** One component identity for the palette, saved designs, preview and export. */
export const generatorTags = Object.freeze({ input: 'zx-input' });

export function resolveGeneratorTag(tag: string): string {
  return tag === 'el-input' ? generatorTags.input : tag;
}

export function normalizeGeneratorFields<T extends { tag: string; children?: T[] }>(
  fields: T[]
): T[] {
  return fields.map((field) => ({
    ...field,
    tag: resolveGeneratorTag(field.tag),
    ...(field.children ? { children: normalizeGeneratorFields(field.children) } : {}),
  }));
}

interface LegacyLayoutField {
  span?: number;
  full?: boolean;
  children?: LegacyLayoutField[];
}

export function resolveGeneratorColumns(conf: {
  columns?: number;
  fields: LegacyLayoutField[];
}): 1 | 2 | 3 {
  if (conf.columns !== undefined) {
    if (conf.columns !== 1 && conf.columns !== 2 && conf.columns !== 3) {
      throw new TypeError('生成表单 columns 必须为 1、2 或 3');
    }
    return conf.columns;
  }
  // Read legacy geometry once at the export boundary; output uses field intent.
  const spans: number[] = [];
  const collect = (fields: LegacyLayoutField[]) =>
    fields.forEach((field) => {
      if (field.children) collect(field.children);
      else if (!field.full) spans.push(field.span || 24);
    });
  collect(conf.fields);
  return Math.min(3, Math.max(1, Math.ceil(24 / Math.min(24, ...spans)))) as 1 | 2 | 3;
}
