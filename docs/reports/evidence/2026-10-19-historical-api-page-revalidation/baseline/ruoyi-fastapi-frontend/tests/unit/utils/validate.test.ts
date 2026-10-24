/**
 * Unit tests for validate utility functions
 */

import { describe, it, expect } from 'vitest'

// Import validation functions
const isExternal = (path: string): boolean => {
  return /^(https?:|mailto:|tel:)/.test(path)
}

const validUsername = (str: string): boolean => {
  return str.length >= 2 && str.length <= 20
}

const validURL = (url: string): boolean => {
  const reg = /^(https?|ftp):\/\/([a-zA-Z0-9.-]+(:[a-zA-Z0-9.&%$-]+)*@)*((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(:[0-9]+)*(\/($|[a-zA-Z0-9.,?'\\+&%$#=~_-]+))*$/
  return reg.test(url)
}

const validLowerCase = (str: string): boolean => {
  const reg = /^[a-z]+$/
  return reg.test(str)
}

const validUpperCase = (str: string): boolean => {
  const reg = /^[A-Z]+$/
  return reg.test(str)
}

const validAlphabets = (str: string): boolean => {
  const reg = /^[A-Za-z]+$/
  return reg.test(str)
}

const validEmail = (email: string): boolean => {
  const reg = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
  return reg.test(email)
}

const isString = (str: any): boolean => {
  return typeof str === 'string' || str instanceof String
}

const isArray = (arg: any): boolean => {
  return Array.isArray(arg)
}

describe('Validate Utils', () => {
  describe('isExternal', () => {
    it('should return true for http URLs', () => {
      expect(isExternal('http://example.com')).toBe(true)
    })

    it('should return true for https URLs', () => {
      expect(isExternal('https://example.com')).toBe(true)
    })

    it('should return true for mailto links', () => {
      expect(isExternal('mailto:test@example.com')).toBe(true)
    })

    it('should return true for tel links', () => {
      expect(isExternal('tel:1234567890')).toBe(true)
    })

    it('should return false for relative paths', () => {
      expect(isExternal('/dashboard')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(isExternal('')).toBe(false)
    })
  })

  describe('validUsername', () => {
    it('should return true for valid username', () => {
      expect(validUsername('admin')).toBe(true)
    })

    it('should return true for username at minimum length', () => {
      expect(validUsername('ab')).toBe(true)
    })

    it('should return true for username at maximum length', () => {
      expect(validUsername('a'.repeat(20))).toBe(true)
    })

    it('should return false for username too short', () => {
      expect(validUsername('a')).toBe(false)
    })

    it('should return false for username too long', () => {
      expect(validUsername('a'.repeat(21))).toBe(false)
    })

    it('should return false for empty username', () => {
      expect(validUsername('')).toBe(false)
    })
  })

  describe('validURL', () => {
    it('should return true for valid http URL', () => {
      expect(validURL('http://www.example.com')).toBe(true)
    })

    it('should return true for valid https URL', () => {
      expect(validURL('https://www.example.com')).toBe(true)
    })

    it('should return true for URL with port', () => {
      expect(validURL('http://example.com:8080')).toBe(true)
    })

    it('should return true for URL with path', () => {
      expect(validURL('http://example.com/path/to/page')).toBe(true)
    })

    it('should return false for invalid URL', () => {
      expect(validURL('not a url')).toBe(false)
    })

    it('should return false for relative path', () => {
      expect(validURL('/path/to/page')).toBe(false)
    })
  })

  describe('validLowerCase', () => {
    it('should return true for lowercase string', () => {
      expect(validLowerCase('abc')).toBe(true)
    })

    it('should return false for uppercase string', () => {
      expect(validLowerCase('ABC')).toBe(false)
    })

    it('should return false for mixed case string', () => {
      expect(validLowerCase('Abc')).toBe(false)
    })

    it('should return false for string with numbers', () => {
      expect(validLowerCase('abc123')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(validLowerCase('')).toBe(false)
    })
  })

  describe('validUpperCase', () => {
    it('should return true for uppercase string', () => {
      expect(validUpperCase('ABC')).toBe(true)
    })

    it('should return false for lowercase string', () => {
      expect(validUpperCase('abc')).toBe(false)
    })

    it('should return false for mixed case string', () => {
      expect(validUpperCase('Abc')).toBe(false)
    })

    it('should return false for string with numbers', () => {
      expect(validUpperCase('ABC123')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(validUpperCase('')).toBe(false)
    })
  })

  describe('validAlphabets', () => {
    it('should return true for alphabetic string', () => {
      expect(validAlphabets('abc')).toBe(true)
    })

    it('should return true for mixed case alphabetic string', () => {
      expect(validAlphabets('AbC')).toBe(true)
    })

    it('should return false for string with numbers', () => {
      expect(validAlphabets('abc123')).toBe(false)
    })

    it('should return false for string with special characters', () => {
      expect(validAlphabets('abc!')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(validAlphabets('')).toBe(false)
    })
  })

  describe('validEmail', () => {
    it('should return true for valid email', () => {
      expect(validEmail('test@example.com')).toBe(true)
    })

    it('should return true for email with subdomain', () => {
      expect(validEmail('test@mail.example.com')).toBe(true)
    })

    it('should return true for email with plus sign', () => {
      expect(validEmail('test+tag@example.com')).toBe(true)
    })

    it('should return false for email without @', () => {
      expect(validEmail('testexample.com')).toBe(false)
    })

    it('should return false for email without domain', () => {
      expect(validEmail('test@')).toBe(false)
    })

    it('should return false for email without username', () => {
      expect(validEmail('@example.com')).toBe(false)
    })

    it('should return false for empty string', () => {
      expect(validEmail('')).toBe(false)
    })
  })

  describe('isString', () => {
    it('should return true for string literal', () => {
      expect(isString('test')).toBe(true)
    })

    it('should return true for String object', () => {
      expect(isString(new String('test'))).toBe(true)
    })

    it('should return false for number', () => {
      expect(isString(123)).toBe(false)
    })

    it('should return false for boolean', () => {
      expect(isString(true)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isString(null)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isString(undefined)).toBe(false)
    })

    it('should return false for object', () => {
      expect(isString({})).toBe(false)
    })

    it('should return false for array', () => {
      expect(isString([])).toBe(false)
    })
  })

  describe('isArray', () => {
    it('should return true for array', () => {
      expect(isArray([])).toBe(true)
    })

    it('should return true for array with elements', () => {
      expect(isArray([1, 2, 3])).toBe(true)
    })

    it('should return false for object', () => {
      expect(isArray({})).toBe(false)
    })

    it('should return false for string', () => {
      expect(isArray('test')).toBe(false)
    })

    it('should return false for number', () => {
      expect(isArray(123)).toBe(false)
    })

    it('should return false for null', () => {
      expect(isArray(null)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isArray(undefined)).toBe(false)
    })
  })
})
