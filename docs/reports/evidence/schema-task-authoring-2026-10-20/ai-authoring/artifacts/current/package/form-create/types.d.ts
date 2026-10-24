import { Rule } from '@form-create/element-ui';
import { Values } from '../types';
import { FieldPath } from '../fields/types';
export type { Rule as NativeRule } from '@form-create/element-ui';
export type { FieldPath } from '../fields/types';
export type SchemaRule = Rule & {
    fullWidth?: boolean;
};
export type RuleFor<T extends object> = Omit<SchemaRule, 'field' | 'value'> & {
    field: Extract<keyof T, string>;
    value?: never;
};
export interface Definition {
    id: string;
    revision: number;
    engine: 'form-create@3.3.5';
    contract: 'zxui-schema-form-v1';
    rules: Rule[];
}
/** Import admission is separate from trusted code component registration. */
export type DefinitionPolicy = Record<string, {
    props: readonly string[];
}>;
export interface FieldIssue {
    /** Segments address the submitted editing value. Missing/unknown paths are form-level. */
    path?: FieldPath;
    message: string;
}
export interface ArrayKey {
    /** Path to an array. A numeric segment matches that concrete parent row. */
    path: FieldPath;
    /** Stable string/number property on every row; duplicates cannot be safely addressed. */
    key: string;
}
export type SaveResult<T extends object = Values> = {
    ok: true;
    values?: T;
} | {
    ok: false;
    issues: readonly FieldIssue[];
};
export type Save<T extends object = Values> = (values: T, signal: AbortSignal) => Promise<SaveResult<T>>;
export type FormPhase = 'idle' | 'validating' | 'saving' | 'blocked' | 'invalid' | 'saved' | 'error';
export interface BusinessContext<T extends object = Values> {
    read(): T;
    /** Record lifetime: reset does not cancel resources initialized once by createRules. */
    signal(): AbortSignal;
}
export interface SchemaFormInstance<T extends object = Values> {
    read(): T;
    reset(): void;
    submit(): Promise<boolean>;
    focus(path?: FieldPath): void;
    readonly dirty: boolean;
    readonly pending: boolean;
    readonly fieldPending: boolean;
    readonly blocked: boolean;
    readonly phase: FormPhase;
    readonly status: string;
}
