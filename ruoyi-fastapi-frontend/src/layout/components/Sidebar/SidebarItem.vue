<template>
  <div
    v-if="!item.hidden"
    class="sidebar-entry"
    :class="{ 'is-nested': depth > 0 }"
    :style="{ '--app-nav-level': depth }"
  >
    <template
      v-if="
        hasOneShowingChild(item.children, item) &&
        (!onlyOneChild.children || onlyOneChild.noShowingChildren) &&
        !item.alwaysShow
      "
    >
      <app-link v-if="onlyOneChild.meta" :to="resolvePath(onlyOneChild.path, onlyOneChild.query)">
        <el-menu-item
          :index="resolvePath(onlyOneChild.path)"
          :aria-label="onlyOneChild.meta.title"
          :class="{ 'submenu-title-noDropdown': depth === 0 }"
        >
          <ZxIcon
            :icon="resolveNavigationIcon(onlyOneChild.meta.icon || item.meta?.icon)"
            class="navigation-menu-icon"
            size="var(--app-nav-icon-size)"
            aria-hidden="true"
          />
          <template #title
            ><span class="menu-title" :title="hasTitle(onlyOneChild.meta.title)">{{
              onlyOneChild.meta.title
            }}</span></template
          >
        </el-menu-item>
      </app-link>
    </template>

    <el-sub-menu
      v-else
      ref="subMenu"
      :index="resolvePath(item.path)"
      :aria-label="item.meta?.title"
      :data-sidebar-group="resolvePath(item.path)"
      tabindex="0"
      popper-class="app-sidebar-popper"
      teleported
      @click.capture="activateGroup"
      @keydown.enter.capture="activateGroup"
      @keydown.space.capture="activateGroup"
    >
      <template v-if="item.meta" #title>
        <ZxIcon
          :icon="resolveNavigationIcon(item.meta.icon)"
          class="navigation-menu-icon"
          size="var(--app-nav-icon-size)"
          aria-hidden="true"
        />
        <span class="menu-title" :title="hasTitle(item.meta.title)">{{ item.meta.title }}</span>
      </template>

      <sidebar-item
        v-for="(child, index) in item.children"
        :key="child.path + index"
        :depth="depth + 1"
        :item="child"
        :base-path="resolvePath(child.path)"
        class="nest-menu"
      />
    </el-sub-menu>
  </div>
</template>

<script setup>
import { isExternal } from '@/utils/validate';
import AppLink from './Link';
import { getNormalPath } from '@/utils/ruoyi';
import { ZxIcon } from '@zxio/zxui/core';
import { resolveNavigationIcon } from '@/icons/navigation';

const props = defineProps({
  // route object
  item: {
    type: Object,
    required: true,
  },
  depth: {
    type: Number,
    default: 0,
  },
  basePath: {
    type: String,
    default: '',
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['expand-group']);
const onlyOneChild = ref({});

function activateGroup(event) {
  if (!props.collapsed) {
    if (event.type === 'keydown' && event.target === event.currentTarget) {
      event.preventDefault();
      event.stopPropagation();
      event.currentTarget.querySelector(':scope > .el-sub-menu__title')?.click();
    }
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  emit('expand-group', resolvePath(props.item.path));
}

function hasOneShowingChild(children = [], parent) {
  if (!children) {
    children = [];
  }
  const showingChildren = children.filter((item) => {
    if (item.hidden) {
      return false;
    }
    onlyOneChild.value = item;
    return true;
  });

  // When there is only one child router, the child router is displayed by default
  if (showingChildren.length === 1) {
    return true;
  }

  // Show parent if there are no child router to display
  if (showingChildren.length === 0) {
    onlyOneChild.value = { ...parent, path: '', noShowingChildren: true };
    return true;
  }

  return false;
}

function resolvePath(routePath, routeQuery) {
  if (isExternal(routePath)) {
    return routePath;
  }
  if (isExternal(props.basePath)) {
    return props.basePath;
  }
  if (routeQuery) {
    let query = JSON.parse(routeQuery);
    return {
      path: getNormalPath(props.basePath + '/' + routePath),
      query: query,
    };
  }
  return getNormalPath(props.basePath + '/' + routePath);
}

function hasTitle(title) {
  if (title.length > 5) {
    return title;
  } else {
    return '';
  }
}
</script>
