/**
 * RuoYi 通用工具函数测试
 * 测试日期格式化、字典处理、树结构等功能
 */
import { describe, it, expect } from 'vitest'
import {
  parseTime,
  addDateRange,
  selectDictLabel,
  selectDictLabels,
  sprintf,
  parseStrEmpty,
  mergeRecursive,
  handleTree,
  tansParams,
  getNormalPath,
  blobValidate
} from '@/utils/ruoyi'

describe('RuoYi Utils', () => {
  describe('parseTime', () => {
    it('should format date object', () => {
      const date = new Date('2024-01-15 10:30:45')
      const result = parseTime(date)
      expect(result).toMatch(/2024-01-15 \d{2}:\d{2}:\d{2}/)
    })

    it('should format timestamp (milliseconds)', () => {
      const timestamp = new Date('2024-01-15').getTime()
      const result = parseTime(timestamp)
      expect(result).toContain('2024-01-15')
    })

    it('should format timestamp (seconds)', () => {
      const timestamp = Math.floor(new Date('2024-01-15').getTime() / 1000)
      const result = parseTime(timestamp)
      expect(result).toContain('2024-01-15')
    })

    it('should format date string', () => {
      const result = parseTime('2024-01-15 10:30:45')
      expect(result).toContain('2024-01-15')
    })

    it('should handle custom pattern', () => {
      const date = new Date('2024-01-15')
      const result = parseTime(date, '{y}/{m}/{d}')
      expect(result).toMatch(/2024\/01\/15/)
    })

    it('should return null for empty input', () => {
      const result = parseTime()
      expect(result).toBeNull()
    })

    it('should return null for null input', () => {
      // @ts-ignore
      const result = parseTime(null)
      expect(result).toBeNull()
    })

    it('should handle ISO date string', () => {
      const result = parseTime('2024-01-15T10:30:45.000Z')
      expect(result).toContain('2024-01-15')
    })

    it('should format with weekday', () => {
      const date = new Date('2024-01-15')
      const result = parseTime(date, '{y}-{m}-{d} 星期{a}')
      expect(result).toMatch(/2024-01-15 星期[一二三四五六日]/)
    })

    it('should pad single digits', () => {
      const date = new Date('2024-01-05 09:05:03')
      const result = parseTime(date, '{y}-{m}-{d} {h}:{i}:{s}')
      expect(result).toMatch(/2024-01-05 \d{2}:\d{2}:\d{2}/)
    })
  })

  describe('addDateRange', () => {
    it('should add default date range', () => {
      const params = { name: 'test' }
      const dateRange = ['2024-01-01', '2024-01-31']
      const result = addDateRange(params, dateRange)
      
      expect(result.beginTime).toBe('2024-01-01')
      expect(result.endTime).toBe('2024-01-31')
      expect(result.name).toBe('test')
    })

    it('should add custom property date range', () => {
      const params = { name: 'test' }
      const dateRange = ['2024-01-01', '2024-01-31']
      const result = addDateRange(params, dateRange, 'CreateTime')
      
      expect(result.beginCreateTime).toBe('2024-01-01')
      expect(result.endCreateTime).toBe('2024-01-31')
    })

    it('should handle empty date range', () => {
      const params = { name: 'test' }
      const result = addDateRange(params, [])
      
      expect(result.beginTime).toBeUndefined()
      expect(result.endTime).toBeUndefined()
    })

    it('should handle non-array date range', () => {
      const params = { name: 'test' }
      // @ts-ignore
      const result = addDateRange(params, null)
      
      expect(result.beginTime).toBeUndefined()
      expect(result.endTime).toBeUndefined()
    })
  })

  describe('selectDictLabel', () => {
    const dicts = [
      { value: '0', label: '正常' },
      { value: '1', label: '停用' },
      { value: 2, label: '删除' }
    ]

    it('should return label for string value', () => {
      const result = selectDictLabel(dicts, '0')
      expect(result).toBe('正常')
    })

    it('should return label for number value', () => {
      const result = selectDictLabel(dicts, 2)
      expect(result).toBe('删除')
    })

    it('should return value when not found', () => {
      const result = selectDictLabel(dicts, '999')
      expect(result).toBe('999')
    })

    it('should return empty string for undefined', () => {
      // @ts-ignore
      const result = selectDictLabel(dicts, undefined)
      expect(result).toBe('')
    })
  })

  describe('selectDictLabels', () => {
    const dicts = [
      { value: '0', label: '正常' },
      { value: '1', label: '停用' },
      { value: '2', label: '删除' }
    ]

    it('should return labels for comma-separated values', () => {
      const result = selectDictLabels(dicts, '0,1')
      expect(result).toBe('正常,停用')
    })

    it('should return labels for array values', () => {
      const result = selectDictLabels(dicts, ['0', '1'])
      expect(result).toBe('正常,停用')
    })

    it('should handle custom separator', () => {
      const result = selectDictLabels(dicts, '0,1', ';')
      expect(result).toBe('正常;停用')
    })

    it('should return empty string for undefined', () => {
      // @ts-ignore
      const result = selectDictLabels(dicts, undefined)
      expect(result).toBe('')
    })

    it('should return empty string for empty array', () => {
      const result = selectDictLabels(dicts, [])
      expect(result).toBe('')
    })

    it('should include original value when not found', () => {
      const result = selectDictLabels(dicts, '0,999')
      expect(result).toContain('正常')
      expect(result).toContain('999')
    })
  })

  describe('sprintf', () => {
    it('should replace single placeholder', () => {
      const result = sprintf('Hello %s', 'World')
      expect(result).toBe('Hello World')
    })

    it('should replace multiple placeholders', () => {
      const result = sprintf('Hello %s, you are %s', 'John', 'awesome')
      expect(result).toBe('Hello John, you are awesome')
    })

    it('should handle missing arguments', () => {
      const result = sprintf('Hello %s %s', 'World')
      expect(result).toBe('')
    })

    it('should handle no placeholders', () => {
      const result = sprintf('Hello World')
      expect(result).toBe('Hello World')
    })

    it('should handle number arguments', () => {
      const result = sprintf('Count: %s', 42)
      expect(result).toBe('Count: 42')
    })
  })

  describe('parseStrEmpty', () => {
    it('should return empty string for null', () => {
      const result = parseStrEmpty(null)
      expect(result).toBe('')
    })

    it('should return empty string for undefined', () => {
      const result = parseStrEmpty(undefined)
      expect(result).toBe('')
    })

    it('should return empty string for "null" string', () => {
      const result = parseStrEmpty('null')
      expect(result).toBe('')
    })

    it('should return empty string for "undefined" string', () => {
      const result = parseStrEmpty('undefined')
      expect(result).toBe('')
    })

    it('should return original string for valid input', () => {
      const result = parseStrEmpty('test')
      expect(result).toBe('test')
    })

    it('should return number as is', () => {
      const result = parseStrEmpty(123)
      expect(result).toBe(123)
    })

    it('should return empty string for empty string', () => {
      const result = parseStrEmpty('')
      expect(result).toBe('')
    })
  })

  describe('mergeRecursive', () => {
    it('should merge simple objects', () => {
      const source = { a: 1, b: 2 }
      const target = { b: 3, c: 4 }
      const result = mergeRecursive(source, target)
      
      expect(result.a).toBe(1)
      expect(result.b).toBe(3)
      expect(result.c).toBe(4)
    })

    it('should merge nested objects', () => {
      const source = { a: { x: 1 } }
      const target = { a: { y: 2 } }
      const result = mergeRecursive(source, target)
      
      expect(result.a.x).toBe(1)
      expect(result.a.y).toBe(2)
    })

    it('should handle null source properties', () => {
      const source = { a: null }
      const target = { a: { x: 1 } }
      const result = mergeRecursive(source, target)
      
      expect(result.a.x).toBe(1)
    })

    it('should overwrite primitives', () => {
      const source = { a: 1 }
      const target = { a: 2 }
      const result = mergeRecursive(source, target)
      
      expect(result.a).toBe(2)
    })
  })

  describe('handleTree', () => {
    const data = [
      { id: 1, parentId: 0, name: 'Root' },
      { id: 2, parentId: 1, name: 'Child 1' },
      { id: 3, parentId: 1, name: 'Child 2' },
      { id: 4, parentId: 2, name: 'Grandchild' }
    ]

    it('should build tree structure', () => {
      const tree = handleTree(data)
      
      expect(tree).toHaveLength(1)
      expect(tree[0].id).toBe(1)
      expect(tree[0].children).toHaveLength(2)
    })

    it('should handle custom field names', () => {
      const customData = [
        { key: 1, parent: 0, name: 'Root' },
        { key: 2, parent: 1, name: 'Child' }
      ]
      const tree = handleTree(customData, 'key', 'parent', 'kids')
      
      expect(tree[0].kids).toBeDefined()
    })

    it('should handle empty data', () => {
      const tree = handleTree([])
      expect(tree).toEqual([])
    })

    it('should handle flat structure', () => {
      const flatData = [
        { id: 1, parentId: 0, name: 'Item 1' },
        { id: 2, parentId: 0, name: 'Item 2' }
      ]
      const tree = handleTree(flatData)
      
      expect(tree).toHaveLength(2)
    })

    it('should handle deep nesting', () => {
      const deepData = [
        { id: 1, parentId: 0, name: 'Level 1' },
        { id: 2, parentId: 1, name: 'Level 2' },
        { id: 3, parentId: 2, name: 'Level 3' },
        { id: 4, parentId: 3, name: 'Level 4' }
      ]
      const tree = handleTree(deepData)
      
      expect(tree[0].children[0].children[0].children).toHaveLength(1)
    })
  })

  describe('tansParams', () => {
    it('should encode simple params', () => {
      const params = { name: 'test', age: 25 }
      const result = tansParams(params)
      
      expect(result).toContain('name=test')
      expect(result).toContain('age=25')
    })

    it('should handle nested objects', () => {
      const params = { user: { name: 'test', age: 25 } }
      const result = tansParams(params)
      
      expect(result).toContain('user%5Bname%5D=test')
      expect(result).toContain('user%5Bage%5D=25')
    })

    it('should skip null values', () => {
      const params = { name: 'test', age: null }
      const result = tansParams(params)
      
      expect(result).toContain('name=test')
      expect(result).not.toContain('age')
    })

    it('should skip empty strings', () => {
      const params = { name: 'test', age: '' }
      const result = tansParams(params)
      
      expect(result).toContain('name=test')
      expect(result).not.toContain('age')
    })

    it('should skip undefined values', () => {
      const params = { name: 'test', age: undefined }
      const result = tansParams(params)
      
      expect(result).toContain('name=test')
      expect(result).not.toContain('age')
    })

    it('should encode special characters', () => {
      const params = { name: 'test@example.com' }
      const result = tansParams(params)
      
      expect(result).toContain('name=test%40example.com')
    })
  })

  describe('getNormalPath', () => {
    it('should normalize double slashes', () => {
      const result = getNormalPath('/path//to/file')
      expect(result).toBe('/path/to/file')
    })

    it('should remove trailing slash', () => {
      const result = getNormalPath('/path/to/file/')
      expect(result).toBe('/path/to/file')
    })

    it('should handle empty string', () => {
      const result = getNormalPath('')
      expect(result).toBe('')
    })

    it('should handle undefined', () => {
      // @ts-ignore
      const result = getNormalPath(undefined)
      expect(result).toBe('')
    })

    it('should handle "undefined" string', () => {
      const result = getNormalPath('undefined')
      expect(result).toBe('')
    })

    it('should handle normal path', () => {
      const result = getNormalPath('/path/to/file')
      expect(result).toBe('/path/to/file')
    })

    it('should handle multiple double slashes', () => {
      const result = getNormalPath('/path//to//file')
      expect(result).toBe('/path/to/file')
    })
  })

  describe('blobValidate', () => {
    it('should return true for blob data', () => {
      const blob = { type: 'application/octet-stream' }
      const result = blobValidate(blob)
      expect(result).toBe(true)
    })

    it('should return false for JSON data', () => {
      const json = { type: 'application/json' }
      const result = blobValidate(json)
      expect(result).toBe(false)
    })

    it('should return true for image data', () => {
      const image = { type: 'image/png' }
      const result = blobValidate(image)
      expect(result).toBe(true)
    })

    it('should return true for PDF data', () => {
      const pdf = { type: 'application/pdf' }
      const result = blobValidate(pdf)
      expect(result).toBe(true)
    })

    it('should return true for Excel data', () => {
      const excel = { type: 'application/vnd.ms-excel' }
      const result = blobValidate(excel)
      expect(result).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle parseTime with invalid date', () => {
      const result = parseTime('invalid-date')
      expect(result).toBeTruthy() // Will return some date string
    })

    it('should handle handleTree with circular references prevention', () => {
      const data = [
        { id: 1, parentId: 2, name: 'Node 1' },
        { id: 2, parentId: 1, name: 'Node 2' }
      ]
      const tree = handleTree(data)
      expect(tree).toBeDefined()
    })

    it('should handle tansParams with array values', () => {
      const params = { ids: [1, 2, 3] }
      const result = tansParams(params)
      expect(result).toBeTruthy()
    })

    it('should handle mergeRecursive with arrays', () => {
      const source = { arr: [1, 2] }
      const target = { arr: [3, 4] }
      const result = mergeRecursive(source, target)
      expect(result.arr).toBeDefined()
    })
  })
})
