<script lang="tsx">
import { computed, defineComponent, unref, PropType } from 'vue'
import { ElMenu, ElScrollbar } from 'element-plus'
import { useAppStore } from '@/store/modules/app'
import { usePermissionStore } from '@/store/modules/permission'
import { useRenderMenuItem } from './components/useRenderMenuItem'
import { useRouter } from 'vue-router'
import { isUrl } from '@/utils/is'
import { useDesign } from '@/hooks/web/useDesign'

const { getPrefixCls } = useDesign()

const prefixCls = getPrefixCls('menu')

export default defineComponent({
  name: 'Menu',
  props: {
    menuSelect: {
      type: Function as PropType<(index: string) => void>,
      default: undefined
    }
  },
  setup(props) {
    const appStore = useAppStore()

    const layout = computed(() => appStore.getLayout)

    const { push, currentRoute } = useRouter()

    const permissionStore = usePermissionStore()

    const menuMode = computed((): 'vertical' | 'horizontal' => {
      // 竖
      const vertical: LayoutType[] = ['classic', 'topLeft', 'cutMenu']

      if (vertical.includes(unref(layout))) {
        return 'vertical'
      } else {
        return 'horizontal'
      }
    })

    const routers = computed(() =>
      unref(layout) === 'cutMenu' ? permissionStore.getMenuTabRouters : permissionStore.getRouters
    )

    const collapse = computed(() => appStore.getCollapse)

    const uniqueOpened = computed(() => appStore.getUniqueOpened)

    const activeMenu = computed(() => {
      const { meta, path } = unref(currentRoute)
      // if set path, the sidebar will highlight the path you set
      if (meta.activeMenu) {
        return meta.activeMenu as string
      }
      return path
    })

    const menuSelect = (index: string) => {
      if (props.menuSelect) {
        props.menuSelect(index)
      }
      // 自定义事件
      if (isUrl(index)) {
        window.open(index)
      } else {
        push(index)
      }
    }

    const renderMenuWrap = () => {
      if (unref(layout) === 'top') {
        return renderMenu()
      } else {
        return <ElScrollbar class="h-full">{renderMenu()}</ElScrollbar>
      }
    }

    const renderMenu = () => {
      return (
        <ElMenu
          defaultActive={unref(activeMenu)}
          mode={unref(menuMode)}
          collapse={
            unref(layout) === 'top' || unref(layout) === 'cutMenu' ? false : unref(collapse)
          }
          uniqueOpened={unref(layout) === 'top' ? false : unref(uniqueOpened)}
          backgroundColor="var(--left-menu-bg-color)"
          textColor="var(--left-menu-text-color)"
          class="pb-[60px]"
          activeTextColor="var(--left-menu-text-active-color)"
          popperClass={
            unref(menuMode) === 'vertical'
              ? `${prefixCls}-popper--vertical`
              : `${prefixCls}-popper--horizontal`
          }
          onSelect={menuSelect}
        >
          {{
            default: () => {
              const { renderMenuItem } = useRenderMenuItem(menuMode)
              return renderMenuItem(unref(routers))
            }
          }}
        </ElMenu>
      )
    }

    return () => (
      <div
        id={prefixCls}
        class={[
          `${prefixCls} ${prefixCls}__${unref(menuMode)}`,
          'h-[100%] flex flex-col min-h-0 bg-[var(--left-menu-bg-color)]',
          {
            'w-[var(--left-menu-min-width)]': unref(collapse) && unref(layout) !== 'cutMenu',
            'w-[var(--left-menu-max-width)]': !unref(collapse) && unref(layout) !== 'cutMenu'
          }
        ]}
      >
        {renderMenuWrap()}
      </div>
    )
  }
})
</script>

<style lang="less" scoped>
@prefix-cls: ~'@{adminNamespace}-menu';

.@{prefix-cls} {
  position: relative;
  transition: width var(--transition-time-02);
  box-shadow: var(--left-menu-box-shadow);
  z-index: 100;

  :deep(.@{elNamespace}-menu) {
    width: 100% !important;
    border-right: none;

    // 设置父级菜单标题的hover效果
    .@{elNamespace}-sub-menu__title {
      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: #f5f7fa !important;
      }
    }

    // 选中子级时，父级标题保持常规颜色（不高亮）
    .is-active {
      & > .@{elNamespace}-sub-menu__title {
        color: var(--left-menu-text-color) !important;
        background-color: transparent !important;

        &:hover {
          color: var(--left-menu-text-active-color) !important;
          background-color: #f5f7fa !important;
        }
      }
    }

    // 设置一级菜单项的常规与hover效果
    .@{elNamespace}-menu-item {
      position: relative;
      z-index: 0;
      background-color: transparent !important;

      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: transparent !important;

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: var(--left-menu-active-bar-width);
          background: var(--left-menu-hover-bg-color, rgba(28, 100, 242, 0.08));
          border-top-right-radius: 8px;
          border-bottom-right-radius: 8px;
          z-index: -1;
        }
      }
    }

    // 设置选中时的高亮背景和高亮颜色
    .@{elNamespace}-menu-item.is-active {
      color: var(--left-menu-text-active-color) !important;
      position: relative;
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
        box-shadow: var(--left-menu-active-shadow, inset 0 0 0 1px rgba(255, 255, 255, 0.3));
        transition: background 0.25s ease, box-shadow 0.25s ease;
      }

      // 左侧高亮竖条
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: var(--left-menu-active-bar-width);
        background-color: var(--left-menu-text-active-color);
      }

      &:hover {
        background-color: transparent !important;

        &::after {
          background: var(--left-menu-bg-active-color);
          box-shadow: var(--left-menu-active-shadow, inset 0 0 0 1px rgba(255, 255, 255, 0.4));
        }
      }
    }

    // 设置子菜单的样式
    .@{elNamespace}-menu {
      background-color: var(--left-menu-bg-color) !important;

      .@{elNamespace}-sub-menu__title,
      .@{elNamespace}-menu-item {
        position: relative;
        z-index: 0;
        background-color: transparent !important;

        // 左侧缩进指示线
        &::before {
          content: '';
          position: absolute;
          left: 16px;
          top: 0;
          bottom: 0;
          width: 2px;
          background-color: var(--left-menu-indent-color, var(--el-border-color));
          z-index: 1;
        }

        &:hover {
          background-color: transparent !important;

          &::after {
            content: '';
            position: absolute;
            inset: 0;
            left: calc(16px + 2px);
            background: var(--left-menu-hover-bg-color, rgba(28, 100, 242, 0.08));
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            z-index: -1;
          }
        }
      }

      // 子菜单项的 active 状态
      .@{elNamespace}-menu-item.is-active {
        color: var(--left-menu-text-active-color) !important;

        &::before {
          background-color: var(--left-menu-text-active-color);
          width: 3px;
        }

        &::after {
          content: '';
          position: absolute;
          inset: 0;
          left: calc(16px + 3px);
          background: var(--left-menu-bg-active-color);
          border-top-right-radius: 10px;
          border-bottom-right-radius: 10px;
          z-index: -1;
          box-shadow: var(--left-menu-active-shadow, inset 0 0 0 1px rgba(255, 255, 255, 0.3));
          transition: background 0.25s ease, box-shadow 0.25s ease;
        }

        &:hover {
          background-color: transparent !important;
        }
      }
    }
  }

  // 折叠时的最小宽度
  :deep(.@{elNamespace}-menu--collapse) {
    width: var(--left-menu-min-width);

    & > .is-active,
    & > .is-active > .@{elNamespace}-sub-menu__title {
      position: relative;
      background-color: var(--left-menu-collapse-bg-active-color) !important;

      // 折叠状态下的左侧高亮竖条
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
  }

  // 折叠动画的时候，就需要把文字给隐藏掉
  :deep(.horizontal-collapse-transition) {
    .@{prefix-cls}__title {
      display: none;
    }
  }

  // 水平菜单
  &__horizontal {
    height: calc(~'var(--top-tool-height)') !important;

    :deep(.@{elNamespace}-menu--horizontal) {
      height: calc(~'var(--top-tool-height)');
      border-bottom: none;
      // 重新设置底部高亮颜色
      & > .@{elNamespace}-sub-menu.is-active {
        .@{elNamespace}-sub-menu__title {
          border-bottom-color: var(--el-color-primary) !important;
        }
      }

      .@{elNamespace}-menu-item.is-active {
        position: relative;

        &::after {
          display: none !important;
        }
      }

      .@{prefix-cls}__title {
        /* stylelint-disable-next-line */
        max-height: calc(~'var(--top-tool-height) - 2px') !important;
        /* stylelint-disable-next-line */
        line-height: calc(~'var(--top-tool-height) - 2px');
      }
    }
  }
}
</style>

<style lang="less">
@prefix-cls: ~'@{adminNamespace}-menu-popper';

.@{prefix-cls}--vertical,
.@{prefix-cls}--horizontal {
  // 父级菜单标题的hover效果
  .el-sub-menu__title {
    &:hover {
      color: var(--left-menu-text-active-color) !important;
      background-color: #f5f7fa !important;
    }
  }

  // 选中子级时，父级标题保持常规颜色（不高亮）
  .is-active {
    & > .el-sub-menu__title {
      color: var(--left-menu-text-color) !important;
      background-color: transparent !important;

      &:hover {
        color: var(--left-menu-text-active-color) !important;
        background-color: #f5f7fa !important;
      }
    }
  }

  // 菜单项的hover效果
  .el-menu-item {
    &:hover {
      color: var(--left-menu-text-active-color) !important;
      background-color: #f5f7fa !important;
    }
  }

  // 菜单项的选中状态
  .el-menu-item.is-active {
    position: relative;
    background-color: var(--left-menu-bg-active-color) !important;
    color: var(--left-menu-text-active-color) !important;

    // 左侧高亮竖条
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: var(--left-menu-active-bar-width);
      background-color: var(--left-menu-text-active-color);
    }

    &:hover {
      background-color: var(--left-menu-bg-active-color) !important;
    }
  }
}

@submenu-prefix-cls: ~'@{adminNamespace}-submenu-popper';

// 设置子菜单溢出时滚动样式
.@{submenu-prefix-cls}--vertical {
  max-height: 100%;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
    background-color: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: rgb(144 147 153 / 30%);
    border-radius: 4px;
  }
}
</style>
