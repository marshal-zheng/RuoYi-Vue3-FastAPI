import { ParsedNumberText } from './types';
/** Parse a complete decimal literal; never silently accept a partial prefix. */
export declare function parseNumberText(text: string): ParsedNumberText;
