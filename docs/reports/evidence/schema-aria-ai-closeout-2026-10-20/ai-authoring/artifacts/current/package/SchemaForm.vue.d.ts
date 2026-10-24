import { Bindings, Values } from './types';
import { ArrayKey, BusinessContext, FormPhase, Save, SchemaRule } from './form-create/types';
declare const _default: <T extends object = Values>(__VLS_props: NonNullable<Awaited<typeof __VLS_setup>>["props"], __VLS_ctx?: __VLS_PrettifyLocal<Pick<NonNullable<Awaited<typeof __VLS_setup>>, "attrs" | "emit" | "slots">>, __VLS_expose?: NonNullable<Awaited<typeof __VLS_setup>>["expose"], __VLS_setup?: Promise<{
    props: __VLS_PrettifyLocal<Pick<Partial<{}> & Omit<{
        readonly onSaved?: ((values: T) => any) | undefined;
    } & import('vue').VNodeProps & import('vue').AllowedComponentProps & import('vue').ComponentCustomProps, never>, "onSaved"> & {
        initial: T;
        createRules: (context: BusinessContext<T>) => SchemaRule[];
        save: Save<T>;
        bindings?: Bindings;
        labelPosition?: "left" | "right" | "top";
        labelWidth?: string | number;
        disabled?: boolean;
        arrayKeys?: readonly ArrayKey[];
        columns?: 1 | 2 | 3;
    } & Partial<{}>> & import('vue').PublicProps;
    expose(exposed: import('vue').ShallowUnwrapRef<{
        read: () => T;
        reset: () => void;
        submit: () => Promise<boolean>;
        focus: (path?: import('./fields/types').FieldPath) => void;
        dirty: import('vue').ComputedRef<boolean>;
        phase: Readonly<import('vue').Ref<FormPhase, FormPhase>>;
        blocked: import('vue').ComputedRef<boolean>;
        fieldPending: import('vue').ComputedRef<boolean>;
        pending: Readonly<import('vue').Ref<boolean, boolean>>;
        status: Readonly<import('vue').Ref<string, string>>;
    }>): void;
    attrs: any;
    slots: Readonly<{
        diagnostics(props: {
            status: string;
            dirty: boolean;
            pending: boolean;
            fieldPending: boolean;
            blocked: boolean;
            phase: FormPhase;
        }): unknown;
    }> & {
        diagnostics(props: {
            status: string;
            dirty: boolean;
            pending: boolean;
            fieldPending: boolean;
            blocked: boolean;
            phase: FormPhase;
        }): unknown;
    };
    emit: (e: "saved", values: T) => void;
}>) => import('vue').VNode<import('vue').RendererNode, import('vue').RendererElement, {
    [key: string]: any;
}> & {
    __ctx?: Awaited<typeof __VLS_setup>;
};
export default _default;
type __VLS_PrettifyLocal<T> = {
    [K in keyof T]: T[K];
} & {};
