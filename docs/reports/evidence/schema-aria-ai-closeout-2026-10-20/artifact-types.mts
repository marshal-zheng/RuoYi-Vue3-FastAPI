import { ZxInputNumber, zxInputNumberProps } from '@zxio/zxui/input-number'
import type {
  ZxInputNumberInstance,
  ZxInputNumberProps,
} from '@zxio/zxui/input-number'

type IsAny<T> = 0 extends 1 & T ? true : false
const propsAreTyped: IsAny<ZxInputNumberProps> = false
const internalAttributeChannelIsPrivate:
  'nativeAttrs' extends keyof ZxInputNumberProps ? false : true = true
const supported: ZxInputNumberProps = {
  modelValue: null,
  min: -1,
  max: 2,
  step: 0.5,
  precision: 1,
  readonly: false,
  controlsPosition: 'right',
  ariaLabel: 'Quantity',
  valueOnClear: 'min',
}
const valueContract = zxInputNumberProps.modelValue
declare const instance: ZxInputNumberInstance
instance.focus()
instance.blur()
// @ts-expect-error The numeric component does not accept string model values.
const invalidValue: ZxInputNumberProps = { modelValue: '1' }
// @ts-expect-error The pinned public contract does not promise future EP APIs.
const unsupportedFormatter: ZxInputNumberProps = { formatter: (value: number) => `${value}` }
void [
  ZxInputNumber,
  propsAreTyped,
  internalAttributeChannelIsPrivate,
  supported,
  valueContract,
  invalidValue,
  unsupportedFormatter,
]
