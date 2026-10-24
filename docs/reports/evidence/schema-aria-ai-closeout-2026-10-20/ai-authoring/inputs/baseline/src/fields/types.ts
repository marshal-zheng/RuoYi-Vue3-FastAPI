export interface FieldMessage {
  severity: 'error' | 'warning' | 'info'
  message: string
}
export interface FieldControlAttrs {
  id: string
  'aria-required'?: true
  'aria-invalid'?: true
  'aria-describedby'?: string
}
export interface NumberTextEdit {
  text: string
  badInput: boolean
}
export type ParsedNumberText =
  | { status: 'empty' }
  | { status: 'valid'; value: number }
  | { status: 'invalid' }
