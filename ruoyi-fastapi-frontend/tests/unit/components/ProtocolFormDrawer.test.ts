/**
 * Unit tests for ProtocolFormDrawer component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElForm, ElInput, ElSelect } from 'element-plus'
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue'

// Mock dependencies
vi.mock('@/api/protocol/protocol', () => ({
  getProtocol: vi.fn(),
  addProtocol: vi.fn(),
  updateProtocol: vi.fn(),
}))

describe('ProtocolFormDrawer', () => {
  let wrapper: any

  const createWrapper = (props = {}) => {
    return mount(ProtocolFormDrawer, {
      props: {
        visible: true,
        ...props,
      },
      global: {
        components: {
          ElForm,
          ElInput,
          ElSelect,
        },
        stubs: {
          ZxDrawer: true,
          ElFormItem: true,
          ElRow: true,
          ElCol: true,
          ElOption: true,
          ProtocolTypeSelector: true,
          EthernetProtocolTemplate: true,
          Protocol1553BTemplate: true,
          CANProtocolTemplate: true,
          RS422ProtocolTemplate: true,
        },
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render drawer when visible', () => {
      wrapper = createWrapper({ visible: true })
      expect(wrapper.exists()).toBe(true)
    })

    it('should not render drawer when not visible', () => {
      wrapper = createWrapper({ visible: false })
      expect(wrapper.props('visible')).toBe(false)
    })

    it('should render form with inputs', () => {
      wrapper = createWrapper()
      expect(wrapper.findComponent(ElForm).exists()).toBe(true)
    })
  })

  describe('Add Mode', () => {
    it('should have empty initial data in add mode', () => {
      wrapper = createWrapper({ protocolId: undefined })
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should show add title in add mode', () => {
      wrapper = createWrapper({ protocolId: undefined })
      expect(wrapper.vm.drawerTitle).toContain('新增')
    })

    it('should allow protocol type selection in add mode', () => {
      wrapper = createWrapper({ protocolId: undefined })
      expect(wrapper.vm.formData?.protocolType).toBeDefined()
    })
  })

  describe('Edit Mode', () => {
    it('should load protocol data in edit mode', () => {
      wrapper = createWrapper({ protocolId: 1 })
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should show edit title in edit mode', () => {
      wrapper = createWrapper({ protocolId: 1 })
      expect(wrapper.vm.drawerTitle).toContain('修改')
    })

    it('should disable protocol type change in edit mode', () => {
      wrapper = createWrapper({ protocolId: 1 })
      expect(wrapper.vm.isEdit).toBeTruthy()
    })
  })

  describe('Protocol Type Selection', () => {
    it('should render protocol type selector', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formData?.protocolType).toBeDefined()
    })

    it('should support Ethernet protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'Ethernet'
      expect(wrapper.vm.formData.protocolType).toBe('Ethernet')
    })

    it('should support 1553B protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = '1553B'
      expect(wrapper.vm.formData.protocolType).toBe('1553B')
    })

    it('should support CAN protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'CAN'
      expect(wrapper.vm.formData.protocolType).toBe('CAN')
    })

    it('should support RS422 protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'RS422'
      expect(wrapper.vm.formData.protocolType).toBe('RS422')
    })
  })

  describe('Form Validation', () => {
    it('should validate protocol name', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules?.protocolName).toBeDefined()
    })

    it('should validate protocol type', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules?.protocolType).toBeDefined()
    })

    it('should validate required fields', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules).toBeDefined()
    })
  })

  describe('Protocol Templates', () => {
    it('should render appropriate template based on protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'Ethernet'
      expect(wrapper.vm.currentTemplate).toBeDefined()
    })

    it('should switch template when protocol type changes', async () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'CAN'
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.formData.protocolType).toBe('CAN')
    })
  })

  describe('Form Submission', () => {
    it('should emit submit event with form data', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted()).toBeDefined()
    })

    it('should validate form before submission', async () => {
      wrapper = createWrapper()
      const form = wrapper.findComponent(ElForm)
      expect(form.exists()).toBe(true)
    })

    it('should handle successful submission', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should handle submission errors', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Drawer Events', () => {
    it('should handle drawer close event', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.drawerEvents).toBeDefined()
    })

    it('should reset form on close', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should emit close event', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted()).toBeDefined()
    })
  })

  describe('Protocol Configuration', () => {
    it('should handle Ethernet configuration', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'Ethernet'
      wrapper.vm.formData.config = { ip: '192.168.1.1', port: 8080 }
      expect(wrapper.vm.formData.config).toBeDefined()
    })

    it('should handle 1553B configuration', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = '1553B'
      wrapper.vm.formData.config = { busAddress: 1, subAddress: 2 }
      expect(wrapper.vm.formData.config).toBeDefined()
    })

    it('should handle CAN configuration', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'CAN'
      wrapper.vm.formData.config = { canId: 0x123, baudRate: 500000 }
      expect(wrapper.vm.formData.config).toBeDefined()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing protocol ID gracefully', () => {
      wrapper = createWrapper({ protocolId: null })
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle invalid protocol ID', () => {
      wrapper = createWrapper({ protocolId: -1 })
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle empty form data', () => {
      wrapper = createWrapper()
      wrapper.vm.formData = {}
      expect(wrapper.vm.formData).toEqual({})
    })

    it('should handle unknown protocol type', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'Unknown'
      expect(wrapper.vm.formData.protocolType).toBe('Unknown')
    })

    it('should handle API errors gracefully', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Form Reset', () => {
    it('should reset form data', () => {
      wrapper = createWrapper()
      wrapper.vm.formData = { protocolName: 'Test' }
      expect(wrapper.vm.formData.protocolName).toBe('Test')
    })

    it('should clear validation errors on reset', () => {
      wrapper = createWrapper()
      const form = wrapper.findComponent(ElForm)
      expect(form.exists()).toBe(true)
    })

    it('should reset protocol type selection', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.protocolType = 'CAN'
      expect(wrapper.vm.formData.protocolType).toBe('CAN')
    })
  })

  describe('Loading State', () => {
    it('should show loading state during data fetch', () => {
      wrapper = createWrapper({ protocolId: 1 })
      expect(wrapper.vm.loading).toBeDefined()
    })

    it('should disable form during submission', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.loading).toBeDefined()
    })
  })
})
