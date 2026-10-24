import { Component } from 'vue';
export type Json = null | boolean | number | string | Json[] | {
    [key: string]: Json;
};
export type Values = Record<string, Json>;
/** Composite fields opt into messages, edit-state, validation and focus adaptation. */
export interface CompositeBinding {
    component: Component;
    composite: true;
}
export type Binding = Component | CompositeBinding;
export type Bindings = Record<string, Binding>;
