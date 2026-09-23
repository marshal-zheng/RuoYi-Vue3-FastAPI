/**
 * Unit tests for ProjectFormDialog component
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectFormDialog from '@/views/project/components/ProjectFormDialog.vue'

vi.mock('@/api/project/project', () => ({
  getProject: vi.fn(),
  addProject: vi.fn(),
  updateProject: vi.fn()
}))

const renderSlotStub = {
  inheritAttrs: false,
  template: '<div><slot /></div>'
}

describe('ProjectFormDialog', () => {
  it('should render the project form inside the dialog shell', () => {
    const wrapper = mount(ProjectFormDialog, {
      global: {
        stubs: {
          ZxDialog: renderSlotStub,
          ElForm: { inheritAttrs: false, template: '<form><slot /></form>' },
          ElFormItem: renderSlotStub,
          ZxInput: { inheritAttrs: false, template: '<input />' }
        }
      }
    })

    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.findAll('input').length).toBeGreaterThan(0)
  })
})
