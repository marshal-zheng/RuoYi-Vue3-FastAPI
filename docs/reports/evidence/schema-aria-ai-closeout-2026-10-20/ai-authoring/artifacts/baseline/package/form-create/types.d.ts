import { Rule } from '@form-create/element-ui';
import { Values } from '../types';
export type { Rule as NativeRule } from '@form-create/element-ui';
export type RuleFor<T> = Omit<Rule, 'field' | 'value'> & {
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
export interface FieldIssue {
    /** An empty or unknown field is displayed at form level. */
    field: string;
    message: string;
}
export type SaveResult = {
    ok: true;
} | {
    ok: false;
    issues: FieldIssue[];
};
export type Save = (values: Values, signal: AbortSignal) => Promise<SaveResult>;
export interface BusinessContext {
    read(): Values;
    signal(): AbortSignal;
}
export interface SchemaFormInstance {
    read(): Values;
    reset(): void;
    submit(): Promise<boolean>;
    readonly dirty: boolean;
    readonly pending: boolean;
    readonly status: string;
}
