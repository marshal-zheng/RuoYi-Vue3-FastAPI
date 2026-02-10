<script setup lang="ts">
import { ElCard, ElDescriptions, ElDescriptionsItem, ElSkeleton, ElTooltip } from 'element-plus';
import { propTypes } from '@/utils/propTypes';
import { computed, useSlots, type VNode } from 'vue';

const slots = useSlots();

interface DetailItem {
  label: string;
  value?: any;
  prop?: string;
  span?: number;
  render?: (item: DetailItem) => VNode | string;
  [key: string]: any;
}

const props = defineProps({
  title: propTypes.string.def(''),
  message: propTypes.string.def(''),
  // 是否固定头部
  fixedHeader: propTypes.bool.def(true),
  // 是否显示头部底部边框
  showHeaderBorder: propTypes.bool.def(true),
  // 是否显示分隔线 (divider)
  showDivider: propTypes.bool.def(true),
  // 头部布局类型: compact(紧凑型) | normal(正常型)
  headerType: propTypes.oneOf(['compact', 'normal']).def('compact'),
  // 头部内边距控制
  headerPadding: propTypes.string.def('0 20px 20px 20px'),
  // 详情数据
  data: {
    type: Array as () => DetailItem[],
    default: () => [],
  },
  // Descriptions 配置
  column: propTypes.number.def(3),
  border: propTypes.bool.def(false),
  // 内容最小高度
  minHeight: propTypes.string.def('400px'),
  // 加载状态
  loading: propTypes.bool.def(false),
  // skeleton 配置
  skeletonRows: propTypes.number.def(8),
  skeletonAnimated: propTypes.bool.def(true),
});

// 判断是否有 header slot
const hasHeaderSlot = computed(() => !!slots.header);

// 判断是否有数据
const hasData = computed(() => props.data && props.data.length > 0);
</script>

<template>
  <div class="content-detail-wrap">
    <ElCard class="content-detail-wrap__body" shadow="never">
      <ElSkeleton :loading="loading" :animated="skeletonAnimated" :rows="skeletonRows">
        <template #default>
          <!-- 固定头部 -->
          <div
            v-if="hasHeaderSlot || hasData"
            :class="[
              'content-detail-wrap__header',
              {
                'content-detail-wrap__header--fixed': fixedHeader,
                'content-detail-wrap__header--no-border': !showHeaderBorder,
                'content-detail-wrap__header--no-divider': !showDivider,
                'content-detail-wrap__header--compact': headerType === 'compact',
                'content-detail-wrap__header--normal': headerType === 'normal',
              },
            ]"
            :style="{ padding: headerPadding }"
          >
            <!-- 自定义 header slot -->
            <slot v-if="hasHeaderSlot" name="header"></slot>

            <!-- 紧凑型布局 -->
            <div
              v-else-if="headerType === 'compact' && hasData"
              class="content-detail-wrap__header-compact"
            >
              <div class="content-detail-wrap__header-compact-grid">
                <div
                  v-for="(item, index) in data"
                  :key="index"
                  class="content-detail-wrap__header-compact-item"
                >
                  <span class="content-detail-wrap__header-compact-label">{{ item.label }}:</span>
                  <span class="content-detail-wrap__header-compact-value">
                    <component
                      :is="item.render ? item.render(item) : item.value"
                      v-if="item.render"
                    />
                    <ElTooltip
                      v-else
                      :content="String(item.value ?? '')"
                      placement="top"
                      effect="light"
                      :show-after="300"
                      :disabled="!item.value || String(item.value).length < 20"
                      popper-class="content-detail-wrap-tooltip"
                    >
                      <span class="content-detail-wrap__header-compact-value-text">
                        {{ item.value }}
                      </span>
                    </ElTooltip>
                  </span>
                </div>
              </div>
            </div>

            <!-- 正常型布局 (使用 Descriptions) -->
            <ElDescriptions
              v-else-if="headerType === 'normal' && hasData"
              :column="column"
              :border="border"
            >
              <ElDescriptionsItem
                v-for="(item, index) in data"
                :key="index"
                :label="item.label"
                :span="item.span || 1"
              >
                <component :is="item.render ? item.render(item) : item.value" v-if="item.render" />
                <template v-else>{{ item.value }}</template>
              </ElDescriptionsItem>
            </ElDescriptions>
          </div>

          <!-- 内容区域 -->
          <div
            :class="[
              'content-detail-wrap__content',
              {
                'content-detail-wrap__content--with-header':
                  fixedHeader && (hasHeaderSlot || hasData),
              },
            ]"
            :style="{ minHeight }"
          >
            <slot name="body">
              <slot></slot>
            </slot>
          </div>
        </template>
      </ElSkeleton>
    </ElCard>
  </div>
</template>

<style lang="less" scoped>
.content-detail-wrap {
  position: relative;
  width: 100%;
  height: 100%;

  &__body {
    position: relative;
    overflow: visible;
  }

  &__header {
    background: var(--el-bg-color);
    z-index: 10;
    padding: 0 20px 20px 20px;

    &--fixed {
      position: sticky;
      top: 0;
      padding: 0 20px 20px 20px;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--el-border-color);

      &.content-detail-wrap__header--no-border {
        border-bottom: none;
      }

      &.content-detail-wrap__header--no-divider {
        border-bottom: none;
        margin-bottom: 0;
      }
    }

    &--compact {
      .content-detail-wrap__header-compact {
        &-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 12px 24px;
        }

        &-item {
          display: flex;
          align-items: center;
          font-size: 14px;
          line-height: 22px;
          min-width: 0;
        }

        &-label {
          color: var(--el-text-color-secondary);
          margin-right: 8px;
          flex-shrink: 0;
        }

        &-value {
          color: var(--el-text-color-primary);
          flex: 1;
          min-width: 0;
        }

        &-value-text {
          display: inline-block;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 100%;
          vertical-align: bottom;
        }
      }
    }

    &--normal {
      :deep(.el-descriptions) {
        .el-descriptions__label {
          color: var(--el-text-color-secondary);
        }

        .el-descriptions__content {
          color: var(--el-text-color-primary);
        }
      }
    }
  }

  &__content {
    &--with-header {
      padding-top: 0;
    }
  }
}

// Tooltip 样式
:deep(.content-detail-wrap-tooltip) {
  max-width: 400px;
  word-break: break-all;
}
</style>
