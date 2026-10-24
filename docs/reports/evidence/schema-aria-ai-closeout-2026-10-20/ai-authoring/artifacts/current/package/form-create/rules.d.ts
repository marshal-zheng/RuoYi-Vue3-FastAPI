import { SchemaRule } from './types';
/** Isolate writable rules; live code configuration uses the native evaluator. */
export declare function copySessionRules(rules: SchemaRule[]): SchemaRule[];
