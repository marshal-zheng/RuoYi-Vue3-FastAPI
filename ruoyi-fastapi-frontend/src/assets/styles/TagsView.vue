<script setup lang="ts">
import { onMounted, watch, computed, unref, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { RouteLocationNormalizedLoaded, RouterLinkProps } from 'vue-router'
import { usePermissionStore } from '@/store/modules/permission'
import { useTagsViewStore } from '@/store/modules/tagsView'
import { useAppStore } from '@/store/modules/app'
import { useI18n } from '@/hooks/web/useI18n'
import { filterAffixTags } from './helper'
import { ContextMenu, ContextMenuExpose } from '@/components/ContextMenu'
import { useDesign } from '@/hooks/web/useDesign'
import { useTemplateRefsList } from '@vueuse/core'
import { ElScrollbar } from 'element-plus'
import { useScrollTo } from '@/hooks/event/useScrollTo'
import { useTagsView } from '@/hooks/web/useTagsView'
import { cloneDeep } from 'lodash-es'

const { getPrefixCls } = useDesign()

const prefixCls = getPrefixCls('tags-view')

const { t } = useI18n()

const { currentRoute, push } = useRouter()

const { closeAll, closeLeft, closeRight, closeOther, closeCurrent, refreshPage } = useTagsView()

const permissionStore = usePermissionStore()

const routers = computed(() => permissionStore.getRouters)

const tagsViewStore = useTagsViewStore()

const visitedViews = computed(() => tagsViewStore.getVisitedViews)

const affixTagArr = ref<RouteLocationNormalizedLoaded[]>([])

const selectedTag = computed(() => tagsViewStore.getSelectedTag)

const setSelectTag = tagsViewStore.setSelectedTag

const appStore = useAppStore()

const tagsViewIcon = computed(() => appStore.getTagsViewIcon)

const isDark = computed(() => appStore.getIsDark)

// 初始化tag
const initTags = () => {
  affixTagArr.value = filterAffixTags(unref(routers))
  for (const tag of unref(affixTagArr)) {
    // Must have tag name
    if (tag.name) {
      tagsViewStore.addVisitedView(cloneDeep(tag))
    }
  }
}

// 新增tag
const addTags = () => {
  const { name } = unref(currentRoute)
  if (name) {
    setSelectTag(unref(currentRoute))
    tagsViewStore.addView(unref(currentRoute))
  }
}

// 关闭选中的tag
const closeSelectedTag = (view: RouteLocationNormalizedLoaded) => {
  closeCurrent(view, () => {
    if (isActive(view)) {
      toLastView()
    }
  })
}

// 去最后一个
const toLastView = () => {
  const visitedViews = tagsViewStore.getVisitedViews
  const latestView = visitedViews.slice(-1)[0]
  if (latestView) {
    push(latestView)
  } else {
    if (
      unref(currentRoute).path === permissionStore.getAddRouters[0].path ||
      unref(currentRoute).path === permissionStore.getAddRouters[0].redirect
    ) {
      addTags()
      return
    }
    // You can set another route
    push(permissionStore.getAddRouters[0].path)
  }
}

// 关闭全部
const closeAllTags = () => {
  closeAll(() => {
    toLastView()
  })
}

// 关闭其它
const closeOthersTags = () => {
  closeOther()
}

// 重新加载
const refreshSelectedTag = async (view?: RouteLocationNormalizedLoaded) => {
  refreshPage(view)
}

// 关闭左侧
const closeLeftTags = () => {
  closeLeft()
}

// 关闭右侧
const closeRightTags = () => {
  closeRight()
}

// 滚动到选中的tag
const moveToCurrentTag = async () => {
  await nextTick()
  for (const v of unref(visitedViews)) {
    if (v.fullPath === unref(currentRoute).path) {
      moveToTarget(v)
      if (v.fullPath !== unref(currentRoute).fullPath) {
        tagsViewStore.updateVisitedView(unref(currentRoute))
      }

      break
    }
  }
}

const tagLinksRefs = useTemplateRefsList<RouterLinkProps>()

const moveToTarget = (currentTag: RouteLocationNormalizedLoaded) => {
  const wrap$ = unref(scrollbarRef)?.wrapRef
  let firstTag: Nullable<RouterLinkProps> = null
  let lastTag: Nullable<RouterLinkProps> = null

  const tagList = unref(tagLinksRefs)
  // find first tag and last tag
  if (tagList.length > 0) {
    firstTag = tagList[0]
    lastTag = tagList[tagList.length - 1]
  }
  if ((firstTag?.to as RouteLocationNormalizedLoaded).fullPath === currentTag.fullPath) {
    // 直接滚动到0的位置
    const { start } = useScrollTo({
      el: wrap$!,
      position: 'scrollLeft',
      to: 0,
      duration: 500
    })
    start()
  } else if ((lastTag?.to as RouteLocationNormalizedLoaded).fullPath === currentTag.fullPath) {
    // 滚动到最后的位置
    const { start } = useScrollTo({
      el: wrap$!,
      position: 'scrollLeft',
      to: wrap$!.scrollWidth - wrap$!.offsetWidth,
      duration: 500
    })
    start()
  } else {
    // find preTag and nextTag
    const currentIndex: number = tagList.findIndex(
      (item) => (item?.to as RouteLocationNormalizedLoaded).fullPath === currentTag.fullPath
    )
    const tgsRefs = document.getElementsByClassName(`${prefixCls}__item`)

    const prevTag = tgsRefs[currentIndex - 1] as HTMLElement
    const nextTag = tgsRefs[currentIndex + 1] as HTMLElement

    // the tag's offsetLeft after of nextTag
    const afterNextTagOffsetLeft = nextTag.offsetLeft + nextTag.offsetWidth + 4

    // the tag's offsetLeft before of prevTag
    const beforePrevTagOffsetLeft = prevTag.offsetLeft - 4

    if (afterNextTagOffsetLeft > unref(scrollLeftNumber) + wrap$!.offsetWidth) {
      const { start } = useScrollTo({
        el: wrap$!,
        position: 'scrollLeft',
        to: afterNextTagOffsetLeft - wrap$!.offsetWidth,
        duration: 500
      })
      start()
    } else if (beforePrevTagOffsetLeft < unref(scrollLeftNumber)) {
      const { start } = useScrollTo({
        el: wrap$!,
        position: 'scrollLeft',
        to: beforePrevTagOffsetLeft,
        duration: 500
      })
      start()
    }
  }
}

// 是否是当前tag
const isActive = (route: RouteLocationNormalizedLoaded): boolean => {
  return route.path === unref(currentRoute).path
}

// 所有右键菜单组件的元素
const itemRefs = useTemplateRefsList<ComponentRef<typeof ContextMenu & ContextMenuExpose>>()

// 右键菜单状态改变的时候
const visibleChange = (visible: boolean, tagItem: RouteLocationNormalizedLoaded) => {
  if (visible) {
    for (const v of unref(itemRefs)) {
      const elDropdownMenuRef = v.elDropdownMenuRef
      if (tagItem.fullPath !== v.tagItem.fullPath) {
        elDropdownMenuRef?.handleClose()
        setSelectTag(tagItem)
      }
    }
  }
}

// elscroll 实例
const scrollbarRef = ref<ComponentRef<typeof ElScrollbar>>()

// 保存滚动位置
const scrollLeftNumber = ref(0)

const scroll = ({ scrollLeft }) => {
  scrollLeftNumber.value = scrollLeft as number
}

// 移动到某个位置
const move = (to: number) => {
  const wrap$ = unref(scrollbarRef)?.wrapRef
  const { start } = useScrollTo({
    el: wrap$!,
    position: 'scrollLeft',
    to: unref(scrollLeftNumber) + to,
    duration: 500
  })
  start()
}

const canShowIcon = (item: RouteLocationNormalizedLoaded) => {
  if (
    (item?.matched?.[1]?.meta?.icon && unref(tagsViewIcon)) ||
    (item?.meta?.affix && unref(tagsViewIcon) && item?.meta?.icon)
  ) {
    return true
  }
  return false
}

onMounted(() => {
  initTags()
  addTags()
})

watch(
  () => currentRoute.value,
  () => {
    addTags()
    moveToCurrentTag()
  }
)
</script>

<template>
  <div
    :id="prefixCls"
    :class="prefixCls"
    class="flex w-full relative bg-[#fff] dark:bg-[var(--el-bg-color)]"
  >
    <span
      :class="`${prefixCls}__tool ${prefixCls}__tool--first`"
      class="w-[var(--tags-view-height)] h-[var(--tags-view-height)] flex items-center justify-center cursor-pointer"
      @click="move(-200)"
    >
      <Icon
        icon="vi-ep:d-arrow-left"
        color="var(--el-text-color-placeholder)"
        :hover-color="isDark ? '#fff' : 'var(--el-color-black)'"
      />
    </span>
    <div class="overflow-hidden flex-1">
      <ElScrollbar ref="scrollbarRef" class="h-full" @scroll="scroll">
        <div class="flex h-full">
          <ContextMenu
            :ref="itemRefs.set"
            :schema="[
              {
                icon: 'vi-ant-design:sync-outlined',
                label: t('common.reload'),
                disabled: selectedTag?.fullPath !== item.fullPath,
                command: () => {
                  refreshSelectedTag(item)
                }
              },
              {
                icon: 'vi-ant-design:close-outlined',
                label: t('common.closeTab'),
                disabled: !!visitedViews?.length && selectedTag?.meta.affix,
                command: () => {
                  closeSelectedTag(item)
                }
              },
              {
                divided: true,
                icon: 'vi-ant-design:vertical-right-outlined',
                label: t('common.closeTheLeftTab'),
                disabled:
                  !!visitedViews?.length &&
                  (item.fullPath === visitedViews[0].fullPath ||
                    selectedTag?.fullPath !== item.fullPath),
                command: () => {
                  closeLeftTags()
                }
              },
              {
                icon: 'vi-ant-design:vertical-left-outlined',
                label: t('common.closeTheRightTab'),
                disabled:
                  !!visitedViews?.length &&
                  (item.fullPath === visitedViews[visitedViews.length - 1].fullPath ||
                    selectedTag?.fullPath !== item.fullPath),
                command: () => {
                  closeRightTags()
                }
              },
              {
                divided: true,
                icon: 'vi-ant-design:tag-outlined',
                label: t('common.closeOther'),
                disabled: selectedTag?.fullPath !== item.fullPath,
                command: () => {
                  closeOthersTags()
                }
              },
              {
                icon: 'vi-ant-design:line-outlined',
                label: t('common.closeAll'),
                command: () => {
                  closeAllTags()
                }
              }
            ]"
            v-for="item in visitedViews"
            :key="item.fullPath"
            :tag-item="item"
            :class="[
              `${prefixCls}__item`,
              item?.meta?.affix ? `${prefixCls}__item--affix` : '',
              {
                'is-active': isActive(item)
              }
            ]"
            @visible-change="visibleChange"
          >
            <div>
              <router-link :ref="tagLinksRefs.set" :to="{ ...item }" custom v-slot="{ navigate }">
                <div
                  :class="`${prefixCls}__item-inner`"
                  role="button"
                  tabindex="0"
                  @click="navigate"
                  @keydown.enter.prevent="navigate"
                >
                  <Icon
                    v-if="canShowIcon(item)"
                    :icon="item?.matched?.[1]?.meta?.icon || item?.meta?.icon"
                    :size="12"
                  />
                  {{ t(item?.meta?.title as string) }}
                  <Icon
                    :class="`${prefixCls}__item--close`"
                    color="#333"
                    icon="vi-ant-design:close-outlined"
                    :size="12"
                    @click.prevent.stop="closeSelectedTag(item)"
                  />
                </div>
              </router-link>
            </div>
          </ContextMenu>
        </div>
      </ElScrollbar>
    </div>
    <span
      :class="`${prefixCls}__tool`"
      class="w-[var(--tags-view-height)] h-[var(--tags-view-height)] flex items-center justify-center cursor-pointer"
      @click="move(200)"
    >
      <Icon
        icon="vi-ep:d-arrow-right"
        color="var(--el-text-color-placeholder)"
        :hover-color="isDark ? '#fff' : 'var(--el-color-black)'"
      />
    </span>
    <span
      :class="`${prefixCls}__tool`"
      class="w-[var(--tags-view-height)] h-[var(--tags-view-height)] flex items-center justify-center cursor-pointer"
      @click="refreshSelectedTag(selectedTag)"
    >
      <Icon
        icon="vi-ant-design:reload-outlined"
        color="var(--el-text-color-placeholder)"
        :hover-color="isDark ? '#fff' : 'var(--el-color-black)'"
      />
    </span>
    <ContextMenu
      trigger="click"
      :schema="[
        {
          icon: 'vi-ant-design:sync-outlined',
          label: t('common.reload'),
          command: () => {
            refreshSelectedTag(selectedTag)
          }
        },
        {
          icon: 'vi-ant-design:close-outlined',
          label: t('common.closeTab'),
          disabled: !!visitedViews?.length && selectedTag?.meta.affix,
          command: () => {
            closeSelectedTag(selectedTag!)
          }
        },
        {
          divided: true,
          icon: 'vi-ant-design:vertical-right-outlined',
          label: t('common.closeTheLeftTab'),
          disabled: !!visitedViews?.length && selectedTag?.fullPath === visitedViews[0].fullPath,
          command: () => {
            closeLeftTags()
          }
        },
        {
          icon: 'vi-ant-design:vertical-left-outlined',
          label: t('common.closeTheRightTab'),
          disabled:
            !!visitedViews?.length &&
            selectedTag?.fullPath === visitedViews[visitedViews.length - 1].fullPath,
          command: () => {
            closeRightTags()
          }
        },
        {
          divided: true,
          icon: 'vi-ant-design:tag-outlined',
          label: t('common.closeOther'),
          command: () => {
            closeOthersTags()
          }
        },
        {
          icon: 'vi-ant-design:line-outlined',
          label: t('common.closeAll'),
          command: () => {
            closeAllTags()
          }
        }
      ]"
    >
      <span
        :class="`${prefixCls}__tool`"
        class="w-[var(--tags-view-height)] h-[var(--tags-view-height)] flex items-center justify-center cursor-pointer block"
      >
        <Icon
          icon="vi-ant-design:setting-outlined"
          color="var(--el-text-color-placeholder)"
          :hover-color="isDark ? '#fff' : 'var(--el-color-black)'"
        />
      </span>
    </ContextMenu>
  </div>
</template>

<style lang="less" scoped>
@prefix-cls: ~'@{adminNamespace}-tags-view';

.@{prefix-cls} {
  background-color: var(--tags-view-bg-color);
  box-shadow: var(--tags-view-box-shadow);
  border-bottom: 1px solid var(--tags-view-border-color);
  z-index: 99;
  
  :deep(.@{elNamespace}-scrollbar__view) {
    height: 100%;
  }

  &__tool {
    position: relative;
    background-color: var(--tags-view-bg-color);
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--tags-view-item-hover-bg);
    }

    &::before {
      position: absolute;
      top: 1px;
      left: 0;
      width: 100%;
      height: calc(~'100% - 1px');
      border-left: 1px solid var(--tags-view-border-color);
      content: '';
    }

    &--first {
      &::before {
        position: absolute;
        top: 1px;
        left: 0;
        width: 100%;
        height: calc(~'100% - 1px');
        border-right: 1px solid var(--tags-view-border-color);
        border-left: none;
        content: '';
      }
    }
  }

  &__item {
    position: relative;
    display: flex;
    align-items: center;
    height: calc(~'var(--tags-view-height) - 1px');
    // margin: 0 10px;
    font-size: 13px;
    font-weight: 500;
    color: var(--tags-view-text-color);
    cursor: pointer;
    border: none;
    border-radius: 0;
    background-color: var(--tags-view-item-bg);
    transition: color 0.2s ease, background-color 0.2s ease;

    &--close {
      position: absolute;
      top: 50%;
      right: 10px;
      display: none;
      transform: translate(0, -50%);
      transition: all 0.2s ease;
    }

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
    
    &:not(.@{prefix-cls}__item--affix):hover {
      .@{prefix-cls}__item--close {
        display: block;
      }
    }
  }

  &__item-inner {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    height: 100%;
    padding: 0 32px 0 18px;
    white-space: nowrap;
    outline: none;

    &:focus-visible {
      color: var(--tags-view-text-active-color);
      background-color: var(--tags-view-item-hover-bg);
    }
  }

  &__item:not(.is-active):hover {
    color: var(--tags-view-text-active-color);
    background-color: var(--tags-view-item-hover-bg);
  }

  &__item.is-active {
    color: var(--tags-view-text-active-color);
    background-color: rgba(30, 94, 255, 0.08);
    
    &::after {
      transform: scaleX(1);
    }

    .@{prefix-cls}__item--close {
      :deep(svg) {
        color: var(--tags-view-text-active-color) !important;
      }
    }
  }
}

.dark {
  .@{prefix-cls} {
    background-color: var(--el-bg-color);

    &__tool {
      background-color: var(--el-bg-color);
      
      &--first {
        &::after {
          display: none;
        }
      }
    }

    &__item {
      color: var(--el-text-color-primary);
      background-color: transparent;
    }

    &__item:not(.is-active) {
      &:hover {
        color: var(--el-color-primary-light-5);
        background-color: rgba(0, 82, 217, 0.12);
      }
    }

    &__item.is-active {
      color: var(--el-color-primary-light-5);
      background-color: rgba(0, 82, 217, 0.16);
      
      .@{prefix-cls}__item--close {
        :deep(svg) {
          color: var(--el-color-primary-light-5) !important;
        }
      }
    }
  }
}
</style>
