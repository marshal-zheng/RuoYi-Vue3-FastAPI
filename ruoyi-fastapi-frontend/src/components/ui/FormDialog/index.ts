import { computed, reactive, shallowReactive, unref } from 'vue';
import { useDialog } from '@zxio/zxui';
import type { CSSProperties } from 'vue';
import { formLayoutPolicy, type FormColumns } from './policy';

export { default as FormGrid } from './FormGrid.vue';
export type { FormColumns } from './policy';

type DialogOptions<T extends Record<string, any>> = NonNullable<Parameters<typeof useDialog<T>>[0]>;
type FormDialogStyle = Omit<CSSProperties, 'width' | 'height'> & { width?: never; height?: never };
export type FormDialogOptions<T extends Record<string, any>> = Omit<
  DialogOptions<T>,
  'width' | 'height' | 'dialogStyle'
> & {
  columns: FormColumns;
  width?: never;
  height?: never;
  dialogStyle?: FormDialogStyle;
};

function checkColumns(columns: FormColumns) {
  if (![1, 2, 3].includes(columns)) {
    throw new TypeError('[useFormDialog] columns must explicitly be 1, 2 or 3');
  }
}

function sanitize<T extends Record<string, any>>(options: Partial<FormDialogOptions<T>>) {
  const { columns: _columns, width, height, dialogStyle, dialogSize: _size, ...rest } = options;
  const safeStyle = dialogStyle ? { ...dialogStyle } : undefined;
  if (
    import.meta.env.DEV &&
    (width !== undefined ||
      height !== undefined ||
      (safeStyle && ('width' in safeStyle || 'height' in safeStyle)))
  ) {
    console.warn(
      '[useFormDialog] width/height are ignored; use columns, dialogSize or dialogStyle.maxHeight'
    );
  }
  if (safeStyle) {
    delete safeStyle.width;
    delete safeStyle.height;
  }
  return { ...rest, ...(safeStyle ? { dialogStyle: safeStyle } : {}) };
}

export function useFormDialog<T extends Record<string, any> = Record<string, any>>(
  options: FormDialogOptions<T>
) {
  checkColumns(options.columns);
  const layoutProps = reactive({ columns: options.columns });
  const sizeOverride = shallowReactive({ value: options.dialogSize });
  const dialogSize = computed(() => {
    const size = unref(sizeOverride.value) ?? formLayoutPolicy.dialogSize[layoutProps.columns];
    if (!['sm', 'md', 'lg', 'xl', 'small', 'large'].includes(String(size))) {
      throw new TypeError('[useFormDialog] dialogSize must be a supported preset');
    }
    return size;
  });
  const dialog = useDialog<T>({ ...sanitize(options), dialogSize });
  return {
    ...dialog,
    formProps: { labelWidth: formLayoutPolicy.labelWidth },
    layoutProps,
    updateOptions(value: Partial<FormDialogOptions<T>>) {
      if (value.columns !== undefined) {
        checkColumns(value.columns);
        layoutProps.columns = value.columns;
      }
      if ('dialogSize' in value) sizeOverride.value = value.dialogSize;
      dialog.updateOptions({ ...sanitize(value), dialogSize });
    },
  };
}
