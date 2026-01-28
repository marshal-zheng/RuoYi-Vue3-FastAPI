/**
 * Unit tests for project API service
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as projectApi from '@/api/project/project'
import request from '@/utils/request'

// Mock request utility
vi.mock('@/utils/request')

describe('Project API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listProject', () => {
    it('should fetch project list', async () => {
      const mockResponse = {
        code: 200,
        data: {
          rows: [
            { project_id: 1, project_name: 'Project 1' },
            { project_id: 2, project_name: 'Project 2' }
          ],
          total: 2
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await projectApi.listProject({ page_num: 1, page_size: 10 })

      expect(request.get).toHaveBeenCalledWith('/system/project/list', {
        params: { page_num: 1, page_size: 10 }
      })
      expect(result.data.rows.length).toBe(2)
    })

    it('should handle empty project list', async () => {
      const mockResponse = {
        code: 200,
        data: { rows: [], total: 0 }
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await projectApi.listProject({})

      expect(result.data.rows).toEqual([])
      expect(result.data.total).toBe(0)
    })

    it('should handle API error', async () => {
      vi.mocked(request.get).mockRejectedValue(new Error('Network error'))

      await expect(projectApi.listProject({})).rejects.toThrow('Network error')
    })
  })

  describe('getProject', () => {
    it('should fetch project by ID', async () => {
      const mockProject = {
        code: 200,
        data: {
          project_id: 1,
          project_name: 'Test Project',
          project_code: 'TEST001'
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockProject)

      const result = await projectApi.getProject(1)

      expect(request.get).toHaveBeenCalledWith('/system/project/1')
      expect(result.data.project_id).toBe(1)
    })

    it('should handle non-existent project', async () => {
      vi.mocked(request.get).mockRejectedValue(new Error('Project not found'))

      await expect(projectApi.getProject(999)).rejects.toThrow('Project not found')
    })
  })

  describe('addProject', () => {
    it('should create new project', async () => {
      const projectData = {
        project_name: 'New Project',
        project_code: 'NEW001',
        description: 'Test description'
      }

      const mockResponse = {
        code: 200,
        data: { project_id: 1 }
      }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await projectApi.addProject(projectData)

      expect(request.post).toHaveBeenCalledWith('/system/project', projectData)
      expect(result.data.project_id).toBe(1)
    })

    it('should validate required fields', async () => {
      const invalidData = { project_name: '' }

      vi.mocked(request.post).mockRejectedValue(new Error('项目名称不能为空'))

      await expect(projectApi.addProject(invalidData)).rejects.toThrow('项目名称不能为空')
    })

    it('should handle duplicate project code', async () => {
      const projectData = {
        project_name: 'Test',
        project_code: 'DUPLICATE'
      }

      vi.mocked(request.post).mockRejectedValue(new Error('项目编码已存在'))

      await expect(projectApi.addProject(projectData)).rejects.toThrow('项目编码已存在')
    })
  })

  describe('updateProject', () => {
    it('should update existing project', async () => {
      const projectData = {
        project_id: 1,
        project_name: 'Updated Project'
      }

      const mockResponse = { code: 200, msg: 'success' }

      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const result = await projectApi.updateProject(projectData)

      expect(request.put).toHaveBeenCalledWith('/system/project', projectData)
      expect(result.code).toBe(200)
    })

    it('should handle update of non-existent project', async () => {
      const projectData = { project_id: 999, project_name: 'Test' }

      vi.mocked(request.put).mockRejectedValue(new Error('项目不存在'))

      await expect(projectApi.updateProject(projectData)).rejects.toThrow('项目不存在')
    })
  })

  describe('delProject', () => {
    it('should delete project by ID', async () => {
      const mockResponse = { code: 200, msg: 'success' }

      vi.mocked(request.delete).mockResolvedValue(mockResponse)

      const result = await projectApi.delProject(1)

      expect(request.delete).toHaveBeenCalledWith('/system/project/1')
      expect(result.code).toBe(200)
    })

    it('should delete multiple projects', async () => {
      const mockResponse = { code: 200, msg: 'success' }

      vi.mocked(request.delete).mockResolvedValue(mockResponse)

      const result = await projectApi.delProject([1, 2, 3])

      expect(request.delete).toHaveBeenCalledWith('/system/project/1,2,3')
    })

    it('should handle delete error', async () => {
      vi.mocked(request.delete).mockRejectedValue(new Error('删除失败'))

      await expect(projectApi.delProject(1)).rejects.toThrow('删除失败')
    })
  })

  describe('exportProject', () => {
    it('should export project data', async () => {
      const mockBlob = new Blob(['project data'], { type: 'application/json' })
      const mockResponse = { data: mockBlob }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await projectApi.exportProject(1)

      expect(request.get).toHaveBeenCalledWith('/system/project/export/1', {
        responseType: 'blob'
      })
      expect(result.data).toBeInstanceOf(Blob)
    })

    it('should handle export error', async () => {
      vi.mocked(request.get).mockRejectedValue(new Error('导出失败'))

      await expect(projectApi.exportProject(1)).rejects.toThrow('导出失败')
    })
  })

  describe('importProject', () => {
    it('should import project data', async () => {
      const file = new File(['project data'], 'project.json', { type: 'application/json' })
      const mockResponse = { code: 200, data: { project_id: 1 } }

      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await projectApi.importProject(file)

      expect(request.post).toHaveBeenCalled()
      expect(result.data.project_id).toBe(1)
    })

    it('should validate file format', async () => {
      const invalidFile = new File(['invalid'], 'test.txt', { type: 'text/plain' })

      vi.mocked(request.post).mockRejectedValue(new Error('文件格式不正确'))

      await expect(projectApi.importProject(invalidFile)).rejects.toThrow('文件格式不正确')
    })
  })

  describe('getProjectTopology', () => {
    it('should fetch project topology', async () => {
      const mockTopology = {
        code: 200,
        data: {
          nodes: [
            { id: 1, name: 'Node 1' },
            { id: 2, name: 'Node 2' }
          ],
          edges: [
            { source: 1, target: 2 }
          ]
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockTopology)

      const result = await projectApi.getProjectTopology(1)

      expect(request.get).toHaveBeenCalledWith('/system/project/1/topology')
      expect(result.data.nodes.length).toBe(2)
      expect(result.data.edges.length).toBe(1)
    })

    it('should handle empty topology', async () => {
      const mockResponse = {
        code: 200,
        data: { nodes: [], edges: [] }
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await projectApi.getProjectTopology(1)

      expect(result.data.nodes).toEqual([])
      expect(result.data.edges).toEqual([])
    })
  })

  describe('updateProjectTopology', () => {
    it('should update project topology', async () => {
      const topologyData = {
        nodes: [{ id: 1, name: 'Node 1' }],
        edges: []
      }

      const mockResponse = { code: 200, msg: 'success' }

      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const result = await projectApi.updateProjectTopology(1, topologyData)

      expect(request.put).toHaveBeenCalledWith('/system/project/1/topology', topologyData)
      expect(result.code).toBe(200)
    })

    it('should validate topology data', async () => {
      const invalidData = { nodes: null }

      vi.mocked(request.put).mockRejectedValue(new Error('拓扑数据格式不正确'))

      await expect(projectApi.updateProjectTopology(1, invalidData)).rejects.toThrow('拓扑数据格式不正确')
    })
  })

  describe('Error Handling', () => {
    it('should handle 401 unauthorized', async () => {
      const error = {
        response: { status: 401, data: { msg: 'Unauthorized' } }
      }

      vi.mocked(request.get).mockRejectedValue(error)

      await expect(projectApi.listProject({})).rejects.toMatchObject(error)
    })

    it('should handle 403 forbidden', async () => {
      const error = {
        response: { status: 403, data: { msg: 'Forbidden' } }
      }

      vi.mocked(request.get).mockRejectedValue(error)

      await expect(projectApi.getProject(1)).rejects.toMatchObject(error)
    })

    it('should handle 500 server error', async () => {
      const error = {
        response: { status: 500, data: { msg: 'Internal Server Error' } }
      }

      vi.mocked(request.post).mockRejectedValue(error)

      await expect(projectApi.addProject({})).rejects.toMatchObject(error)
    })

    it('should handle network timeout', async () => {
      const error = new Error('timeout of 5000ms exceeded')

      vi.mocked(request.get).mockRejectedValue(error)

      await expect(projectApi.listProject({})).rejects.toThrow('timeout')
    })
  })
})
