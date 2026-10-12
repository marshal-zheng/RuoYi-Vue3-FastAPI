<template>
  <!-- Background 插件不需要渲染内容 -->
</template>

<script setup>
import { watch } from 'vue';
import { useGraphTheme } from '../composables/useGraphTheme';
import { useGraphInstance } from '../composables/useGraphInstance';

// Props 定义
const props = defineProps({
  color: {
    type: String,
    default: undefined,
  },
  image: {
    type: String,
    default: '',
  },
  position: {
    type: String,
    default: 'center',
  },
  size: {
    type: String,
    default: 'auto auto',
  },
  repeat: {
    type: String,
    default: 'no-repeat',
  },
  opacity: {
    type: Number,
    default: 1,
  },
});

const graph = useGraphInstance();
const palette = useGraphTheme();

// 更新背景
const updateBackground = () => {
  if (!graph?.value || (!props.color && !palette.value)) return;

  const backgroundOptions = {
    color: props.color ?? palette.value?.background,
    opacity: props.opacity,
  };

  if (props.image) {
    backgroundOptions.image = props.image;
    backgroundOptions.position = props.position;
    backgroundOptions.size = props.size;
    backgroundOptions.repeat = props.repeat;
  }

  graph.value.drawBackground(backgroundOptions);
};

watch(
  () => [
    graph?.value,
    palette.value,
    props.color,
    props.image,
    props.position,
    props.size,
    props.repeat,
    props.opacity,
  ],
  updateBackground,
  { immediate: true, flush: 'post' }
);
</script>
