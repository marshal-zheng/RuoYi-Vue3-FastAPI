import { h, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ElementPlus from 'element-plus'
import Drawer from '../../drawer/src/drawer.vue'
import Dialog from '../../dialog/src/dialog.vue'
import Provider from '../../config-provider/src/config-provider'
import { mergeConfig } from '../../config-provider/src/merge'
import { createPortalTestOwner } from '../../theme-provider/__tests__/fixtures/portal-test-owner'
import {
  drawerDirectives,
  drawerStubs,
} from '../../drawer/__tests__/drawer-stub'
import { useDrawer } from '../../hooks/use-drawer'
import { useDialog } from '../../hooks/use-dialog'

const cleanups: (() => Promise<void>)[] = []
afterEach(async () => {
  for (const cleanup of cleanups.splice(0).reverse()) await cleanup()
})

for (const kind of ['drawer', 'dialog'] as const) {
  describe(`${kind} shared overlay layout`, () => {
    async function fixture(namespace = 'zx') {
      const owner = await createPortalTestOwner(
        `runtime:overlay-${kind}-${Math.random()}`
      )
      const common = ref<Record<string, unknown>>({})
      const near = ref<Record<string, unknown>>({})
      const local = ref<Record<string, unknown>>({})
      const wrapper = mount(
        () =>
          h(Provider, { namespace, overlayLayout: common.value }, () =>
            h(
              Provider,
              {
                namespace,
                [kind === 'drawer' ? 'zxDrawer' : 'zxDialog']: near.value,
              },
              () =>
                h(
                  kind === 'drawer' ? Drawer : Dialog,
                  {
                    modelValue: true,
                    title: 'Layout',
                    ...local.value,
                  },
                  {
                    default: () =>
                      h('div', { 'data-layout-content': '' }, 'Content'),
                  }
                )
            )
          ),
        {
          attachTo: document.body,
          global: {
            plugins: kind === 'drawer' ? [] : [ElementPlus],
            provide: owner.provide,
            stubs: kind === 'drawer' ? drawerStubs : { teleport: false },
            directives: kind === 'drawer' ? drawerDirectives : {},
          },
        }
      )
      cleanups.push(async () => {
        wrapper.unmount()
        await nextTick()
        await owner.dispose()
      })
      const selector = kind === 'drawer' ? '.el-drawer' : '.el-dialog'
      await vi.waitFor(() =>
        expect(document.querySelector(selector)).not.toBeNull()
      )
      const panel = () => document.querySelector<HTMLElement>(selector)!
      return { wrapper, panel, common, near, local }
    }

    it('inherits regional values, merges logical edges, and restores inherited values', async () => {
      const f = await fixture()
      f.common.value = {
        paddingInline: '2rem',
        bodyPadding: 'calc(1rem + 2px)',
        footerPadding: 0,
      }
      f.near.value = { bodyPadding: { blockEnd: '3rem' } }
      f.local.value = {
        bodyPadding: { inlineStart: 0 },
        headerPadding: '8px 12px',
      }
      await nextTick()
      const style = f.panel().style
      expect(style.getPropertyValue('--zx-overlay-local-padding-inline')).toBe(
        '2rem'
      )
      expect(style.getPropertyValue('--zx-overlay-local-body-padding')).toBe(
        'calc(1rem + 2px)'
      )
      expect(style.getPropertyValue('--zx-overlay-local-body-block-end')).toBe(
        '3rem'
      )
      expect(
        style.getPropertyValue('--zx-overlay-local-body-inline-start')
      ).toBe('0px')
      expect(style.getPropertyValue('--zx-overlay-local-footer-padding')).toBe(
        '0px'
      )
      expect(
        f.panel().classList.contains('zx-overlay-layout--body-inline-start')
      ).toBe(true)
      f.local.value = { bodyPadding: undefined }
      await nextTick()
      expect(
        style.getPropertyValue('--zx-overlay-local-body-inline-start')
      ).toBe('')
      expect(style.getPropertyValue('--zx-overlay-local-body-block-end')).toBe(
        '3rem'
      )
    })

    it('keeps zero padding separate from delegated scrolling and consumes new props', async () => {
      const f = await fixture()
      f.common.value = { bodyScroll: 'none' }
      f.local.value = { bodyPadding: 0, paddingInline: 0 }
      await nextTick()
      expect(
        f.panel().classList.contains('zx-overlay-layout--scroll-none')
      ).toBe(true)
      expect(
        f.panel().style.getPropertyValue('--zx-overlay-local-body-padding')
      ).toBe('0px')
      expect(f.panel().hasAttribute('bodyscroll')).toBe(false)
      expect(f.panel().hasAttribute('bodypadding')).toBe(false)
      expect(f.panel().hasAttribute('paddinginline')).toBe(false)
      f.local.value = {
        bodyScroll: 'auto',
        bodyPadding: 0,
      }
      await nextTick()
      expect(
        f.panel().classList.contains('zx-overlay-layout--scroll-none')
      ).toBe(false)
      expect(
        f.panel().style.getPropertyValue('--zx-overlay-local-body-padding')
      ).toBe('0px')
    })

    it('retains namespace-independent layout and divider classes', async () => {
      const f = await fixture('app')
      f.local.value = { divider: true }
      await nextTick()
      expect(f.panel().classList.contains(`app-${kind}-container`)).toBe(true)
      expect(f.panel().classList.contains('zx-overlay-layout')).toBe(true)
      expect(f.panel().classList.contains('zx-overlay-layout--divider')).toBe(
        true
      )
    })

    it('uses non-flow sentinels inside the content wrapper', async () => {
      const f = await fixture()
      const content = f.panel().querySelector('[data-zx-overlay-content]')!
      expect(content).not.toBeNull()
      expect(
        content.querySelectorAll('[data-zx-overlay-sentinel]')
      ).toHaveLength(2)
    })
  })
}

it('preserves Provider shorthand when a nested Provider overrides only one logical edge', () => {
  const merged = mergeConfig(
    {
      overlayLayout: {
        bodyPadding: 'var(--application-insets)',
        bodyScroll: 'none',
      },
    } as any,
    {
      overlayLayout: { bodyPadding: { inlineEnd: 0, blockStart: undefined } },
    } as any
  ) as any
  expect(merged.overlayLayout.bodyPadding).toEqual({
    all: 'var(--application-insets)',
    inlineEnd: 0,
  })
  expect(merged.overlayLayout.bodyScroll).toBe('none')
})

it('passes reactive layout options through both Hooks including restoration to undefined', async () => {
  for (const hook of [useDrawer, useDialog]) {
    const padding = ref<any>({ inlineStart: 0 })
    const scroll = ref<any>('none')
    const controller = hook({
      bodyPadding: padding,
      bodyScroll: scroll,
      paddingInline: '2rem',
    } as any)
    const props = () =>
      'drawerProps' in controller
        ? controller.drawerProps.value
        : controller.dialogProps.value
    expect(props()).toMatchObject({
      bodyPadding: { inlineStart: 0 },
      bodyScroll: 'none',
      paddingInline: '2rem',
    })
    controller.updateOptions({
      bodyPadding: undefined,
      bodyScroll: undefined,
    } as any)
    await nextTick()
    expect(props().bodyPadding).toBeUndefined()
    expect(props().bodyScroll).toBeUndefined()
  }
})

it('inherits empty padding values through nested Providers', () => {
  const parent = {
    overlayLayout: { bodyPadding: { all: '2rem', inlineEnd: 0 } },
  }
  const child = {
    overlayLayout: {
      bodyPadding: { all: ' ', inlineEnd: '', blockStart: undefined },
    },
  }
  expect(
    mergeConfig(parent as any, child as any).overlayLayout?.bodyPadding
  ).toEqual(parent.overlayLayout.bodyPadding)
  expect(
    mergeConfig(parent as any, { overlayLayout: { bodyPadding: '' } })
      .overlayLayout?.bodyPadding
  ).toEqual(parent.overlayLayout.bodyPadding)
})
