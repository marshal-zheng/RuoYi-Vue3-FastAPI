/**
 * Unit tests for helpers utility functions
 */

import { describe, it, expect } from 'vitest'

// Helper functions
const isEmpty = (value: any): boolean => {
  return value === undefined || value === null || value === ''
}

const isNotEmpty = (value: any): boolean => {
  return !isEmpty(value)
}

const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj))
}

const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout | null = null
  return function executedFunction(...args: any[]) {
    const later = () => {
      timeout = null
      func(...args)
    }
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

const throttle = (func: Function, limit: number) => {
  let inThrottle: boolean
  return function executedFunction(...args: any[]) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

const camelCase = (str: string): string => {
  return str.replace(/[-_](.)/g, (_, c) => c.toUpperCase())
}

const kebabCase = (str: string): string => {
  return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()
}

describe('Helpers Utils', () => {
  describe('isEmpty', () => {
    it('should return true for undefined', () => {
      expect(isEmpty(undefined)).toBe(true)
    })

    it('should return true for null', () => {
      expect(isEmpty(null)).toBe(true)
    })

    it('should return true for empty string', () => {
      expect(isEmpty('')).toBe(true)
    })

    it('should return false for zero', () => {
      expect(isEmpty(0)).toBe(false)
    })

    it('should return false for false', () => {
      expect(isEmpty(false)).toBe(false)
    })

    it('should return false for non-empty string', () => {
      expect(isEmpty('test')).toBe(false)
    })

    it('should return false for empty array', () => {
      expect(isEmpty([])).toBe(false)
    })

    it('should return false for empty object', () => {
      expect(isEmpty({})).toBe(false)
    })
  })

  describe('isNotEmpty', () => {
    it('should return false for undefined', () => {
      expect(isNotEmpty(undefined)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isNotEmpty(null)).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(isNotEmpty('')).toBe(false)
    })

    it('should return true for zero', () => {
      expect(isNotEmpty(0)).toBe(true)
    })

    it('should return true for false', () => {
      expect(isNotEmpty(false)).toBe(true)
    })

    it('should return true for non-empty string', () => {
      expect(isNotEmpty('test')).toBe(true)
    })
  })

  describe('deepClone', () => {
    it('should clone simple object', () => {
      const obj = { a: 1, b: 2 }
      const cloned = deepClone(obj)
      expect(cloned).toEqual(obj)
      expect(cloned).not.toBe(obj)
    })

    it('should clone nested object', () => {
      const obj = { a: { b: { c: 1 } } }
      const cloned = deepClone(obj)
      expect(cloned).toEqual(obj)
      expect(cloned.a).not.toBe(obj.a)
    })

    it('should clone array', () => {
      const arr = [1, 2, 3]
      const cloned = deepClone(arr)
      expect(cloned).toEqual(arr)
      expect(cloned).not.toBe(arr)
    })

    it('should clone array of objects', () => {
      const arr = [{ a: 1 }, { b: 2 }]
      const cloned = deepClone(arr)
      expect(cloned).toEqual(arr)
      expect(cloned[0]).not.toBe(arr[0])
    })
  })

  describe('formatBytes', () => {
    it('should format 0 bytes', () => {
      expect(formatBytes(0)).toBe('0 Bytes')
    })

    it('should format bytes', () => {
      expect(formatBytes(100)).toBe('100 Bytes')
    })

    it('should format kilobytes', () => {
      expect(formatBytes(1024)).toBe('1 KB')
    })

    it('should format megabytes', () => {
      expect(formatBytes(1048576)).toBe('1 MB')
    })

    it('should format gigabytes', () => {
      expect(formatBytes(1073741824)).toBe('1 GB')
    })

    it('should format with custom decimals', () => {
      expect(formatBytes(1536, 0)).toBe('2 KB')
    })

    it('should format with default decimals', () => {
      expect(formatBytes(1536)).toContain('KB')
    })
  })

  describe('generateUUID', () => {
    it('should generate UUID with correct format', () => {
      const uuid = generateUUID()
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
    })

    it('should generate unique UUIDs', () => {
      const uuid1 = generateUUID()
      const uuid2 = generateUUID()
      expect(uuid1).not.toBe(uuid2)
    })

    it('should generate UUID with correct length', () => {
      const uuid = generateUUID()
      expect(uuid.length).toBe(36)
    })
  })

  describe('capitalize', () => {
    it('should capitalize first letter', () => {
      expect(capitalize('hello')).toBe('Hello')
    })

    it('should not change already capitalized string', () => {
      expect(capitalize('Hello')).toBe('Hello')
    })

    it('should handle single character', () => {
      expect(capitalize('a')).toBe('A')
    })

    it('should handle empty string', () => {
      expect(capitalize('')).toBe('')
    })

    it('should only capitalize first letter', () => {
      expect(capitalize('hello world')).toBe('Hello world')
    })
  })

  describe('camelCase', () => {
    it('should convert kebab-case to camelCase', () => {
      expect(camelCase('hello-world')).toBe('helloWorld')
    })

    it('should convert snake_case to camelCase', () => {
      expect(camelCase('hello_world')).toBe('helloWorld')
    })

    it('should handle multiple separators', () => {
      expect(camelCase('hello-world-test')).toBe('helloWorldTest')
    })

    it('should not change already camelCase string', () => {
      expect(camelCase('helloWorld')).toBe('helloWorld')
    })

    it('should handle empty string', () => {
      expect(camelCase('')).toBe('')
    })
  })

  describe('kebabCase', () => {
    it('should convert camelCase to kebab-case', () => {
      expect(kebabCase('helloWorld')).toBe('hello-world')
    })

    it('should convert PascalCase to kebab-case', () => {
      expect(kebabCase('HelloWorld')).toBe('hello-world')
    })

    it('should handle multiple capital letters', () => {
      expect(kebabCase('helloWorldTest')).toBe('hello-world-test')
    })

    it('should not change already kebab-case string', () => {
      expect(kebabCase('hello-world')).toBe('hello-world')
    })

    it('should handle empty string', () => {
      expect(kebabCase('')).toBe('')
    })
  })

  describe('debounce', () => {
    it('should debounce function calls', (done) => {
      let callCount = 0
      const debouncedFn = debounce(() => {
        callCount++
      }, 100)

      debouncedFn()
      debouncedFn()
      debouncedFn()

      setTimeout(() => {
        expect(callCount).toBe(1)
        done()
      }, 150)
    })

    it('should pass arguments to debounced function', (done) => {
      let receivedArg: any
      const debouncedFn = debounce((arg: any) => {
        receivedArg = arg
      }, 100)

      debouncedFn('test')

      setTimeout(() => {
        expect(receivedArg).toBe('test')
        done()
      }, 150)
    })
  })

  describe('throttle', () => {
    it('should throttle function calls', (done) => {
      let callCount = 0
      const throttledFn = throttle(() => {
        callCount++
      }, 100)

      throttledFn()
      throttledFn()
      throttledFn()

      expect(callCount).toBe(1)

      setTimeout(() => {
        throttledFn()
        expect(callCount).toBe(2)
        done()
      }, 150)
    })

    it('should pass arguments to throttled function', () => {
      let receivedArg: any
      const throttledFn = throttle((arg: any) => {
        receivedArg = arg
      }, 100)

      throttledFn('test')
      expect(receivedArg).toBe('test')
    })
  })
})
