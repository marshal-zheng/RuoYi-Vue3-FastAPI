import type { VxeColumnSlotTypes } from 'vxe-table';
import type { InputHTMLAttributes } from 'vue';

export type DictEditorRow = Record<string, string | number | boolean | null | undefined>;

export type DictEditorScalar = string | number | undefined;
export type DictEditorValue = DictEditorScalar | { value: DictEditorScalar; label?: string };

export type DictAutocompleteProps = {
  dictType?: string;
  placeholder?: string;
  disabled?: boolean;
  inputType?: InputHTMLAttributes['type'];
  clearable?: boolean;
  uppercaseLabel?: boolean;
};

/** The DictAutocomplete renderer supplies the value on the VXE cell parameters. */
export type DictAutocompleteCellParams<Row> = VxeColumnSlotTypes.EditSlotParams<Row> & {
  value?: DictEditorValue;
};

export type DictAutocompleteRenderOptions<Row> = {
  name: 'DictAutocomplete';
  props?:
    | DictAutocompleteProps
    | ((params: DictAutocompleteCellParams<Row>) => DictAutocompleteProps);
  events?: Partial<
    Record<
      'input' | 'change',
      (params: DictAutocompleteCellParams<Row>, value?: DictEditorValue) => void
    >
  >;
};

export type DictAutocompleteParams = DictAutocompleteProps & {
  row?: DictEditorRow;
  column?: { field: string };
};
