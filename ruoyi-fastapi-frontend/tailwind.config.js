import { designTokens } from './src/theme/tokens.js'

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}"
  ],
  darkMode: 'class', // 启用 class 策略的暗黑模式
  theme: {
    // 使用统一的设计 token
    colors: {
      // 继承默认颜色
      inherit: 'inherit',
      current: 'currentColor',
      transparent: 'transparent',
      white: '#ffffff',
      black: '#000000',
      
      // 使用统一的颜色系统
      ...designTokens.colors,
    },
    
    fontFamily: designTokens.fontFamily,
    
    spacing: {
      // 保留 Tailwind 默认间距
      '0': '0px',
      '0.5': '0.125rem',
      '1': '0.25rem',
      '1.5': '0.375rem',
      '2': '0.5rem',
      '2.5': '0.625rem',
      '3': '0.75rem',
      '3.5': '0.875rem',
      '4': '1rem',
      '5': '1.25rem',
      '6': '1.5rem',
      '7': '1.75rem',
      '8': '2rem',
      '9': '2.25rem',
      '10': '2.5rem',
      '11': '2.75rem',
      '12': '3rem',
      '14': '3.5rem',
      '16': '4rem',
      '20': '5rem',
      '24': '6rem',
      '28': '7rem',
      '32': '8rem',
      '36': '9rem',
      '40': '10rem',
      '44': '11rem',
      '48': '12rem',
      '52': '13rem',
      '56': '14rem',
      '60': '15rem',
      '64': '16rem',
      '72': '18rem',
      '80': '20rem',
      '96': '24rem',
      
      // 添加语义化间距
      ...designTokens.spacing,
    },
    
    borderRadius: designTokens.borderRadius,
    boxShadow: designTokens.boxShadow,
    screens: designTokens.screens,
    zIndex: designTokens.zIndex,
    
    extend: {
      // CSS 变量支持
      colors: {
        // Element Plus 主题变量映射
        'el-primary': 'var(--el-color-primary, #409eff)',
        'el-success': 'var(--el-color-success, #67c23a)', 
        'el-warning': 'var(--el-color-warning, #e6a23c)',
        'el-danger': 'var(--el-color-danger, #f56c6c)',
        'el-info': 'var(--el-color-info, #909399)',
        
        // 背景色变量
        'el-bg': 'var(--el-bg-color, #ffffff)',
        'el-bg-page': 'var(--el-bg-color-page, #f2f3f5)',
        'el-bg-overlay': 'var(--el-bg-color-overlay, #ffffff)',
        
        // 文字颜色变量
        'el-text-primary': 'var(--el-text-color-primary, #303133)',
        'el-text-regular': 'var(--el-text-color-regular, #606266)',
        'el-text-secondary': 'var(--el-text-color-secondary, #909399)',
        'el-text-placeholder': 'var(--el-text-color-placeholder, #a8abb2)',
        
        // 边框颜色变量
        'el-border': 'var(--el-border-color, #dcdfe6)',
        'el-border-light': 'var(--el-border-color-light, #e4e7ed)',
        'el-border-lighter': 'var(--el-border-color-lighter, #ebeef5)',
        'el-border-extra-light': 'var(--el-border-color-extra-light, #f2f6fc)',
        
        // 自定义项目主题变量
        'sidebar-bg': 'var(--sidebar-bg, #304156)',
        'sidebar-text': 'var(--sidebar-text, #bfcbd9)',
        'navbar-bg': 'var(--navbar-bg, #ffffff)',
        'navbar-text': 'var(--navbar-text, #303133)',
      },
      
      // 动画和过渡
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      
      // 自定义组件类
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    // 添加自定义工具类
    function({ addUtilities }) {
      const newUtilities = {
        // Element Plus 风格的工具类
        '.el-card': {
          '@apply bg-el-bg border border-el-border-light rounded-base shadow-base': {},
        },
        '.el-button-primary': {
          '@apply bg-primary-500 hover:bg-primary-600 text-white border-primary-500 hover:border-primary-600': {},
        },
        '.el-button-success': {
          '@apply bg-success-500 hover:bg-success-600 text-white border-success-500 hover:border-success-600': {},
        },
        '.el-button-warning': {
          '@apply bg-warning-500 hover:bg-warning-600 text-white border-warning-500 hover:border-warning-600': {},
        },
        '.el-button-danger': {
          '@apply bg-danger-500 hover:bg-danger-600 text-white border-danger-500 hover:border-danger-600': {},
        },
        '.el-input': {
          '@apply border border-el-border rounded-base px-3 py-2 focus:border-primary-500 focus:outline-none': {},
        },
        // 布局工具类
        '.app-container': {
          '@apply p-5': {},
        },
        '.page-header': {
          '@apply mb-5 pb-4 border-b border-el-border-lighter': {},
        },
        '.card-shadow': {
          '@apply shadow-base hover:shadow-md transition-shadow duration-300': {},
        },
      }
      
      addUtilities(newUtilities)
    }
  ],
}