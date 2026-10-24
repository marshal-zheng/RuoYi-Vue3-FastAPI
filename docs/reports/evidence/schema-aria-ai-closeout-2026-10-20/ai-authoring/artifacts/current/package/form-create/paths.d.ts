import { Api } from '@form-create/element-ui';
import { ArrayKey, FieldPath } from './types';
type Identity = {
    index: number;
    key?: string;
    value?: string | number;
    snapshot?: unknown;
    unsafe?: true;
};
export type AnchoredPath = readonly (string | Identity)[];
export declare function validPath(path: unknown): path is FieldPath;
export declare function readPath(value: unknown, path: FieldPath): unknown;
export declare function anchorPath(path: FieldPath, submitted: unknown, keys: readonly ArrayKey[]): AnchoredPath;
export declare function resolvePath(anchor: AnchoredPath, current: unknown): {
    path?: FieldPath;
    deleted?: true;
};
export interface FieldLocation {
    api: Api;
    field: string;
    relative: FieldPath;
}
/** Public native APIs only; a remainder may be handled by an opted-in composite. */
export declare function locateField(api: Api | undefined, path: FieldPath): FieldLocation | undefined;
export {};
