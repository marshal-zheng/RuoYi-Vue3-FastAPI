# RuoYi项目UI样式对齐方案

## 1. CSS变量系统迁移

### 1.1 创建新的CSS变量文件
需要在 `src/assets/styles/` 下创建 `design-tokens.css`：

```css
:root {
  /* ===== 基础设计令牌 ===== */
  
  /* 主色调系统 - 企业蓝 */
  --el-color-primary: #0052d9 !important;
  --el-color-primary-light-3: #3370ff !important;
  --el-color-primary-light-5: #6690ff !important;
  --el-color-primary-light-7: #99b5ff !important;
  --el-color-primary-light-8: #b3ccff !important;
  --el-color-primary-light-9: #e6f0ff !important;
  --el-color-primary-dark-2: #003ba8 !important;

  /* 文本颜色层级 */
  --el-text-color-primary: #1d2129 !important;
  --el-text-color-regular: #4e5969 !important;
  --el-text-color-secondary: #86909c !important;
  --el-text-color-placeholder: #c9cdd4 !important;

  /* 背景色系统 */
  --el-bg-color: #ffffff;
  --el-bg-color-page: #f7f8fa;
  --app-content-bg-color: #f5f7fa;

  /* 边框颜色 */
  --el-border-color: #e5e6eb !important;
  --el-border-color-light: #f0f1f5 !important;
  --el-border-color-lighter: #f5f6fa !important;

  /* ===== 左侧菜单系统 ===== */
  --left-menu-max-width: 200px;
  --left-menu-min-width: 64px;
  --left-menu-bg-color: #f6f8fc;
  --left-menu-bg-active-color: rgba(35, 101, 235, 0.14);
  --left-menu-hover-bg-color: rgba(35, 101, 235, 0.1);
  --left-menu-text-color: #1f2a37;
  --left-menu-text-active-color: #1e5eff;
  --left-menu-border-color: #d9e2f4;
  --left-menu-active-bar-width: 4px;
  --left-menu-box-shadow: 0 12px 30px rgba(17, 40, 84, 0.08);
  --left-menu-indent-color: rgba(79, 117, 191, 0.28);

  /* ===== 顶部工具栏系统 ===== */
  --logo-height: 50px;
  --top-header-bg-color: #ffffff;
  --top-header-text-color: #4e5969;
  --top-header-hover-color: #f2f5fc;
  --top-tool-height: var(--logo-height);

  /* ===== 标签页系统 ===== */
  --tags-view-height: 38px;
  --tags-view-bg-color: #f3f5f9;
  --tags-view-border-color: #d9e2f4;
  --tags-view-item-bg: transparent;
  --tags-view-item-hover-bg: rgba(30, 94, 255, 0.08);
  --tags-view-text-color: #3a4558;
  --tags-view-text-active-color: #1e5eff;
  --tags-view-indicator-color: #1e5eff;

  /* ===== 阴影系统 ===== */
  --el-box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
  --el-box-shadow-light: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  --app-card-shadow: 0 10px 24px rgba(0, 0, 0, 0.06), 0 2px 8px rgba(0, 0, 0, 0.04);

  /* ===== 动画系统 ===== */
  --transition-time-02: 0.2s;
  --transition-time-03: 0.3s;

  /* ===== 圆角系统 ===== */
  --el-border-radius-base: 2px !important;
  --el-border-radius-small: 2px !important;
  --app-card-radius: 0;
}
```

### 1.2 更新variables.module.less
需要逐步替换现有Less变量：

```less
// 保持向后兼容，同时引入新的CSS变量
@base-sidebar-width: var(--left-menu-max-width, 200px);
@menuBg: var(--left-menu-bg-color, #f6f8fc);
@menuActiveText: var(--left-menu-text-active-color, #1e5eff);
@menuText: var(--left-menu-text-color, #1f2a37);
```

## 2. 侧边栏样式升级

### 2.1 Sidebar/index.vue 样式改造
在 `src/layout/components/Sidebar/index.vue` 中添加：

```vue
<style lang="less" scoped>
.sidebar-container {
  background-color: var(--left-menu-bg-color);
  box-shadow: var(--left-menu-box-shadow);
  transition: width var(--transition-time-02);
  position: relative;
  z-index: 100;
  
  // 重写Element Plus菜单样式
  :deep(.el-menu) {
    border-right: none;
    
    // 菜单项基础样式
    .el-menu-item {
      position: relative;
      background-color: transparent !important;
      
      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: transparent !important;
        
        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: var(--left-menu-active-bar-width);
          background: var(--left-menu-hover-bg-color);
          border-top-right-radius: 8px;
          border-bottom-right-radius: 8px;
          z-index: -1;
        }
      }
    }
    
    // 激活状态样式
    .el-menu-item.is-active {
      color: var(--left-menu-text-active-color) !important;
      background-color: transparent !important;
      
      &::after {
        content: '';
        position: absolute;
        inset: 0;
        left: var(--left-menu-active-bar-width);
        background: var(--left-menu-bg-active-color);
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
        z-index: -1;
      }
      
      // 左侧指示条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-text-active-color);
      }
    }
    
    // 子菜单样式
    .el-sub-menu .el-menu {
      .el-menu-item {
        position: relative;
        
        // 左侧缩进线
        &::before {
          content: '';
          position: absolute;
          left: 16px;
          top: 0;
          bottom: 0;
          width: 2px;
          background-color: var(--left-menu-indent-color);
          z-index: 1;
        }
        
        &.is-active::before {
          background-color: var(--left-menu-text-active-color);
          width: 3px;
        }
      }
    }
  }
}
</style>
```

## 3. 顶部导航栏升级

### 3.1 Navbar.vue 样式改造
在 `src/layout/components/Navbar.vue` 中：

```vue
<template>
  <div class="navbar">
    <!-- 添加返回按钮 -->
    <div class="navbar-left">
      <hamburger 
        v-if="!sidebar.hide"
        id="hamburger-container" 
        :is-active="sidebar.opened" 
        class="hamburger-container" 
        @toggleClick="toggleSideBar" 
      />
      <button 
        v-if="showBackButton" 
        type="button" 
        class="back-button"
        @click="handleBack"
      >
        <svg-icon icon-class="arrow-left" />
        <span>返回</span>
      </button>
      <breadcrumb id="breadcrumb-container" class="breadcrumb-container" />
    </div>
    
    <div class="navbar-right">
      <!-- 工具图标区域... -->
    </div>
  </div>
</template>

<style lang="less" scoped>
.navbar {
  height: var(--top-tool-height);
  background: var(--top-header-bg-color);
  box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--top-tool-p-x, 0);
  
  .navbar-left {
    display: flex;
    align-items: center;
    height: 100%;
    gap: 12px;
  }
  
  .back-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    height: 32px;
    padding: 0 18px;
    border-radius: 0;
    border: 1px solid var(--left-menu-border-color);
    outline: none;
    background: #f3f5f9;
    color: var(--top-header-text-color);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-time-02);
    
    &:hover {
      color: var(--left-menu-text-active-color);
      border-color: var(--left-menu-text-active-color);
      background: rgba(30, 94, 255, 0.08);
    }
  }
  
  .navbar-right {
    display: flex;
    align-items: center;
    height: 100%;
  }
}
</style>
```

## 4. TagsView标签页升级

### 4.1 TagsView/index.vue 样式改造
```vue
<style lang="less" scoped>
.tags-view-container {
  height: var(--tags-view-height);
  background: var(--tags-view-bg-color);
  border-bottom: 1px solid var(--tags-view-border-color);
  box-shadow: var(--tags-view-box-shadow, inset 0 -1px 0 rgba(9, 30, 66, 0.08));
  
  .tags-view-wrapper {
    .tags-view-item {
      position: relative;
      display: inline-flex;
      align-items: center;
      height: calc(var(--tags-view-height) - 1px);
      padding: 0 32px 0 18px;
      font-size: 13px;
      font-weight: 500;
      color: var(--tags-view-text-color);
      background: var(--tags-view-item-bg);
      cursor: pointer;
      border: none;
      border-radius: 0;
      transition: color 0.2s ease, background-color 0.2s ease;
      
      // 底部指示器
      &::after {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 2px;
        background: var(--tags-view-indicator-color);
        content: '';
        transform: scaleX(0);
        transform-origin: center;
        transition: transform 0.2s ease;
      }
      
      // 关闭按钮
      .el-icon-close {
        position: absolute;
        top: 50%;
        right: 10px;
        display: none;
        transform: translate(0, -50%);
        transition: all 0.2s ease;
      }
      
      &:hover {
        color: var(--tags-view-text-active-color);
        background: var(--tags-view-item-hover-bg);
        
        .el-icon-close {
          display: block;
        }
      }
      
      &.active {
        color: var(--tags-view-text-active-color);
        background: var(--tags-view-item-hover-bg);
        
        &::after {
          transform: scaleX(1);
        }
        
        .el-icon-close {
          display: block;
          color: var(--tags-view-text-active-color);
        }
      }
    }
  }
}
</style>
```

## 5. 实施步骤

### Phase 1: 基础设施 (第1周)
1. 创建 `design-tokens.css` CSS变量文件
2. 在 `main.js` 中引入新的变量文件
3. 更新 `variables.module.less` 保持兼容性

### Phase 2: 核心组件升级 (第2-3周)
1. 升级Sidebar组件样式
2. 升级Navbar组件样式  
3. 升级TagsView组件样式
4. 测试各种交互状态

### Phase 3: 细节优化 (第4周)
1. 添加过渡动画
2. 响应式适配
3. 暗色主题支持
4. 浏览器兼容性测试

### Phase 4: 验收测试 (第5周)
1. 视觉还原度检查
2. 交互体验测试
3. 性能影响评估
4. 文档更新

## 6. 注意事项

1. **向后兼容**：保持现有Less变量，逐步迁移
2. **测试覆盖**：每个组件升级后充分测试
3. **性能监控**：关注CSS文件大小和渲染性能
4. **代码审查**：确保代码质量和可维护性

## 7. 预期效果

实施完成后，项目将具备：
- ✅ 现代企业级视觉设计
- ✅ 一致的设计语言系统
- ✅ 流畅的交互动画
- ✅ 专业的用户体验
- ✅ 易于维护的样式架构

通过对齐evaluate-system的设计，你的项目将获得更专业、更现代的视觉表现。