import { ref } from 'vue'
import { mergeConfig, useDrawer, useDialog } from '@zxio/zxui'
import type { ZxConfigProviderContext, ZxOverlayPadding, ZxOverlayBodyScroll } from '@zxio/zxui'

const parent: Partial<ZxConfigProviderContext> = { overlayLayout: { bodyPadding: 'var(--application-insets)', bodyScroll: 'none' } }
const child: Partial<ZxConfigProviderContext> = { overlayLayout: { bodyPadding: { inlineEnd: 0, blockStart: undefined } } }
mergeConfig(parent, child)
const padding = ref<ZxOverlayPadding | undefined>({ inlineStart: 0 })
const scroll = ref<ZxOverlayBodyScroll | undefined>('none')
const drawer = useDrawer({ bodyPadding: padding, bodyScroll: scroll, paddingInline: '2rem' })
const dialog = useDialog({ bodyPadding: padding, bodyScroll: scroll, paddingInline: '2rem' })
drawer.updateOptions({ bodyPadding: undefined, bodyScroll: undefined })
dialog.updateOptions({ bodyPadding: undefined, bodyScroll: undefined })
// @ts-expect-error legacy option is removed from the public hook.
useDrawer({ noContentPadding: true })
// @ts-expect-error legacy option is removed from the public hook.
useDialog({ noContentPadding: true })
// @ts-expect-error scroll owners are finite and cannot accept arbitrary strings.
useDrawer({ bodyScroll: 'legacy' })
// @ts-expect-error scroll owners are finite and cannot accept arbitrary strings.
useDialog({ bodyScroll: 'legacy' })
// @ts-expect-error physical edge spelling does not belong to the logical contract.
mergeConfig({ overlayLayout: { bodyPadding: { left: 24 } } }, {})
