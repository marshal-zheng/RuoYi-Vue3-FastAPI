import { computed, reactive, shallowReactive, unref } from 'vue';
import { useDialog } from '@zxio/zxui/hooks';
import type { DialogOptions } from '@zxio/zxui/hooks';
import type { CSSProperties } from 'vue';
import { formLayoutPolicy, type FormColumns } from './policy';

export { default as FormGrid } from './FormGrid.vue';
export type { FormColumns } from './policy';

type FormDialogStyle = Omit<CSSProperties, 'width' | 'height'> & { width?: never; height?: never };
export type FormDialogOptions<T extends object> = Omit<
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

function sanitize<T extends object>(options: Partial<FormDialogOptions<T>>) {
  const safeStyle = options.dialogStyle ? { ...options.dialogStyle } : undefined;
  if (
    options.width !== undefined ||
    options.height !== undefined ||
    (safeStyle && ('width' in safeStyle || 'height' in safeStyle))
  ) {
    throw new TypeError(
      '[useFormDialog] width/height are unsupported; use columns, dialogSize or dialogStyle.maxHeight'
    );
  }
  const rest = { ...options };
  delete rest.columns;
  delete rest.width;
  delete rest.height;
  delete rest.dialogStyle;
  delete rest.dialogSize;
  return { ...rest, ...(safeStyle ? { dialogStyle: safeStyle } : {}) };
}

export function useFormDialog<T extends object = Record<string, unknown>>(
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
  const dialog = useDialog<T>({ showFullScreen: false, ...sanitize(options), dialogSize });
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

/** SchemaForm owns values and validation; this entry shares presentation policy only. */
export function schemaFormDialog(options: { columns: FormColumns }) {
  checkColumns(options.columns);
  return {
    dialogProps: {
      dialogSize: formLayoutPolicy.dialogSize[options.columns],
      showFullScreen: false,
    },
    schemaFormProps: {
      labelWidth: formLayoutPolicy.labelWidth,
      labelPosition: 'left' as const,
    },
  };
}
