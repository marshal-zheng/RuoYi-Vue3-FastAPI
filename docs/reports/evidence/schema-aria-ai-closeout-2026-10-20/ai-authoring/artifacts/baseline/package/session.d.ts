import { Api } from '@form-create/element-ui';
import { Values } from './types';
import { FieldIssue, Save } from './form-create/types';
export declare function createSession(initial: Values, save: Save, committed?: (values: Values) => void): {
    key: Readonly<import('vue').Ref<number, number>>;
    seed: Readonly<import('vue').ShallowRef<Values, Values>>;
    pending: Readonly<import('vue').Ref<boolean, boolean>>;
    status: Readonly<import('vue').Ref<string, string>>;
    issues: Readonly<import('vue').Ref<readonly {
        readonly field: string;
        readonly message: string;
    }[], readonly {
        readonly field: string;
        readonly message: string;
    }[]>>;
    formIssues: import('vue').ComputedRef<FieldIssue[]>;
    dirty: import('vue').ComputedRef<boolean>;
    read: () => Values;
    attach: (value: Api) => void;
    observe: (value: Values) => void;
    signal: () => AbortSignal;
    reset: () => void;
    submit: () => Promise<boolean>;
    dispose: () => void;
};
export type Session = ReturnType<typeof createSession>;
