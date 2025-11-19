<template>
  <div
    id="tags-view-container"
    class="flex items-center h-10 w-full relative border-b border-gray-200"
    style="background-color: #f3f5f9"
  >
    <!-- 标签滚动区域 -->
    <div class="flex-1 overflow-hidden">
      <scroll-pane ref="scrollPaneRef" class="h-full" @scroll="handleScroll">
        <router-link
          v-for="tag in visitedViews"
          :key="tag.path"
          :data-path="tag.path"
          :class="[
            'tags-view-item',
            'relative inline-flex items-center h-full px-4',
            'text-[13px] font-medium cursor-pointer no-underline whitespace-nowrap',
            'text-gray-600 bg-transparent',
            'transition-colors duration-200',
            isActive(tag) ? 'is-active' : 'hover:text-blue-600 hover:bg-blue-50/50',
            isAffix(tag) ? 'tags-view-item--affix' : '',
          ]"
          :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"
          @click.middle="!isAffix(tag) ? closeSelectedTag(tag) : ''"
          @dblclick="!isAffix(tag) ? closeSelectedTag(tag) : ''"
          :title="tag.title.length > 10 ? tag.title : ''"
        >
          <span class="inline-flex items-center whitespace-nowrap mr-2">
            {{ tag.title }}
          </span>
          <zx-icon
            v-if="!isAffix(tag)"
            icon="Close"
            class="tags-view-item__close absolute top-1/2 right-2.5 -translate-y-1/2 hidden cursor-pointer transition-opacity duration-200"
            :size="12"
            @click.prevent.stop="closeSelectedTag(tag)"
          />
        </router-link>
      </scroll-pane>
    </div>

    <!-- 右侧操作区域 -->
    <div class="flex items-center h-full border-l border-gray-200">
      <!-- 刷新当前页面按钮 -->
      <div
        class="tags-view-tool relative flex items-center justify-center w-10 h-full cursor-pointer text-gray-500 hover:text-blue-600 hover:bg-blue-50/50 transition-colors duration-200"
        @click="refreshSelectedTag($route)"
        title="刷新当前页面 (Ctrl+R)"
      >
        <zx-icon icon="RefreshRight" :size="14" />
      </div>

      <!-- 更多操作下拉菜单 -->
      <el-dropdown trigger="click" @command="handleCommand">
        <div
          class="tags-view-tool relative flex items-center justify-center w-10 h-full cursor-pointer text-gray-500 hover:text-blue-600 hover:bg-blue-50/50 transition-colors duration-200"
          title="更多操作"
        >
          <zx-icon icon="MoreFilled" :size="14" />
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="refresh" :icon="RefreshRight"> 刷新页面 </el-dropdown-item>
            <el-dropdown-item
              v-if="visitedViews.length > 1"
              command="closeOthers"
              :icon="CircleClose"
            >
              关闭其他标签
            </el-dropdown-item>
            <el-dropdown-item v-if="!isFirstView()" command="closeLeft" :icon="Back">
              关闭左侧标签
            </el-dropdown-item>
            <el-dropdown-item v-if="!isLastView()" command="closeRight" :icon="Right">
              关闭右侧标签
            </el-dropdown-item>
            <el-dropdown-item v-if="visitedViews.length > 1" command="closeAll" :icon="CircleClose">
              关闭所有标签
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { RefreshRight, CircleClose, Back, Right } from '@element-plus/icons-vue';
import ScrollPane from './ScrollPane';
import { getNormalPath } from '@/utils/ruoyi';
import useTagsViewStore from '@/store/modules/tagsView';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';

const affixTags = ref([]);
const scrollPaneRef = ref(null);

const { proxy } = getCurrentInstance();
const route = useRoute();
const router = useRouter();

const visitedViews = computed(() => useTagsViewStore().visitedViews);
const routes = computed(() => usePermissionStore().routes);
const theme = computed(() => useSettingsStore().theme);

watch(route, () => {
  addTags();
  moveToCurrentTag();
});

onMounted(() => {
  initTags();
  addTags();
  document.addEventListener('keydown', handleGlobalKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown);
});

function isActive(r) {
  return r.path === route.path;
}
function isAffix(tag) {
  return tag.meta && tag.meta.affix;
}
function isFirstView(view) {
  const target = view || { fullPath: route.fullPath };
  return target.fullPath === '/index' || target.fullPath === visitedViews.value[1]?.fullPath;
}
function isLastView(view) {
  const target = view || { fullPath: route.fullPath };
  return target.fullPath === visitedViews.value[visitedViews.value.length - 1]?.fullPath;
}
function filterAffixTags(routes, basePath = '') {
  let tags = [];
  routes.forEach((route) => {
    if (route.meta && route.meta.affix) {
      const tagPath = getNormalPath(basePath + '/' + route.path);
      tags.push({
        fullPath: tagPath,
        path: tagPath,
        name: route.name,
        meta: { ...route.meta },
      });
    }
    if (route.children) {
      const tempTags = filterAffixTags(route.children, route.path);
      if (tempTags.length >= 1) {
        tags = [...tags, ...tempTags];
      }
    }
  });
  return tags;
}
function initTags() {
  const res = filterAffixTags(routes.value);
  affixTags.value = res;
  for (const tag of res) {
    // Must have tag name
    if (tag.name) {
      useTagsViewStore().addVisitedView(tag);
    }
  }
}
function addTags() {
  const { name } = route;
  if (name) {
    useTagsViewStore().addView(route);
  }
}
function moveToCurrentTag() {
  nextTick(() => {
    for (const r of visitedViews.value) {
      if (r.path === route.path) {
        scrollPaneRef.value.moveToTarget(r);
        // when query is different then update
        if (r.fullPath !== route.fullPath) {
          useTagsViewStore().updateVisitedView(route);
        }
      }
    }
  });
}
function refreshSelectedTag(view) {
  proxy.$tab.refreshPage(view);
  if (route.meta.link) {
    useTagsViewStore().delIframeView(route);
  }
}
function closeSelectedTag(view) {
  proxy.$tab.closePage(view).then(({ visitedViews }) => {
    if (isActive(view)) {
      toLastView(visitedViews, view);
    }
  });
}
function closeRightTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta,
  };
  proxy.$tab.closeRightPage(currentTag).then((visitedViews) => {
    if (!visitedViews.find((i) => i.fullPath === route.fullPath)) {
      toLastView(visitedViews);
    }
  });
}
function closeLeftTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta,
  };
  proxy.$tab.closeLeftPage(currentTag).then((visitedViews) => {
    if (!visitedViews.find((i) => i.fullPath === route.fullPath)) {
      toLastView(visitedViews);
    }
  });
}
function closeOthersTags() {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta,
  };
  proxy.$tab.closeOtherPage(currentTag).then(() => {
    moveToCurrentTag();
  });
}
function closeAllTags(view) {
  proxy.$tab.closeAllPage().then(({ visitedViews }) => {
    if (affixTags.value.some((tag) => tag.path === route.path)) {
      return;
    }
    toLastView(visitedViews, view);
  });
}
function toLastView(visitedViews, view) {
  const latestView = visitedViews.slice(-1)[0];
  if (latestView) {
    router.push(latestView.fullPath);
  } else {
    // now the default is to redirect to the home page if there is no tags-view,
    // you can adjust it according to your needs.
    if (view.name === 'Dashboard') {
      // to reload home page
      router.replace({ path: '/redirect' + view.fullPath });
    } else {
      router.push('/');
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
    e.preventDefault();
    const currentTag = visitedViews.value.find((tag) => tag.path === route.path);
    if (currentTag && !isAffix(currentTag)) {
      closeSelectedTag(currentTag);
    }
  }

  // Ctrl+R 刷新当前页面
  if (e.ctrlKey && e.key === 'r') {
    e.preventDefault();
    refreshSelectedTag(route);
  }

  // Ctrl+Shift+T 重新打开最近关闭的标签（预留）
  if (e.ctrlKey && e.shiftKey && e.key === 'T') {
    e.preventDefault();
    // TODO: 实现重新打开逻辑
  }
}

// 处理右侧操作按钮命令
function handleCommand(command) {
  const currentTag = {
    path: route.path,
    query: route.query,
    fullPath: route.fullPath,
    name: route.name,
    meta: route.meta,
  };

  switch (command) {
    case 'refresh':
      refreshSelectedTag(currentTag);
      break;
    case 'closeOthers':
      closeOthersTags();
      break;
    case 'closeLeft':
      closeLeftTags();
      break;
    case 'closeRight':
      closeRightTags();
      break;
    case 'closeAll':
      closeAllTags(currentTag);
      break;
  }
}
</script>

<style scoped>
/* 底部指示器 */
.tags-view-item::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: v-bind(theme);
  transform: scaleX(0);
  transform-origin: center;
  transition: transform 0.2s ease;
}

/* 关闭按钮基础样式 */
.tags-view-item__close {
  color: #9ca3af;
}

/* hover 时显示关闭按钮 */
.tags-view-item:not(.tags-view-item--affix):hover .tags-view-item__close {
  display: block !important;
}

.tags-view-item__close:hover {
  color: #6b7280 !important;
  opacity: 1 !important;
}

/* 激活状态 */
.tags-view-item.is-active {
  color: v-bind(theme) !important;
  /* background-color: #ffffff !important; */
}

.tags-view-item.is-active::after {
  transform: scaleX(1);
}

/* 激活状态的关闭按钮 */
.tags-view-item.is-active .tags-view-item__close {
  display: block !important;
  color: v-bind(theme) !important;
}

.tags-view-item.is-active .tags-view-item__close:hover {
  opacity: 0.7 !important;
}

/* 工具按钮左边框 */
.tags-view-tool::before {
  content: '';
  position: absolute;
  top: 1px;
  left: 0;
  width: 100%;
  height: calc(100% - 1px);
  border-left: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  #tags-view-container {
    height: 2.25rem;
  }

  .tags-view-item {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
    font-size: 0.75rem;
  }

  .tags-view-tool {
    width: 2rem;
  }
}
</style>
