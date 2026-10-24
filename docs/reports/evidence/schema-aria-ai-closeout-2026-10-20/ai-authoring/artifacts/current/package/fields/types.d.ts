import { Json } from '../types';
/** Data addressing only; interpretation and stable row identity belong to the host. */
export type FieldPath = readonly (string | number)[];
export interface FieldMessage {
    severity: 'error' | 'warning' | 'info';
    message: string;
    /** Relative to the receiving composite field. */
    path?: FieldPath;
}
/** A complete snapshot: omitted pending/blocking mean false/empty in every host. */
export interface FieldEditState {
    /** Activity indicator. Non-blocking option refreshes may set this alone. */
    pending?: boolean;
    /** Unfinished edits that the host must check at every commit entry point. */
    blocking?: readonly FieldMessage[];
}
export interface FieldControl {
    focus(path?: FieldPath): void;
    /** Composite validation is invoked by the host's submit pipeline. */
    validate?(): boolean | Promise<boolean>;
}
export interface FieldControlAttrs {
    id: string;
    'aria-required'?: true;
    'aria-invalid'?: true;
    'aria-describedby'?: string;
    'aria-labelledby'?: string;
}
export interface NumberTextEdit {
    text: string;
    badInput: boolean;
}
export type ParsedNumberText = {
    status: 'empty';
} | {
    status: 'valid';
    value: number;
} | {
    status: 'invalid';
};
export interface JsonTextEdit {
    text: string;
    badInput: boolean;
}
export type ParsedJsonText = {
    status: 'empty';
} | {
    status: 'valid';
    value: Json;
} | {
    status: 'invalid';
};
