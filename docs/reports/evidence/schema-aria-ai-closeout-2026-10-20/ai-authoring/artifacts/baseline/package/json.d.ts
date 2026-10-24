import { Json } from './types';
export declare function record(value: unknown): value is Record<string, unknown>;
export declare function safeJson(value: unknown, path?: string, definition?: boolean, depth?: number): asserts value is Json;
export declare function copy<T>(value: T): T;
export declare function equal(left: unknown, right: unknown): boolean;
