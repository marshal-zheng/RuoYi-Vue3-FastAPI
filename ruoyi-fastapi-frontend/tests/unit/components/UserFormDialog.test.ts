/**
 * Unit tests for UserFormDialog component
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UserFormDialog from '@/views/system/user/components/UserFormDialog.vue'

vi.mock('@/api/system/user', () => ({
  getUser: vi.fn(),
  addUser: vi.fn(),
  updateUser: vi.fn()
}))

const renderSlotStub = {
  inheritAttrs: false,
  template: '<div><slot /></div>'
}

const formStub = {
  name: 'ElForm',
  inheritAttrs: false,
  template: '<form><slot /></form>'
}

describe('UserFormDialog', () => {
  it('should render the user form inside the dialog shell', () => {
    const wrapper = mount(UserFormDialog, {
      props: {
        deptOptions: [{ id: 1, label: '研发部' }],
        statusOptions: [{ value: '0', label: '正常' }],
        sexOptions: [{ value: '0', label: '男' }]
      },
      global: {
        stubs: {
          ZxDialog: renderSlotStub,
          ElForm: formStub,
          ElFormItem: renderSlotStub,
          ElRow: renderSlotStub,
          ElCol: renderSlotStub,
          ElInput: { inheritAttrs: false, template: '<input />' },
          ElTreeSelect: { inheritAttrs: false, template: '<select />' },
          ElSelect: renderSlotStub,
          ElOption: true,
          ElRadioGroup: renderSlotStub,
          ElRadio: renderSlotStub
        }
      }
    })

    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.findAll('input').length).toBeGreaterThan(0)
    expect(wrapper.find('select').exists()).toBe(true)
  })
})
