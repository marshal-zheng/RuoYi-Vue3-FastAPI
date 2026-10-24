import { JsonTextEdit } from './types';
type __VLS_Props = {
    text: string;
    disabled?: boolean;
    readonly?: boolean;
};
declare const _default: import('vue').DefineComponent<__VLS_Props, {
    focus: () => void | undefined;
}, {}, {}, {}, import('vue').ComponentOptionsMixin, import('vue').ComponentOptionsMixin, {} & {
    edit: (edit: JsonTextEdit) => any;
}, string, import('vue').PublicProps, Readonly<__VLS_Props> & Readonly<{
    onEdit?: ((edit: JsonTextEdit) => any) | undefined;
}>, {}, {}, {}, {}, string, import('vue').ComponentProvideOptions, false, {}, any>;
export default _default;
