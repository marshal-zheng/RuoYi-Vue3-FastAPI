import { computed, provide, ref, shallowRef, watch } from 'vue'
import {
  themePortalBindingKey,
  useRequiredThemePortalBinding,
} from '../../theme-provider'
import { useGlobalConfig } from '../../config-provider'
import { allocateZIndex } from '../../hooks/use-layer-governance'

import type { Ref } from 'vue'
import type { ZxDialogProps } from './props'

/** The portal lease follows content lifetime, not just modelValue. */
export function useDialogPortal(
  props: Pick<ZxDialogProps, 'appendTo' | 'destroyOnClose'>,
  visible: Ref<boolean>,
  attrs: Record<string, unknown>
) {
  const config = useGlobalConfig()
  const active = ref(visible.value)
  const leaving = ref(false)
  const result = useRequiredThemePortalBinding(
    computed(() => props.appendTo),
    active
  )
  provide(themePortalBindingKey, shallowRef(null))
  const binding = result.ok ? result.value : null
  const appendTo = computed(() => binding?.binding.value?.target)
  const ready = computed(() => Boolean(appendTo.value))
  const allocatedZIndex = ref<number>()
  const zIndex = () => {
    const explicit = Number(attrs.zIndex ?? attrs['z-index'])
    return Number.isFinite(explicit) ? explicit : allocatedZIndex.value
  }
  watch(
    visible,
    (value) => {
      leaving.value = !value && active.value
      if (value) {
        active.value = true
        allocatedZIndex.value = allocateZIndex(config.value?.zIndex)
      }
    },
    { immediate: true, flush: 'sync' }
  )
  watch(
    () => props.destroyOnClose,
    (value) => {
      if (value && !visible.value && !leaving.value) active.value = false
    }
  )
  const afterClosed = () => {
    if (visible.value) return
    leaving.value = false
    if (props.destroyOnClose) active.value = false
  }
  return { appendTo, ready, zIndex, afterClosed }
}
