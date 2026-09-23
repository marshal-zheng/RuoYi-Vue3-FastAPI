import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import useSettingsStore from '@/store/modules/settings'
import { setZxThemePreference } from '@/theme/zx-theme-config'

// Mock dependencies
vi.mock('@/settings', () => ({
  default: {
    sideTheme: 'theme-dark',
    showSettings: true,
    topNav: false,
    topNavBorder: true,
    tagsView: true,
    fixedHeader: false,
    sidebarLogo: true,
    dynamicTitle: false
  }
}))

vi.mock('@/utils/dynamicTitle', () => ({
  useDynamicTitle: vi.fn()
}))

vi.mock('@vueuse/core', () => ({
  usePreferredDark: vi.fn(() => ({ value: false }))
}))

describe('Settings Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
    setZxThemePreference({ themeId: 'default', mode: 'light', density: 'default' })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('State Initialization', () => {
    it('should initialize with default settings', () => {
      const store = useSettingsStore()

      expect(store.title).toBe('')
      expect(store.theme).toBe('#0052D9')
      expect(store.sideTheme).toBe('theme-dark')
      expect(store.showSettings).toBe(true)
      expect(store.topNav).toBe(false)
      expect(store.tagsView).toBe(true)
      expect(store.fixedHeader).toBe(false)
      expect(store.sidebarLogo).toBe(true)
      expect(store.dynamicTitle).toBe(false)
      expect(store.topNavBorder).toBe(true)
      expect(store.isDark).toBe(false)
    })

    it('should load settings from localStorage', () => {
      const storedSettings = {
        theme: '#FF0000',
        sideTheme: 'theme-light',
        topNav: true,
        tagsView: false,
        fixedHeader: true,
        sidebarLogo: false,
        dynamicTitle: true,
        topNavBorder: false
      }
      localStorage.setItem('layout-setting', JSON.stringify(storedSettings))

      const store = useSettingsStore()

      expect(store.theme).toBe('#FF0000')
      expect(store.sideTheme).toBe('theme-light')
      expect(store.topNav).toBe(true)
      expect(store.tagsView).toBe(false)
      expect(store.fixedHeader).toBe(true)
      expect(store.sidebarLogo).toBe(false)
      expect(store.dynamicTitle).toBe(true)
      expect(store.topNavBorder).toBe(false)
    })

    it('should use default when localStorage is empty', () => {
      localStorage.removeItem('layout-setting')

      const store = useSettingsStore()

      expect(store.theme).toBe('#0052D9')
      expect(store.sideTheme).toBe('theme-dark')
    })

    it('should handle partial localStorage data', () => {
      const partialSettings = {
        theme: '#00FF00',
        topNav: true
      }
      localStorage.setItem('layout-setting', JSON.stringify(partialSettings))

      const store = useSettingsStore()

      expect(store.theme).toBe('#00FF00')
      expect(store.topNav).toBe(true)
      expect(store.sideTheme).toBe('theme-dark') // Should use default
    })
  })

  describe('changeSetting', () => {
    it('should change theme color', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#FF5722' })

      expect(store.theme).toBe('#FF5722')
    })

    it('should change side theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'sideTheme', value: 'theme-light' })

      expect(store.sideTheme).toBe('theme-light')
    })

    it('should change topNav setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'topNav', value: true })

      expect(store.topNav).toBe(true)
    })

    it('should change tagsView setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'tagsView', value: false })

      expect(store.tagsView).toBe(false)
    })

    it('should change fixedHeader setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'fixedHeader', value: true })

      expect(store.fixedHeader).toBe(true)
    })

    it('should change sidebarLogo setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'sidebarLogo', value: false })

      expect(store.sidebarLogo).toBe(false)
    })

    it('should change dynamicTitle setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'dynamicTitle', value: true })

      expect(store.dynamicTitle).toBe(true)
    })

    it('should change topNavBorder setting', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'topNavBorder', value: false })

      expect(store.topNavBorder).toBe(false)
    })

    it('should not change non-existent property', () => {
      const store = useSettingsStore()
      const initialState = { ...store.$state }

      store.changeSetting({ key: 'nonExistent', value: 'value' })

      expect(store.$state).toEqual(initialState)
    })

    it('should handle multiple setting changes', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#FF0000' })
      store.changeSetting({ key: 'topNav', value: true })
      store.changeSetting({ key: 'tagsView', value: false })

      expect(store.theme).toBe('#FF0000')
      expect(store.topNav).toBe(true)
      expect(store.tagsView).toBe(false)
    })
  })

  describe('setTitle', () => {
    it('should set page title', () => {
      const store = useSettingsStore()

      store.setTitle('系统管理')

      expect(store.title).toBe('系统管理')
    })

    it('should update title multiple times', () => {
      const store = useSettingsStore()

      store.setTitle('用户管理')
      expect(store.title).toBe('用户管理')

      store.setTitle('角色管理')
      expect(store.title).toBe('角色管理')
    })

    it('should handle empty title', () => {
      const store = useSettingsStore()

      store.setTitle('')

      expect(store.title).toBe('')
    })

    it('should handle special characters in title', () => {
      const store = useSettingsStore()

      store.setTitle('系统管理 - 用户列表')

      expect(store.title).toBe('系统管理 - 用户列表')
    })
  })

  describe('toggleTheme', () => {
    it('should toggle dark mode', () => {
      const store = useSettingsStore()
      const initialDark = store.isDark

      store.toggleTheme()

      expect(store.isDark).toBe(!initialDark)
    })

    it('should toggle dark mode multiple times', () => {
      const store = useSettingsStore()
      const initialDark = store.isDark

      store.toggleTheme()
      expect(store.isDark).toBe(!initialDark)

      store.toggleTheme()
      expect(store.isDark).toBe(initialDark)

      store.toggleTheme()
      expect(store.isDark).toBe(!initialDark)
    })
  })

  describe('Theme Presets', () => {
    it('should handle blue theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#0052D9' })

      expect(store.theme).toBe('#0052D9')
    })

    it('should handle red theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#F44336' })

      expect(store.theme).toBe('#F44336')
    })

    it('should handle green theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#4CAF50' })

      expect(store.theme).toBe('#4CAF50')
    })

    it('should handle custom hex color', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#ABCDEF' })

      expect(store.theme).toBe('#ABCDEF')
    })
  })

  describe('Side Theme Options', () => {
    it('should handle dark side theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'sideTheme', value: 'theme-dark' })

      expect(store.sideTheme).toBe('theme-dark')
    })

    it('should handle light side theme', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'sideTheme', value: 'theme-light' })

      expect(store.sideTheme).toBe('theme-light')
    })
  })

  describe('Layout Combinations', () => {
    it('should handle top navigation with tags view', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'topNav', value: true })
      store.changeSetting({ key: 'tagsView', value: true })

      expect(store.topNav).toBe(true)
      expect(store.tagsView).toBe(true)
    })

    it('should handle fixed header with sidebar logo', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'fixedHeader', value: true })
      store.changeSetting({ key: 'sidebarLogo', value: true })

      expect(store.fixedHeader).toBe(true)
      expect(store.sidebarLogo).toBe(true)
    })

    it('should handle dynamic title with top nav border', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'dynamicTitle', value: true })
      store.changeSetting({ key: 'topNavBorder', value: true })

      expect(store.dynamicTitle).toBe(true)
      expect(store.topNavBorder).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle invalid localStorage JSON', () => {
      localStorage.setItem('layout-setting', 'invalid json')

      const store = useSettingsStore()

      expect(store.theme).toBe('#0052D9')
    })

    it('should handle null values in settings', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: null })

      expect(store.theme).toBe(null)
    })

    it('should handle undefined values in settings', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: undefined })

      expect(store.theme).toBe(undefined)
    })

    it('should handle boolean toggle', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'showSettings', value: false })
      expect(store.showSettings).toBe(false)

      store.changeSetting({ key: 'showSettings', value: true })
      expect(store.showSettings).toBe(true)
    })
  })

  describe('Integration Scenarios', () => {
    it('should handle complete theme customization', () => {
      const store = useSettingsStore()

      store.changeSetting({ key: 'theme', value: '#FF5722' })
      store.changeSetting({ key: 'sideTheme', value: 'theme-light' })
      store.changeSetting({ key: 'topNav', value: true })
      store.changeSetting({ key: 'fixedHeader', value: true })
      store.changeSetting({ key: 'sidebarLogo', value: false })

      expect(store.theme).toBe('#FF5722')
      expect(store.sideTheme).toBe('theme-light')
      expect(store.topNav).toBe(true)
      expect(store.fixedHeader).toBe(true)
      expect(store.sidebarLogo).toBe(false)
    })

    it('should handle title change with theme toggle', () => {
      const store = useSettingsStore()

      store.setTitle('Dashboard')
      store.toggleTheme()

      expect(store.title).toBe('Dashboard')
      expect(store.isDark).toBe(true)
    })
  })
})
