<template>
  <div 
    id="tags-view-container" 
    class="flex items-center h-8 w-full shadow-sm"
    style="background: var(--tags-bg, #fff); 
           border-bottom: 1px solid var(--tags-item-border, #d8dce5);"
  >
    <!-- 标签滚动区域 -->
    <div class="flex-1 overflow-hidden">
      <scroll-pane 
        ref="scrollPaneRef" 
        class="h-full" 
        @scroll="handleScroll"
      >
        <router-link
          v-for="tag in visitedViews"
          :key="tag.path"
          :data-path="tag.path"
          :class="[
            'inline-flex items-center relative h-6 px-2 mx-1 first:ml-4 last:mr-4',
            'border rounded text-xs cursor-pointer no-underline whitespace-nowrap',
            'transition-all duration-200 ease-in-out hover:shadow-sm hover:-translate-y-px',
            isActive(tag) ? 'text-white border-transparent shadow-sm' : ''
          ]"
          @mouseenter="e => {
            if (!isActive(tag)) {
              e.target.style.backgroundColor = 'var(--tags-item-hover, #f5f7fa)'
            }
          }"
          @mouseleave="e => {
            if (!isActive(tag)) {
              e.target.style.backgroundColor = 'var(--tags-item-bg, #fff)'
            }
          }"
          :style="isActive(tag) ? { 
            background: theme, 
            borderColor: theme,
            color: '#fff'
          } : {
            color: 'var(--tags-item-text, #495060)',
            background: 'var(--tags-item-bg, #fff)',
            borderColor: 'var(--tags-item-border, #d8dce5)'
          }"
          :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"
          @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"
          @dblclick="!isAffix(tag) ? closeSelectedTag(tag) : ''"
          :title="tag.title.length > 10 ? tag.title : ''"
        >
          <span 
            v-if="isActive(tag)" 
            class="inline-block w-2 h-2 bg-white rounded-full mr-1 
                   animate-pulse"
          ></span>
          <span class="flex-1 overflow-hidden text-ellipsis">
            {{ tag.title }}
          </span>
          <span 
            v-if="!isAffix(tag)" 
            @click.prevent.stop="closeSelectedTag(tag)" 
            class="flex items-center justify-center w-4 h-4 ml-1 
                   rounded-full opacity-60 hover:opacity-100 
                   transition-all duration-200 group"
            :style="isActive(tag) ? {
              color: '#fff'
            } : {
              color: 'var(--tags-item-text, #495060)'
            }"
            @mouseenter="e => {
              if (isActive(tag)) {
                e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
              } else {
                e.target.style.backgroundColor = 'var(--tags-close-hover, rgba(0, 0, 0, 0.1))'
              }
            }"
            @mouseleave="e => {
              e.target.style.backgroundColor = 'transparent'
            }"
          >
            <Close class="w-3 h-3" />
          </span>
        </router-link>
      </scroll-pane>
    </div>
    
    <!-- 右侧操作区域 -->
    <div 
      class="flex items-center gap-1 px-3"
      style="border-left: 1px solid var(--tags-item-border, #d8dce5);"
    >
      <!-- 刷新当前页面按钮 -->
      <div 
        class="flex items-center justify-center w-6 h-6 rounded cursor-pointer 
               transition-all duration-200" 
        style="color: var(--tags-item-text, #495060);"
        @click="refreshSelectedTag($route)" 
        @mouseenter="e => {
          e.target.style.color = 'var(--el-color-primary, #409eff)'
          e.target.style.backgroundColor = 'var(--tags-item-hover, #f5f7fa)'
        }"
        @mouseleave="e => {
          e.target.style.color = 'var(--tags-item-text, #495060)'
          e.target.style.backgroundColor = 'transparent'
        }"
        title="刷新当前页面 (Ctrl+R)"
      >
        <el-icon class="text-sm"><RefreshRight /></el-icon>
      </div>
      
      <!-- 更多操作下拉菜单 -->
      <el-dropdown trigger="click" @command="handleCommand">
        <div 
          class="flex items-center justify-center w-6 h-6 rounded cursor-pointer 
                 transition-all duration-200" 
          style="color: var(--tags-item-text, #495060);"
          @mouseenter="e => {
            e.target.style.color = 'var(--el-color-primary, #409eff)'
            e.target.style.backgroundColor = 'var(--tags-item-hover, #f5f7fa)'
          }"
          @mouseleave="e => {
            e.target.style.color = 'var(--tags-item-text, #495060)'
            e.target.style.backgroundColor = 'transparent'
          }"
          title="更多操作"
        >
          <el-icon class="text-sm"><MoreFilled /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="refresh" :icon="RefreshRight">
              刷新页面
            </el-dropdown-item>
            <el-dropdown-item 
              v-if="visitedViews.length > 1"
              command="closeOthers" 
              :icon="CircleClose"
            >
              关闭其他标签
            </el-dropdown-item>
            <el-dropdown-item 
              v-if="!isFirstView()"
              command="closeLeft" 
              :icon="Back"
            >
              关闭左侧标签
            </el-dropdown-item>
            <el-dropdown-item 
              v-if="!isLastView()"
              command="closeRight" 
              :icon="Right"
            >
              关闭右侧标签
            </el-dropdown-item>
            <el-dropdown-item 
              v-if="visitedViews.length > 1"
              command="closeAll" 
              :icon="CircleClose"
            >
              关闭所有标签
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

  </div>
</template>

<script setup>
import { MoreFilled, RefreshRight, CircleClose, Close, Back, Right } from '@element-plus/icons-vue'
import ScrollPane from './ScrollPane'
import { getNormalPath } from '@/utils/ruoyi'
import useTagsViewStore from '@/store/modules/tagsView'
import useSettingsStore from '@/store/modules/settings'
import usePermissionStore from '@/store/modules/permission'

const affixTags = ref([]);
const scrollPaneRef = ref(null);

const { proxy } = getCurrentInstance();
const route = useRoute();
const router = useRouter();

const visitedViews = computed(() => useTagsViewStore().visitedViews);
const routes = computed(() => usePermissionStore().routes);
const theme = computed(() => useSettingsStore().theme);

watch(route, () => {
  addTags()
  moveToCurrentTag()
})

onMounted(() => {
  initTags()
  addTags()
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})

function isActive(r) {
  return r.path === route.path
}
function activeStyle(tag) {
  if (!isActive(tag)) return {};
  return {
    "background-color": theme.value,
    "border-color": theme.value
  };
}
function isAffix(tag) {
  return tag.meta && tag.meta.affix
}
function isFirstView(view) {
  try {
    const target = view || { fullPath: route.fullPath }
    return target.fullPath === '/index' || target.fullPath === visitedViews.value[1]?.fullPath
  } catch (err) {
    return false
  }
}
function isLastView(view) {
  try {
    const target = view || { fullPath: route.fullPath }
    return target.fullPath === visitedViews.value[visitedViews.value.length - 1]?.fullPath
  } catch (err) {
    return false
  }
}
function filterAffixTags(routes, basePath = '') {
  let tags = []
  routes.forEach(route => {
    if (route.meta && route.meta.affix) {
      const tagPath = getNormalPath(basePath + '/' + route.path)
      tags.push({
        fullPath: tagPath,
        path: tagPath,
        name: route.name,
        meta: { ...route.meta }
      })
    }
    if (route.children) {
      const tempTags = filterAffixTags(route.children, route.path)
      if (tempTags.length >= 1) {
        tags = [...tags, ...tempTags]
      }
    }
  })
  return tags
}
function initTags() {
  const res = filterAffixTags(routes.value);
  affixTags.value = res;
  for (const tag of res) {
    // Must have tag name
    if (tag.name) {
       useTagsViewStore().addVisitedView(tag)
    }
  }
}
function addTags() {
  const { name } = route
  if (name) {
    useTagsViewStore().addView(route)
  }
}
function moveToCurrentTag() {
  nextTick(() => {
    for (const r of visitedViews.value) {
      if (r.path === route.path) {
        scrollPaneRef.value.moveToTarget(r);
        // when query is different then update
        if (r.fullPath !== route.fullPath) {
          useTagsViewStore().updateVisitedView(route)
        }
      }
    }
  })
}
function refreshSelectedTag(view) {
  proxy.$tab.refreshPage(view);
  if (route.meta.link) {
    useTagsViewStore().delIframeView(route);
  }
}
function closeSelectedTag(view) {
  // 添加关闭动画
  const tagElement = document.querySelector(`[data-path="${view.path}"]`)
  if (tagElement) {
    tagElement.style.transform = 'scale(0.8)'
    tagElement.style.opacity = '0'
    
    setTimeout(() => {
      proxy.$tab.closePage(view).then(({ visitedViews }) => {
        if (isActive(view)) {
          toLastView(visitedViews, view)
        }
      })
    }, 150)
  } else {
    // 如果找不到元素，直接关闭
    proxy.$tab.closePage(view).then(({ visitedViews }) => {
      if (isActive(view)) {
        toLastView(visitedViews, view)
      }
    })
  }
}
function closeRightTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta
  }
  proxy.$tab.closeRightPage(currentTag).then(visitedViews => {
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
function closeLeftTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta
  }
  proxy.$tab.closeLeftPage(currentTag).then(visitedViews => {
    if (!visitedViews.find(i => i.fullPath === route.fullPath)) {
      toLastView(visitedViews)
    }
  })
}
function closeOthersTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta
  }
  proxy.$tab.closeOtherPage(currentTag).then(() => {
    moveToCurrentTag()
  })
}
function closeAllTags(view) {
  proxy.$tab.closeAllPage().then(({ visitedViews }) => {
    if (affixTags.value.some(tag => tag.path === route.path)) {
      return
    }
    toLastView(visitedViews, view)
  })
}
function toLastView(visitedViews, view) {
  const latestView = visitedViews.slice(-1)[0]
  if (latestView) {
    router.push(latestView.fullPath)
  } else {
    // now the default is to redirect to the home page if there is no tags-view,
    // you can adjust it according to your needs.
    if (view.name === 'Dashboard') {
      // to reload home page
      router.replace({ path: '/redirect' + view.fullPath })
    } else {
      router.push('/')
    }
  }
}
function handleScroll() {
  // 滚动时可以添加其他逻辑
}

// 全局快捷键处理
function handleGlobalKeydown(e) {
  // Ctrl+W 关闭当前标签
  if (e.ctrlKey && e.key === 'w') {
    e.preventDefault()
    const currentTag = visitedViews.value.find(tag => tag.path === route.path)
    if (currentTag && !isAffix(currentTag)) {
      closeSelectedTag(currentTag)
    }
  }
  
  // Ctrl+R 刷新当前页面
  if (e.ctrlKey && e.key === 'r') {
    e.preventDefault()
    refreshSelectedTag(route)
  }
  
  // Ctrl+Shift+T 重新打开最近关闭的标签（预留）
  if (e.ctrlKey && e.shiftKey && e.key === 'T') {
    e.preventDefault()
    // TODO: 实现重新打开逻辑
    console.log('重新打开最近关闭的标签')
  }
}

// 处理右侧操作按钮命令
function handleCommand(command) {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta
  }
  
  switch (command) {
    case 'refresh':
      refreshSelectedTag(currentTag)
      break
    case 'closeOthers':
      closeOthersTags()
      break
    case 'closeLeft':
      closeLeftTags()
      break
    case 'closeRight':
      closeRightTags()
      break
    case 'closeAll':
      closeAllTags(currentTag)
      break
  }
}
</script>

