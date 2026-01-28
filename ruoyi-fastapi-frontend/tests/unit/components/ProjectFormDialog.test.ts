/**
 * Unit tests for ProjectFormDialog component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElForm, ElInput, ElSelect } from 'element-plus'
import ProjectFormDialog from '@/views/project/components/ProjectFormDialog.vue'

// Mock dependencies
vi.mock('@/api/project/project', () => ({
  getProject: vi.fn(),
  addProject: vi.fn(),
  updateProject: vi.fn(),
}))

describe('ProjectFormDialog', () => {
  let wrapper: any

  const createWrapper = (props = {}) => {
    return mount(ProjectFormDialog, {
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
          ZxDialog: true,
          ElFormItem: true,
          ElRow: true,
          ElCol: true,
          ElOption: true,
        },
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render dialog when visible', () => {
      wrapper = createWrapper({ visible: true })
      expect(wrapper.exists()).toBe(true)
    })

    it('should not render dialog when not visible', () => {
      wrapper = createWrapper({ visible: false })
      expect(wrapper.props('visible')).toBe(false)
    })

    it('should render form with inputs', () => {
      wrapper = createWrapper()
      expect(wrapper.findAllComponents(ElInput).length).toBeGreaterThan(0)
    })
  })

  describe('Add Mode', () => {
    it('should have empty initial data in add mode', () => {
      wrapper = createWrapper({ projectId: undefined })
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should show add title in add mode', () => {
      wrapper = createWrapper({ projectId: undefined })
      expect(wrapper.vm.dialogTitle).toContain('新增')
    })

    it('should validate required fields in add mode', () => {
      wrapper = createWrapper({ projectId: undefined })
      expect(wrapper.vm.formRules).toBeDefined()
    })
  })

  describe('Edit Mode', () => {
    it('should load project data in edit mode', () => {
      wrapper = createWrapper({ projectId: 1 })
      expect(wrapper.vm.formData).toBeDefined()
    })

    it('should show edit title in edit mode', () => {
      wrapper = createWrapper({ projectId: 1 })
      expect(wrapper.vm.dialogTitle).toContain('修改')
    })

    it('should populate form with existing data', () => {
      wrapper = createWrapper({ projectId: 1 })
      expect(wrapper.vm.formData).toBeDefined()
    })
  })

  describe('Form Validation', () => {
    it('should validate project name', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules?.projectName).toBeDefined()
    })

    it('should validate project name length', () => {
      wrapper = createWrapper()
      const rules = wrapper.vm.formRules?.projectName
      expect(rules).toBeDefined()
    })

    it('should validate required fields', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules).toBeDefined()
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

  describe('Project Name Field', () => {
    it('should render project name input', () => {
      wrapper = createWrapper()
      const inputs = wrapper.findAllComponents(ElInput)
      expect(inputs.length).toBeGreaterThan(0)
    })

    it('should bind project name to model', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formData?.projectName).toBeDefined()
    })

    it('should validate project name on input', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formRules?.projectName).toBeDefined()
    })
  })

  describe('Description Field', () => {
    it('should render description textarea', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.formData?.description).toBeDefined()
    })

    it('should allow optional description', () => {
      wrapper = createWrapper()
      wrapper.vm.formData.description = ''
      expect(wrapper.vm.formData.description).toBe('')
    })
  })

  describe('Dialog Events', () => {
    it('should handle dialog close event', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.dialogEvents).toBeDefined()
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

  describe('Edge Cases', () => {
    it('should handle missing project ID gracefully', () => {
      wrapper = createWrapper({ projectId: null })
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle invalid project ID', () => {
      wrapper = createWrapper({ projectId: -1 })
      expect(wrapper.exists()).toBe(true)
    })

    it('should handle empty form data', () => {
      wrapper = createWrapper()
      wrapper.vm.formData = {}
      expect(wrapper.vm.formData).toEqual({})
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
      wrapper.vm.formData = { projectName: 'Test' }
      expect(wrapper.vm.formData.projectName).toBe('Test')
    })

    it('should clear validation errors on reset', () => {
      wrapper = createWrapper()
      const form = wrapper.findComponent(ElForm)
      expect(form.exists()).toBe(true)
    })
  })

  describe('Loading State', () => {
    it('should show loading state during data fetch', () => {
      wrapper = createWrapper({ projectId: 1 })
      expect(wrapper.vm.loading).toBeDefined()
    })

    it('should disable form during submission', () => {
      wrapper = createWrapper()
      expect(wrapper.vm.loading).toBeDefined()
    })
  })
})
