import { Api } from '@form-create/element-ui';
import { ComputedRef, Ref } from 'vue';
import { Values } from './types';
import { ArrayKey, FieldIssue, FormPhase, Save } from './form-create/types';
import { FieldControl, FieldEditState, FieldMessage, FieldPath } from './fields/types';
interface CompositePort {
    messages: ComputedRef<readonly FieldMessage[]>;
    report(state: FieldEditState): void;
    dispose(): void;
}
export interface Session<T extends object = Values> {
    key: Readonly<Ref<number>>;
    seed: Readonly<Ref<T>>;
    pending: Readonly<Ref<boolean>>;
    phase: Readonly<Ref<FormPhase>>;
    status: Readonly<Ref<string>>;
    issues: Readonly<Ref<readonly FieldIssue[]>>;
    formIssues: ComputedRef<readonly FieldIssue[]>;
    dirty: ComputedRef<boolean>;
    fieldPending: ComputedRef<boolean>;
    blocked: ComputedRef<boolean>;
    read(): T;
    focus(path?: FieldPath): void;
    attach(api: Api): void;
    ready(api: Api): void;
    observe(value: T): void;
    registerComposite(api: Api, field: string, control: () => FieldControl | undefined): CompositePort;
    signal(): AbortSignal;
    reset(): void;
    submit(): Promise<boolean>;
    dispose(): void;
}
export declare function createSession<T extends object = Values>(initial: T, save: Save<T>, committed?: (values: T) => void, arrayKeys?: readonly ArrayKey[]): Session<T>;
export {};
