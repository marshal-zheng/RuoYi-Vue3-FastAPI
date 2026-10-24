import { h, nextTick, ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { expect, it, vi } from 'vitest'
import ElementPlus, { ElInputNumber } from 'element-plus'
import {
  createDirectionalNavigation,
  directionalNavigationKey,
} from '@zxio/hooks'
import ZxDialog from '../src/dialog.vue'
import ZxDrawer from '../../drawer/src/drawer.vue'
import { createPortalTestOwner } from '../../theme-provider/__tests__/fixtures/portal-test-owner'

import type { Component } from 'vue'

const press = (element: HTMLElement, key: string, repeat = false) => {
  const event = new KeyboardEvent('keydown', {
    key,
    repeat,
    bubbles: true,
    cancelable: true,
  })
  element.dispatchEvent(event)
  element.dispatchEvent(
    new KeyboardEvent('keyup', { key, bubbles: true, cancelable: true })
  )
  return event
}

it.each([
  ['Dialog', ZxDialog, '.el-dialog'],
  ['Drawer', ZxDrawer, '.el-drawer'],
] as const)(
  '%s owns modal navigation and uses its existing guarded close',
  async (name: string, component: Component, selector: string) => {
    const rects = vi
      .spyOn(HTMLElement.prototype, 'getClientRects')
      .mockReturnValue([{ width: 100, height: 30 }] as unknown as DOMRectList)
    const portal = await createPortalTestOwner(
      `runtime:navigation-${name.toLowerCase()}`
    )
    const navigation = createDirectionalNavigation({ enabled: true })
    const page = document.body.appendChild(document.createElement('section'))
    const opener = page.appendChild(document.createElement('button'))
    navigation.register({
      id: 'page',
      root: page,
      items: () => [{ id: 'opener', element: () => opener }],
    })

    await navigation.focus('page')
    let allowClose = false
    const guard = vi.fn(() => allowClose)
    const wrapper = mount(component, {
      props: {
        modelValue: true,
        title: name,
        showFullScreen: false,
        handleBeforeCancel: guard,
      },
      slots: {
        default: () => [
          h('input', {
            'data-combobox': '',
            role: 'combobox',
            'aria-expanded': 'false',
          }),
          h('button', { 'data-body-action': '' }, 'Action'),
        ],
      },
      global: {
        provide: {
          ...portal.provide,
          [directionalNavigationKey as symbol]: navigation,
        },
        plugins: [ElementPlus],
        stubs: { teleport: false },
      },
    })
    try {
      await vi.waitFor(() =>
        expect(
          document.querySelector(`${selector}[data-zx-navigation-group]`)
        ).not.toBeNull()
      )
      const panel = document.querySelector<HTMLElement>(selector)!
      const group = panel.dataset.zxNavigationGroup!
      expect(await navigation.focus('page')).toBe(false)
      const combo = panel.querySelector<HTMLInputElement>('[data-combobox]')!
      combo.focus()
      expect(press(combo, 'ArrowDown').defaultPrevented).toBe(false)
      const action =
        panel.querySelector<HTMLButtonElement>('[data-body-action]')!
      const click = vi.fn()
      action.addEventListener('click', click)
      action.focus()
      expect(press(action, 'Enter').defaultPrevented).toBe(true)
      press(action, 'Enter', true)
      expect(click).toHaveBeenCalledOnce()
      expect(press(action, 'Escape').defaultPrevented).toBe(true)
      await flushPromises()
      expect(guard).toHaveBeenCalledOnce()
      expect(wrapper.emitted('update:modelValue')).toBeUndefined()
      expect(await navigation.focus('page')).toBe(false)
      action.focus()
      allowClose = true
      press(action, 'Escape')
      await flushPromises()
      await nextTick()
      expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([false])
      await wrapper.setProps({ modelValue: false })
      expect(await navigation.focus(group)).toBe(false)
      expect(document.activeElement).toBe(opener)
      expect(await navigation.focus('page')).toBe(true)
    } finally {
      wrapper.unmount()
      navigation.dispose()
      page.remove()
      await portal.dispose()
      rects.mockRestore()
    }
  }
)

it('restricts a nested modal to the top layer and restores the parent action before the page', async () => {
  const rects = vi
    .spyOn(HTMLElement.prototype, 'getClientRects')
    .mockReturnValue([{ width: 100, height: 30 }] as unknown as DOMRectList)
  const portal = await createPortalTestOwner('runtime:nested-navigation')
  const navigation = createDirectionalNavigation({ enabled: true })
  const page = document.body.appendChild(document.createElement('section'))
  const opener = page.appendChild(document.createElement('button'))
  navigation.register({
    id: 'page',
    root: page,
    items: () => [{ id: 'open', element: () => opener }],
  })
  await navigation.focus('page')
  const global = {
    provide: {
      ...portal.provide,
      [directionalNavigationKey as symbol]: navigation,
    },
    plugins: [ElementPlus],
    stubs: { teleport: false },
  }
  const parent = mount(ZxDialog, {
    props: { modelValue: true, title: 'Parent' },
    slots: {
      default: () => h('button', { 'data-parent-action': '' }, 'Child'),
    },
    global,
  })
  let child: ReturnType<typeof mount> | null = null
  try {
    await vi.waitFor(() =>
      expect(
        document.querySelector('.el-dialog[data-zx-navigation-group]')
      ).not.toBeNull()
    )
    const parentPanel = document.querySelector<HTMLElement>('.el-dialog')!
    const parentGroup = parentPanel.dataset.zxNavigationGroup!
    const parentAction = parentPanel.querySelector<HTMLButtonElement>(
      '[data-parent-action]'
    )!
    parentAction.focus()
    child = mount(ZxDrawer, {
      props: { modelValue: true, title: 'Child' },
      slots: {
        default: () => h('button', { 'data-child-action': '' }, 'Close'),
      },
      global,
    })
    await vi.waitFor(() =>
      expect(
        document.querySelector('.el-drawer[data-zx-navigation-group]')
      ).not.toBeNull()
    )
    expect(await navigation.focus(parentGroup)).toBe(false)
    expect(await navigation.focus('page')).toBe(false)
    const childAction = document.querySelector<HTMLButtonElement>(
      '[data-child-action]'
    )!
    childAction.focus()
    press(childAction, 'Escape')
    await flushPromises()
    await child.setProps({ modelValue: false })
    expect(document.activeElement).toBe(parentAction)
    expect(await navigation.focus('page')).toBe(false)
    expect(await navigation.focus(parentGroup)).toBe(true)
    parentAction.focus()
    press(parentAction, 'Escape')
    await flushPromises()
    await parent.setProps({ modelValue: false })
    expect(document.activeElement).toBe(opener)
    expect(await navigation.focus('page')).toBe(true)
  } finally {
    child?.unmount()
    parent.unmount()
    navigation.dispose()
    page.remove()
    await portal.dispose()
    rects.mockRestore()
  }
})

it.each([
  {
    name: 'Dialog',
    component: ZxDialog,
    selector: '.el-dialog',
    enabled: false,
  },
  {
    name: 'Dialog',
    component: ZxDialog,
    selector: '.el-dialog',
    enabled: true,
  },
  {
    name: 'Drawer',
    component: ZxDrawer,
    selector: '.el-drawer',
    enabled: false,
  },
  {
    name: 'Drawer',
    component: ZxDrawer,
    selector: '.el-drawer',
    enabled: true,
  },
] as const)(
  '$name native number Enter increments without submitting, directional=$enabled',
  async ({
    name,
    component,
    selector,
    enabled,
  }: {
    name: string
    component: Component
    selector: string
    enabled: boolean
  }) => {
    const rects = vi
      .spyOn(HTMLElement.prototype, 'getClientRects')
      .mockReturnValue([{ width: 100, height: 30 }] as unknown as DOMRectList)
    const portal = await createPortalTestOwner(
      `runtime:native-number-${name.toLowerCase()}-${enabled}`
    )
    const navigation = createDirectionalNavigation({ enabled })
    const value = ref(1)
    const confirm = vi.fn(() => false)
    const wrapper = mount(component, {
      props: { modelValue: true, title: name, showFullScreen: false, confirm },
      slots: {
        default: () =>
          h(ElInputNumber, {
            modelValue: value.value,
            min: 0,
            max: 3,
            'onUpdate:modelValue': (next: number | undefined) => {
              value.value = next ?? 0
            },
          }),
      },
      global: {
        provide: {
          ...portal.provide,
          [directionalNavigationKey as symbol]: navigation,
        },
        plugins: [ElementPlus],
        stubs: { teleport: false },
      },
    })
    try {
      await vi.waitFor(() =>
        expect(
          document.querySelector(`${selector}[data-zx-navigation-group]`)
        ).not.toBeNull()
      )
      const panel = document.querySelector<HTMLElement>(selector)!
      const increase = panel.querySelector<HTMLElement>(
        '.el-input-number__increase'
      )!
      if (enabled) {
        // Native EP stepper spans intentionally have tabIndex=-1. Explicit
        // widget items opt into them; ordinary modal discovery still honors Tab.
        const root = increase.closest<HTMLElement>('.el-input-number')!
        navigation.register({
          id: 'number-controls',
          root,
          items: () => [
            { id: 'increase', element: () => increase },
            {
              id: 'input',
              element: () => root.querySelector<HTMLInputElement>('input'),
            },
          ],
        })
        expect(await navigation.focus('number-controls', 'increase')).toBe(true)
      } else increase.focus()
      press(increase, 'Enter')
      await flushPromises()
      expect(value.value).toBe(2)
      expect(confirm).not.toHaveBeenCalled()
      press(increase, 'Enter', true)
      await flushPromises()
      expect(value.value).toBe(enabled ? 2 : 3)
      if (enabled) {
        press(increase, 'ArrowDown')
        await flushPromises()
        expect(document.activeElement?.tagName).toBe('INPUT')
      }
    } finally {
      wrapper.unmount()
      navigation.dispose()
      await portal.dispose()
      rects.mockRestore()
    }
  }
)

it('leaves the default drawer resize entry for its form and admits native resizing explicitly', async () => {
  const rects = vi
    .spyOn(HTMLElement.prototype, 'getClientRects')
    .mockReturnValue([{ width: 100, height: 30 }] as unknown as DOMRectList)
  const portal = await createPortalTestOwner('runtime:drawer-resize-entry')
  const navigation = createDirectionalNavigation({ enabled: true })
  const guard = vi.fn(() => false)
  const wrapper = mount(ZxDrawer, {
    props: {
      modelValue: true,
      showFullScreen: false,
      handleBeforeCancel: guard,
    },
    slots: { default: () => h('input', { 'data-form-entry': '' }) },
    global: {
      provide: {
        ...portal.provide,
        [directionalNavigationKey as symbol]: navigation,
      },
      plugins: [ElementPlus],
      stubs: { teleport: false },
    },
  })
  try {
    await vi.waitFor(() =>
      expect(
        document.querySelector('.el-drawer[data-zx-navigation-group]')
      ).not.toBeNull()
    )
    const panel = document.querySelector<HTMLElement>('.el-drawer')!
    // jsdom has no layout: this seam supplies only the native resize input.
    Object.defineProperty(panel, 'offsetWidth', { value: 560 })
    const handle = panel.querySelector<HTMLElement>('[role=separator]')!
    const input = panel.querySelector<HTMLInputElement>('[data-form-entry]')!
    await flushPromises()
    await nextTick()
    expect(await navigation.focus(panel.dataset.zxNavigationGroup!)).toBe(true)
    const visited = new Set<Element | null>()
    for (let step = 0; step < 8 && document.activeElement !== input; step++) {
      visited.add(document.activeElement)
      press(document.activeElement as HTMLElement, 'ArrowDown')
      await flushPromises()
    }
    expect(visited.has(handle)).toBe(true)
    expect(document.activeElement).toBe(input)
    expect(wrapper.emitted('resize')).toBeUndefined()
    press(input, 'ArrowUp')
    await flushPromises()
    expect(document.activeElement).toBe(handle)
    expect(navigation.isEditing(handle)).toBe(false)
    press(handle, 'Enter')
    expect(navigation.isEditing(handle)).toBe(true)
    expect(wrapper.emitted('resize')).toBeUndefined()
    expect(wrapper.emitted('ok')).toBeUndefined()
    press(handle, 'ArrowLeft')
    await flushPromises()
    expect(wrapper.emitted('resize')?.at(-1)?.[0]).toMatchObject({
      source: 'keyboard',
    })
    input.focus()
    handle.focus()
    expect(navigation.isEditing(handle)).toBe(true)
    press(handle, 'ArrowLeft')
    await flushPromises()
    expect(wrapper.emitted('resize')?.at(-1)?.[0]).toMatchObject({
      source: 'keyboard',
    })
    // Ordinary focus admitted native resize; region focus selects without entering it.
    press(handle, 'Escape')
    await flushPromises()
    expect(guard).toHaveBeenCalledOnce()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  } finally {
    wrapper.unmount()
    navigation.dispose()
    await portal.dispose()
    rects.mockRestore()
  }
})
