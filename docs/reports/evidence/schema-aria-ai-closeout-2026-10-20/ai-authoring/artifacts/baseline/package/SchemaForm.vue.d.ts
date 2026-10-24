import { Bindings, Values } from './types';
import { BusinessContext, NativeRule, Save } from './form-create/types';
type __VLS_Props = {
    initial: Values;
    createRules: (context: BusinessContext) => NativeRule[];
    save: Save;
    bindings?: Bindings;
    labelPosition?: 'left' | 'right' | 'top';
    labelWidth?: string | number;
    disabled?: boolean;
};
declare function __VLS_template(): {
    attrs: Partial<{}>;
    slots: Readonly<{
        diagnostics(props: {
            status: string;
            dirty: boolean;
            pending: boolean;
        }): unknown;
    }> & {
        diagnostics(props: {
            status: string;
            dirty: boolean;
            pending: boolean;
        }): unknown;
    };
    refs: {};
    rootEl: any;
};
type __VLS_TemplateResult = ReturnType<typeof __VLS_template>;
declare const __VLS_component: import('vue').DefineComponent<__VLS_Props, {
    read: () => Values;
    reset: () => void;
    submit: () => Promise<boolean>;
    dirty: import('vue').ComputedRef<boolean>;
    pending: Readonly<import('vue').Ref<boolean, boolean>>;
    status: Readonly<import('vue').Ref<string, string>>;
}, {}, {}, {}, import('vue').ComponentOptionsMixin, import('vue').ComponentOptionsMixin, {} & {
    saved: (values: Values) => any;
}, string, import('vue').PublicProps, Readonly<__VLS_Props> & Readonly<{
    onSaved?: ((values: Values) => any) | undefined;
}>, {
    labelWidth: string | number;
    labelPosition: "left" | "right" | "top";
    bindings: Bindings;
}, {}, {}, {}, string, import('vue').ComponentProvideOptions, false, {}, any>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, __VLS_TemplateResult["slots"]>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
