/**
 * 统一的设计 Token 配置
 * 用于 Tailwind CSS 和 Element Plus 主题一致性
 */

// 基础颜色调色板
export const colors = {
  // 主色调 - 基于 Element Plus 默认主题
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb', 
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#409eff', // Element Plus 默认主色
    600: '#2196f3',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1',
  },
  
  // 功能色 - 与 Element Plus 保持一致
  success: {
    50: '#f0f9ff',
    100: '#e0f7fa',
    200: '#b2ebf2',
    300: '#4dd0e1',
    400: '#26c6da',
    500: '#67c23a', // Element Plus success 色
    600: '#00acc1',
    700: '#0097a7',
    800: '#00838f',
    900: '#006064',
  },
  
  warning: {
    50: '#fffbf0',
    100: '#fff3c4',
    200: '#fce588',
    300: '#fadb14',
    400: '#f9ca24',
    500: '#e6a23c', // Element Plus warning 色
    600: '#d48806',
    700: '#ad6800',
    800: '#874d00',
    900: '#613400',
  },
  
  danger: {
    50: '#fff1f0',
    100: '#ffccc7',
    200: '#ffa39e',
    300: '#ff7875',
    400: '#ff4d4f',
    500: '#f56c6c', // Element Plus danger 色
    600: '#cf1322',
    700: '#a8071a',
    800: '#820014',
    900: '#5c0011',
  },
  
  info: {
    50: '#f7f8fc',
    100: '#e8eaec',
    200: '#c8c9cc',
    300: '#a8abb2',
    400: '#888b97',
    500: '#909399', // Element Plus info 色
    600: '#606266',
    700: '#464c5b',
    800: '#2d3748',
    900: '#1a202c',
  },
  
  // 中性色
  gray: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#ebeef5',
    300: '#dcdfe6',
    400: '#c0c4cc',
    500: '#909399',
    600: '#606266',
    700: '#464c5b',
    800: '#303133',
    900: '#1d1e1f',
  },
  
  // 背景色
  background: {
    light: '#ffffff',
    'light-secondary': '#f8f9fa',
    dark: '#141414',
    'dark-secondary': '#1d1e1f',
  },
  
  // 边框色
  border: {
    light: '#dcdfe6',
    'light-lighter': '#e4e7ed',
    dark: '#434343',
    'dark-lighter': '#303030',
  },
}

// 字体配置
export const fontFamily = {
  sans: [
    'Helvetica Neue',
    'Helvetica', 
    'PingFang SC',
    'Hiragino Sans GB',
    'Microsoft YaHei',
    'Arial',
    'sans-serif'
  ],
}

// 间距配置 - 与 Element Plus 保持一致
export const spacing = {
  'xs': '4px',
  'sm': '8px',
  'md': '12px', 
  'lg': '16px',
  'xl': '20px',
  '2xl': '24px',
  '3xl': '32px',
  '4xl': '40px',
  '5xl': '48px',
}

// 圆角配置
export const borderRadius = {
  'none': '0px',
  'sm': '2px',
  'base': '4px', // Element Plus 默认圆角
  'md': '6px',
  'lg': '8px',
  'xl': '12px',
  '2xl': '16px',
  'full': '9999px',
}

// 阴影配置 - 基于 Element Plus
export const boxShadow = {
  'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  'base': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  'none': 'none',
}

// 断点配置
export const screens = {
  'xs': '480px',
  'sm': '576px',
  'md': '768px',
  'lg': '992px',
  'xl': '1200px',
  '2xl': '1600px',
}

// Z-index 配置
export const zIndex = {
  'dropdown': 1000,
  'sticky': 1020,
  'fixed': 1030,
  'modal-backdrop': 1040,
  'modal': 1050,
  'popover': 1060,
  'tooltip': 1070,
  'toast': 1080,
}

// 导出完整的设计 token
export const designTokens = {
  colors,
  fontFamily,
  spacing,
  borderRadius,
  boxShadow,
  screens,
  zIndex,
}

export default designTokens
