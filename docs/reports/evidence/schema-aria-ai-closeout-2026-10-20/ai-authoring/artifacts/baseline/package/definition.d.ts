import { Bindings } from './types';
import { Definition } from './form-create/types';
export { copy, equal } from './json';
export declare function parseDefinition(text: string, bindings: Bindings): Definition;
