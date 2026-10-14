import { createApp } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createDocsRouteFeatures } from './route-features'

const { install } = vi.hoisted(() => ({ install: vi.fn() }))
vi.mock('./drive-features', () => ({ installDocsDriveFeatures: install }))

beforeEach(() => install.mockReset())

describe('docs route feature preparation', () => {
  it('keeps ordinary pages and similar path prefixes free of Drive setup', async () => {
    const prepare = createDocsRouteFeatures(createApp({}))
    for (const path of [
      '/',
      '/component/select',
      '/component/driver',
      '/guide/theme-showcase',
    ])
      await prepare(path)
    expect(install).not.toHaveBeenCalled()
  })

  it('covers direct, localized, html and query/hash navigation once per app', async () => {
    const app = createApp({})
    const prepare = createDocsRouteFeatures(app)
    for (const path of [
      '/en-US/guide/theme-lab.html',
      '/component/drive',
      'https://docs.local/en-US/component/drive?view=list#demo',
      '/guide/theme-lab/',
    ])
      await prepare(path)
    expect(install).toHaveBeenCalledOnce()
    expect(install).toHaveBeenCalledWith(app)
  })

  it('waits for concurrent preparation before rendering the destination', async () => {
    let finish!: () => void
    install.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve
        })
    )
    const prepare = createDocsRouteFeatures(createApp({}))
    let completed = 0
    const first = prepare('/component/drive').then(() => completed++)
    const second = prepare('/guide/theme-lab').then(() => completed++)
    await vi.waitFor(() => expect(install).toHaveBeenCalledOnce())
    expect(completed).toBe(0)
    finish()
    await Promise.all([first, second])
    expect(completed).toBe(2)
  })

  it('retries failed preparation and isolates separate SSR apps', async () => {
    install.mockRejectedValueOnce(new Error('load failed'))
    const prepare = createDocsRouteFeatures(createApp({}))
    await expect(prepare('/component/drive')).rejects.toThrow('load failed')
    await prepare('/component/drive')
    await createDocsRouteFeatures(createApp({}))('/guide/theme-lab')
    expect(install).toHaveBeenCalledTimes(3)
  })

  it('cancels a slow feature navigation overtaken by an ordinary page', async () => {
    let finish!: () => void
    install.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve
        })
    )
    const prepare = createDocsRouteFeatures(createApp({}))
    const slow = prepare('/component/drive')
    await vi.waitFor(() => expect(install).toHaveBeenCalledOnce())
    await expect(prepare('/component/select')).resolves.toBeUndefined()
    finish()
    await expect(slow).resolves.toBe(false)
    await expect(prepare('/guide/theme-lab')).resolves.toBeUndefined()
  })
})
