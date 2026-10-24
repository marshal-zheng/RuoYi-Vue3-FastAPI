import { Api } from '@form-create/element-ui';
import { Component, PropType } from 'vue';
import { Session } from '../session';
/** A non-value adapter: the child still receives FormCreate's modelValue listener directly. */
export declare function compositeComponent(component: Component, session: Pick<Session, 'registerComposite'>, disabled: () => boolean): import('vue').Raw<import('vue').DefineComponent<import('vue').ExtractPropTypes<{
    formCreateInject: {
        type: PropType<{
            api: Api;
            field: string;
        }>;
        required: true;
    };
}>, () => import('vue').VNode<import('vue').RendererNode, import('vue').RendererElement, {
    [key: string]: any;
}>, {}, {}, {}, import('vue').ComponentOptionsMixin, import('vue').ComponentOptionsMixin, "edit-state"[], "edit-state", import('vue').PublicProps, Readonly<import('vue').ExtractPropTypes<{
    formCreateInject: {
        type: PropType<{
            api: Api;
            field: string;
        }>;
        required: true;
    };
}>> & Readonly<{
    "onEdit-state"?: ((...args: any[]) => any) | undefined;
}>, {}, {}, {}, {}, string, import('vue').ComponentProvideOptions, true, {}, any>>;
