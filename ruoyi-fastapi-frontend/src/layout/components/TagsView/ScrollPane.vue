<template>
  <div class="scroll-container" ref="scrollContainer">
    <div
      class="scroll-wrapper"
      ref="scrollWrapper"
      @wheel.prevent="handleScroll"
      @scroll="emitScroll"
    >
      <div class="tags-content" ref="tagsContent">
        <slot />
      </div>
    </div>
    <!-- 左右滚动按钮 -->
    <div v-show="showLeftButton" class="scroll-button scroll-button-left" @click="scrollToLeft">
      <el-icon><ArrowLeft /></el-icon>
    </div>
    <div v-show="showRightButton" class="scroll-button scroll-button-right" @click="scrollToRight">
      <el-icon><ArrowRight /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue';
import useTagsViewStore from '@/store/modules/tagsView';

const tagAndTagSpacing = ref(4);
const { proxy } = getCurrentInstance();

const scrollContainer = ref(null);
const scrollWrapper = ref(null);
const tagsContent = ref(null);
const showLeftButton = ref(false);
const showRightButton = ref(false);

onMounted(() => {
  updateScrollButtons();
  // 监听窗口大小变化
  window.addEventListener('resize', updateScrollButtons);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateScrollButtons);
});

// 更新滚动按钮显示状态
function updateScrollButtons() {
  if (!scrollWrapper.value || !tagsContent.value) return;

  const wrapper = scrollWrapper.value;
  const content = tagsContent.value;

  showLeftButton.value = wrapper.scrollLeft > 0;
  showRightButton.value = wrapper.scrollLeft < content.scrollWidth - wrapper.clientWidth;
}

function handleScroll(e) {
  const eventDelta = e.wheelDelta || -e.deltaY * 40;
  const wrapper = scrollWrapper.value;
  if (!wrapper) return;

  wrapper.scrollLeft = wrapper.scrollLeft - eventDelta / 4;
  updateScrollButtons();
}

// 左滚动按钮
function scrollToLeft() {
  const wrapper = scrollWrapper.value;
  if (!wrapper) return;

  const targetScrollLeft = Math.max(0, wrapper.scrollLeft - 180);
  smoothScrollTo(wrapper, targetScrollLeft);
}

// 右滚动按钮
function scrollToRight() {
  const wrapper = scrollWrapper.value;
  const content = tagsContent.value;
  if (!wrapper || !content) return;

  const targetScrollLeft = Math.min(
    content.scrollWidth - wrapper.clientWidth,
    wrapper.scrollLeft + 180
  );
  smoothScrollTo(wrapper, targetScrollLeft);
}

// 平滑滚动函数
function smoothScrollTo(element, target) {
  const start = element.scrollLeft;
  const distance = target - start;
  const duration = 300;
  let startTime = null;

  function animate(currentTime) {
    if (startTime === null) startTime = currentTime;
    const timeElapsed = currentTime - startTime;
    const run = easeOutCubic(timeElapsed, start, distance, duration);
    element.scrollLeft = run;

    if (timeElapsed < duration) {
      requestAnimationFrame(animate);
    } else {
      element.scrollLeft = target;
      updateScrollButtons();
    }
  }

  function easeOutCubic(t, b, c, d) {
    t /= d;
    t--;
    return c * (t * t * t + 1) + b;
  }

  requestAnimationFrame(animate);
}

const emits = defineEmits(['scroll']);
const emitScroll = () => {
  updateScrollButtons();
  emits('scroll');
};

const tagsViewStore = useTagsViewStore();
const visitedViews = computed(() => tagsViewStore.visitedViews);

function moveToTarget(currentTag) {
  const container = scrollContainer.value;
  const wrapper = scrollWrapper.value;
  const content = tagsContent.value;

  if (!container || !wrapper || !content) return;

  const containerWidth = container.offsetWidth;
  let firstTag = null;
  let lastTag = null;

  // find first tag and last tag
  if (visitedViews.value.length > 0) {
    firstTag = visitedViews.value[0];
    lastTag = visitedViews.value[visitedViews.value.length - 1];
  }

  if (firstTag === currentTag) {
    wrapper.scrollLeft = 0;
  } else if (lastTag === currentTag) {
    wrapper.scrollLeft = content.scrollWidth - containerWidth;
  } else {
    // 查找当前标签的DOM元素
    const currentTagDom = content.querySelector(`[data-path="${currentTag.path}"]`);
    if (!currentTagDom) return;

    const tagRect = currentTagDom.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    // 计算标签相对于容器的位置
    const tagLeft = currentTagDom.offsetLeft;
    const tagWidth = currentTagDom.offsetWidth;

    // 如果标签在可视区域右侧
    if (tagLeft + tagWidth > wrapper.scrollLeft + containerWidth) {
      wrapper.scrollLeft = tagLeft + tagWidth - containerWidth + 20;
    }
    // 如果标签在可视区域左侧
    else if (tagLeft < wrapper.scrollLeft) {
      wrapper.scrollLeft = Math.max(0, tagLeft - 20);
    }
  }

  updateScrollButtons();
}

defineExpose({
  moveToTarget,
});
</script>

<style scoped>
.scroll-container {
  position: relative;
  width: 100%;
  height: 40px;
  overflow: hidden;
}

.scroll-wrapper {
  width: 100%;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;

  /* 隐藏滚动条 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.scroll-wrapper::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}

.tags-content {
  display: flex;
  align-items: center;
  height: 100%;
  white-space: nowrap;
  min-width: 100%;
  padding: 0 8px;
}

.scroll-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  color: #6b7280;
}

.scroll-button:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #374151;
}

.scroll-button:active {
  transform: translateY(-50%) scale(0.95);
}

.scroll-button .el-icon {
  font-size: 14px;
}

.scroll-button-left {
  left: 4px;
}

.scroll-button-right {
  right: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .scroll-container {
    height: 36px;
  }

  .scroll-button {
    width: 20px;
    height: 20px;
  }

  .scroll-button .el-icon {
    font-size: 12px;
  }

  .scroll-button-left {
    left: 2px;
  }

  .scroll-button-right {
    right: 2px;
  }
}
</style>
