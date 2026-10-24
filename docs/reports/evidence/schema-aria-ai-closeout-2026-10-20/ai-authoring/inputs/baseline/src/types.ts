import type { Component } from 'vue'

export type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json }
export type Values = Record<string, Json>

/** Trusted component registration; props is the JSON import allowlist. */
export interface Binding {
  component: Component
  props: readonly string[]
}
export type Bindings = Record<string, Binding>
