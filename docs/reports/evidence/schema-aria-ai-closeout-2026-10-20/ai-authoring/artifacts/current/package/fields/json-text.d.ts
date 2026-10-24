import { ParsedJsonText } from './types';
/** Parse data, never executable definitions. Empty text remains distinct from null. */
export declare function parseJsonText(text: string): ParsedJsonText;
