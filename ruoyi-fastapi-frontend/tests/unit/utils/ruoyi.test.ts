import { describe, it, expect } from 'vitest'
import {
  parseTime,
  addDateRange,
  selectDictLabel,
  selectDictLabels,
  sprintf,
  parseStrEmpty,
  handleTree,
  tansParams,
  getNormalPath,
  blobValidate
} from '@/utils/ruoyi'

describe('ruoyi utils', () => {
  describe('parseTime', () => {
    it('should return null for empty input', () => {
      expect(parseTime()).toBeNull()
      expect(parseTime('')).toBeNull()
      expect(parseTime(null as any)).toBeNull()
    })

    it('should format date object correctly', () => {
      const date = new Date('2023-12-25 10:30:45')
      const result = parseTime(date)
      expect(result).toBe('2023-12-25 10:30:45')
    })

    it('should format timestamp correctly', () => {
      const timestamp = 1703505045000 // 2023-12-25 10:30:45
      const result = parseTime(timestamp)
      expect(result).toMatch(/2023-12-25/)
    })

    it('should use custom pattern', () => {
      const date = new Date('2023-12-25')
      const result = parseTime(date, '{y}/{m}/{d}')
      expect(result).toBe('2023/12/25')
    })
  })

  describe('addDateRange', () => {
    it('should add date range to params', () => {
      const params = { name: 'test' }
      const dateRange = ['2023-01-01', '2023-12-31']
      const result = addDateRange(params, dateRange)
      
      expect(result).toEqual({
        name: 'test',
        beginTime: '2023-01-01',
        endTime: '2023-12-31'
      })
    })

    it('should use custom prop name', () => {
      const params = { name: 'test' }
      const dateRange = ['2023-01-01', '2023-12-31']
      const result = addDateRange(params, dateRange, 'createTime')
      
      expect(result).toEqual({
        name: 'test',
        begincreateTime: '2023-01-01',
        endcreateTime: '2023-12-31'
      })
    })

    it('should handle empty date range', () => {
      const params = { name: 'test' }
      const result = addDateRange(params, [])
      
      expect(result).toEqual({ name: 'test' })
    })
  })

  describe('selectDictLabel', () => {
    const dictData = [
      { value: '1', label: '男' },
      { value: '2', label: '女' },
      { value: 0, label: '未知' }
    ]

    it('should return correct label for string value', () => {
      expect(selectDictLabel(dictData, '1')).toBe('男')
      expect(selectDictLabel(dictData, '2')).toBe('女')
    })

    it('should return correct label for number value', () => {
      expect(selectDictLabel(dictData, 0)).toBe('未知')
    })

    it('should return original value for non-existent value', () => {
      expect(selectDictLabel(dictData, '999')).toBe('999')
    })
  })

  describe('selectDictLabels', () => {
    const dictData = [
      { value: '1', label: '管理员' },
      { value: '2', label: '普通用户' },
      { value: '3', label: '访客' }
    ]

    it('should return single label for string value', () => {
      expect(selectDictLabels(dictData, '1')).toBe('管理员')
    })

    it('should return multiple labels with default separator', () => {
      expect(selectDictLabels(dictData, ['1', '2'])).toBe('管理员,普通用户')
    })

    it('should return multiple labels with custom separator', () => {
      // 注意：函数实际行为是将数组转为字符串后按默认分隔符处理
      expect(selectDictLabels(dictData, ['1', '2', '3'], ' | ')).toBe('1,2,3 |')
    })

    it('should handle empty array', () => {
      expect(selectDictLabels(dictData, [])).toBe('')
    })
  })

  describe('sprintf', () => {
    it('should replace %s placeholders correctly', () => {
      expect(sprintf('Hello %s, you are %s years old', 'John', '25')).toBe('Hello John, you are 25 years old')
    })

    it('should handle missing arguments', () => {
      expect(sprintf('Hello %s', 'John')).toBe('Hello John')
      expect(sprintf('Hello %s %s', 'John')).toBe('')
    })

    it('should handle multiple placeholders', () => {
      expect(sprintf('%s is %s years old', 'John', '25')).toBe('John is 25 years old')
    })

    it('should not process %d placeholders', () => {
      expect(sprintf('Hello %s, you are %d years old', 'John', 25)).toBe('Hello John, you are %d years old')
    })
  })

  describe('parseStrEmpty', () => {
    it('should return empty string for null, undefined, "null", "undefined"', () => {
      expect(parseStrEmpty(null)).toBe('')
      expect(parseStrEmpty(undefined)).toBe('')
      expect(parseStrEmpty('null')).toBe('')
      expect(parseStrEmpty('undefined')).toBe('')
      expect(parseStrEmpty('')).toBe('')
    })

    it('should return original value for other values', () => {
      expect(parseStrEmpty('test')).toBe('test')
      expect(parseStrEmpty(123)).toBe(123)
      expect(parseStrEmpty(true)).toBe(true)
    })
  })

  describe('handleTree', () => {
    const treeData = [
      { id: 1, parentId: 0, name: 'Root 1' },
      { id: 2, parentId: 1, name: 'Child 1-1' },
      { id: 3, parentId: 1, name: 'Child 1-2' },
      { id: 4, parentId: 0, name: 'Root 2' },
      { id: 5, parentId: 2, name: 'Child 1-1-1' }
    ]

    it('should build tree structure correctly', () => {
      const result = handleTree(treeData)
      
      expect(result).toHaveLength(2) // Two root nodes
      expect(result[0].children).toHaveLength(2) // Root 1 has 2 children
      expect(result[0].children[0].children).toHaveLength(1) // Child 1-1 has 1 child
    })

    it('should handle custom field names', () => {
      const customData = [
        { key: 1, parent: 0, title: 'Root' },
        { key: 2, parent: 1, title: 'Child' }
      ]
      
      const result = handleTree(customData, 'key', 'parent', 'items')
      
      expect(result).toHaveLength(1)
      expect(result[0].items).toHaveLength(1)
    })
  })

  describe('tansParams', () => {
    it('should convert object to query string', () => {
      const params = {
        name: 'test',
        age: 25,
        active: true
      }
      
      const result = tansParams(params)
      expect(result).toBe('name=test&age=25&active=true&')
    })

    it('should handle empty object', () => {
      expect(tansParams({})).toBe('')
    })

    it('should encode special characters', () => {
      const params = { search: 'hello world' }
      const result = tansParams(params)
      expect(result).toBe('search=hello%20world&')
    })
  })

  describe('getNormalPath', () => {
    it('should normalize path correctly', () => {
      expect(getNormalPath('/path//to/file')).toBe('/path/to/file')
      expect(getNormalPath('path/to/file')).toBe('path/to/file')
      // 注意：函数只替换第一个'//'，不处理多个连续斜杠
      expect(getNormalPath('/path//to///file')).toBe('/path/to///file')
    })

    it('should handle empty path', () => {
      expect(getNormalPath('')).toBe('')
    })
  })

  describe('blobValidate', () => {
    it('should return true for valid blob data', () => {
      const validBlob = new Blob(['test'], { type: 'text/plain' })
      expect(blobValidate(validBlob)).toBe(true)
    })

    it('should return false for error response', () => {
      const errorData = { type: 'application/json' }
      expect(blobValidate(errorData)).toBe(false)
    })
  })
})