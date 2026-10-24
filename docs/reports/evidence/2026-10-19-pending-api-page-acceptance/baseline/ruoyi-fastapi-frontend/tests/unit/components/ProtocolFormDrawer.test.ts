/**
 * Unit tests for ProtocolFormDrawer component
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProtocolFormDrawer from '@/components/business/Protocol/ProtocolFormDrawer.vue'

vi.mock('@/api/protocol/protocol', () => ({
  getProtocol: vi.fn()
}))

const renderSlotStub = {
  inheritAttrs: false,
  template: '<div><slot /></div>'
}

describe('ProtocolFormDrawer', () => {
  it('should render the protocol form inside the drawer shell', () => {
    const wrapper = mount(ProtocolFormDrawer, {
      global: {
        stubs: {
          ZxDrawer: renderSlotStub,
          ElForm: { inheritAttrs: false, template: '<form><slot /></form>' },
          ElFormItem: renderSlotStub,
          ZxInput: { inheritAttrs: false, template: '<input />' },
          ElTag: true,
          ElButton: true,
          ProtocolTypeSelector: { inheritAttrs: false, template: '<select />' },
          ImportFileDialog: true,
          EthernetProtocolTemplate: true,
          Protocol1553BTemplate: true,
          CANProtocolTemplate: true,
          RS422ProtocolTemplate: true
        }
      }
    })

    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.findAll('input').length).toBeGreaterThan(0)
    expect(wrapper.find('select').exists()).toBe(true)
  })
})
