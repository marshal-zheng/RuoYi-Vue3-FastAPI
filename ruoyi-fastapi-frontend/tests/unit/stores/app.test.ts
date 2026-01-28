import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import useAppStore from '@/store/modules/app'
import Cookies from 'js-cookie'

// Mock Cookies
vi.mock('js-cookie', () => ({
  default: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn()
  }
}))

describe('App Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('State Initialization', () => {
    it('should initialize with default state when no cookies', () => {
      vi.mocked(Cookies.get).mockReturnValue(undefined)

      const store = useAppStore()

      expect(store.sidebar.opened).toBe(true)
      expect(store.sidebar.withoutAnimation).toBe(false)
      expect(store.sidebar.hide).toBe(false)
      expect(store.device).toBe('desktop')
      expect(store.size).toBe('default')
    })

    it('should initialize sidebar from cookie', () => {
      vi.mocked(Cookies.get).mockImplementation((key) => {
        if (key === 'sidebarStatus') return '0'
        return undefined
      })

      const store = useAppStore()

      expect(store.sidebar.opened).toBe(false)
    })

    it('should initialize size from cookie', () => {
      vi.mocked(Cookies.get).mockImplementation((key) => {
        if (key === 'size') return 'large'
        return undefined
      })

      const store = useAppStore()

      expect(store.size).toBe('large')
    })

    it('should handle sidebar opened state from cookie', () => {
      vi.mocked(Cookies.get).mockImplementation((key) => {
        if (key === 'sidebarStatus') return '1'
        return undefined
      })

      const store = useAppStore()

      expect(store.sidebar.opened).toBe(true)
    })
  })

  describe('toggleSideBar', () => {
    it('should toggle sidebar from opened to closed', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.toggleSideBar(false)

      expect(store.sidebar.opened).toBe(false)
      expect(store.sidebar.withoutAnimation).toBe(false)
      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })

    it('should toggle sidebar from closed to opened', () => {
      vi.mocked(Cookies.get).mockReturnValue('0')
      const store = useAppStore()

      store.toggleSideBar(false)

      expect(store.sidebar.opened).toBe(true)
      expect(store.sidebar.withoutAnimation).toBe(false)
      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 1)
    })

    it('should toggle without animation', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.toggleSideBar(true)

      expect(store.sidebar.withoutAnimation).toBe(true)
    })

    it('should not toggle when sidebar is hidden', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()
      store.sidebar.hide = true
      const initialState = store.sidebar.opened

      const result = store.toggleSideBar(false)

      expect(result).toBe(false)
      expect(store.sidebar.opened).toBe(initialState)
      expect(Cookies.set).not.toHaveBeenCalled()
    })

    it('should update cookie when toggling', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.toggleSideBar(false)

      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })
  })

  describe('closeSideBar', () => {
    it('should close sidebar', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.closeSideBar({ withoutAnimation: false })

      expect(store.sidebar.opened).toBe(false)
      expect(store.sidebar.withoutAnimation).toBe(false)
      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })

    it('should close sidebar without animation', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.closeSideBar({ withoutAnimation: true })

      expect(store.sidebar.opened).toBe(false)
      expect(store.sidebar.withoutAnimation).toBe(true)
      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })

    it('should update cookie when closing', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.closeSideBar({ withoutAnimation: false })

      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })

    it('should close already closed sidebar', () => {
      vi.mocked(Cookies.get).mockReturnValue('0')
      const store = useAppStore()

      store.closeSideBar({ withoutAnimation: false })

      expect(store.sidebar.opened).toBe(false)
      expect(Cookies.set).toHaveBeenCalledWith('sidebarStatus', 0)
    })
  })

  describe('toggleDevice', () => {
    it('should toggle to mobile device', () => {
      const store = useAppStore()

      store.toggleDevice('mobile')

      expect(store.device).toBe('mobile')
    })

    it('should toggle to desktop device', () => {
      const store = useAppStore()
      store.device = 'mobile'

      store.toggleDevice('desktop')

      expect(store.device).toBe('desktop')
    })

    it('should toggle to tablet device', () => {
      const store = useAppStore()

      store.toggleDevice('tablet')

      expect(store.device).toBe('tablet')
    })

    it('should handle multiple device changes', () => {
      const store = useAppStore()

      store.toggleDevice('mobile')
      expect(store.device).toBe('mobile')

      store.toggleDevice('tablet')
      expect(store.device).toBe('tablet')

      store.toggleDevice('desktop')
      expect(store.device).toBe('desktop')
    })
  })

  describe('setSize', () => {
    it('should set size to large', () => {
      const store = useAppStore()

      store.setSize('large')

      expect(store.size).toBe('large')
      expect(Cookies.set).toHaveBeenCalledWith('size', 'large')
    })

    it('should set size to default', () => {
      const store = useAppStore()
      store.size = 'large'

      store.setSize('default')

      expect(store.size).toBe('default')
      expect(Cookies.set).toHaveBeenCalledWith('size', 'default')
    })

    it('should set size to small', () => {
      const store = useAppStore()

      store.setSize('small')

      expect(store.size).toBe('small')
      expect(Cookies.set).toHaveBeenCalledWith('size', 'small')
    })

    it('should update cookie when setting size', () => {
      const store = useAppStore()

      store.setSize('large')

      expect(Cookies.set).toHaveBeenCalledWith('size', 'large')
    })

    it('should handle multiple size changes', () => {
      const store = useAppStore()

      store.setSize('small')
      expect(store.size).toBe('small')

      store.setSize('default')
      expect(store.size).toBe('default')

      store.setSize('large')
      expect(store.size).toBe('large')
    })
  })

  describe('toggleSideBarHide', () => {
    it('should hide sidebar', () => {
      const store = useAppStore()

      store.toggleSideBarHide(true)

      expect(store.sidebar.hide).toBe(true)
    })

    it('should show sidebar', () => {
      const store = useAppStore()
      store.sidebar.hide = true

      store.toggleSideBarHide(false)

      expect(store.sidebar.hide).toBe(false)
    })

    it('should toggle hide status multiple times', () => {
      const store = useAppStore()

      store.toggleSideBarHide(true)
      expect(store.sidebar.hide).toBe(true)

      store.toggleSideBarHide(false)
      expect(store.sidebar.hide).toBe(false)

      store.toggleSideBarHide(true)
      expect(store.sidebar.hide).toBe(true)
    })
  })

  describe('Integration Scenarios', () => {
    it('should handle mobile device with closed sidebar', () => {
      vi.mocked(Cookies.get).mockReturnValue('0')
      const store = useAppStore()

      store.toggleDevice('mobile')

      expect(store.device).toBe('mobile')
      expect(store.sidebar.opened).toBe(false)
    })

    it('should handle desktop device with opened sidebar', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.toggleDevice('desktop')

      expect(store.device).toBe('desktop')
      expect(store.sidebar.opened).toBe(true)
    })

    it('should handle size change with sidebar state', () => {
      vi.mocked(Cookies.get).mockReturnValue('1')
      const store = useAppStore()

      store.setSize('large')
      store.toggleSideBar(false)

      expect(store.size).toBe('large')
      expect(store.sidebar.opened).toBe(false)
    })

    it('should handle hidden sidebar toggle attempt', () => {
      const store = useAppStore()
      store.sidebar.hide = true
      store.sidebar.opened = true

      store.toggleSideBar(false)

      expect(store.sidebar.opened).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle undefined cookie values', () => {
      vi.mocked(Cookies.get).mockReturnValue(undefined)

      const store = useAppStore()

      expect(store.sidebar.opened).toBe(true)
      expect(store.size).toBe('default')
    })

    it('should handle invalid cookie values', () => {
      vi.mocked(Cookies.get).mockImplementation((key) => {
        if (key === 'sidebarStatus') return 'invalid'
        return undefined
      })

      const store = useAppStore()

      expect(store.sidebar.opened).toBe(false)
    })

    it('should handle empty string cookie values', () => {
      vi.mocked(Cookies.get).mockImplementation((key) => {
        if (key === 'size') return ''
        return undefined
      })

      const store = useAppStore()

      expect(store.size).toBe('')
    })
  })
})
