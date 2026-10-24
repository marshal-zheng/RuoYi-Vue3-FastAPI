import { Api } from '@form-create/element-ui';
import { FieldMessage } from '../fields/types';
import { ArrayKey, FieldIssue, FieldPath } from './types';
export declare function createErrors(getApi: () => Api | undefined, getValues: () => object, arrayKeys: readonly ArrayKey[], isComposite: (api: Api, field: string) => boolean): {
    issues: import('vue').ShallowRef<readonly FieldIssue[], readonly FieldIssue[]>;
    formIssues: import('vue').ShallowRef<readonly FieldIssue[], readonly FieldIssue[]>;
    set: (next: readonly FieldIssue[], submitted?: object) => void;
    changed: () => void;
    refresh: () => void;
    messages: (api: Api, field: string) => readonly FieldMessage[];
    first: () => FieldPath | undefined;
    clear: () => void;
    dispose: () => void;
};
