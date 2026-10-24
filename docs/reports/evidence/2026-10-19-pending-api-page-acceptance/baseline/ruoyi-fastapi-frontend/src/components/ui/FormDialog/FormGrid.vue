<template>
  <div class="form-grid" :style="layoutStyle"><slot /></div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formLayoutPolicy, type FormColumns } from './policy';

const props = defineProps<{ columns: FormColumns }>();
const layoutStyle = computed(() => ({
  '--form-columns': props.columns,
  '--form-column-gap': formLayoutPolicy.columnGap,
  '--form-column-min-width': formLayoutPolicy.minColumnWidth,
}));
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(
      min(
        100%,
        max(
          var(--form-column-min-width),
          calc((100% - (var(--form-columns) - 1) * var(--form-column-gap)) / var(--form-columns))
        )
      ),
      1fr
    )
  );
  column-gap: var(--form-column-gap);
  min-width: 0;
}
.form-grid > :deep(*) {
  min-width: 0;
}
.form-grid > :deep([data-form-full]) {
  grid-column: 1 / -1;
}
.form-grid :deep(.el-form-item__label) {
  height: auto;
  white-space: normal;
  overflow-wrap: anywhere;
}
.form-grid :deep(.el-form-item__content) {
  min-width: 0;
}
</style>
