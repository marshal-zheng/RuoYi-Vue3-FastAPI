import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}"
  ],
  darkMode: 'class', // 支持 'class' (html.dark) 或 'media' (系统偏好)
  theme: {
    extend: {
      // 如需：自定义 keyframes/animation/spacing ……
    },
  },
  plugins: [],
  // Tailwind v4 推荐 CSS-first：语义组件类已迁移到 theme.css 的 @layer components 中
} satisfies Config

export default config