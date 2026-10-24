<template>
  <div class="vxe-validation-panel" v-if="hasIssues || alwaysShow">
    <!-- 折叠面板模式 -->
    <el-collapse v-model="activeNames" class="validation-collapse">
      <el-collapse-item name="validation">
        <template #title>
          <div class="validation-header">
            <el-icon :class="['header-icon', summaryIconClass]">
              <component :is="summaryIcon" />
            </el-icon>
            <span class="header-title">{{ title || summaryText }}</span>
            <el-badge
              v-if="errorCount > 0"
              :value="errorCount"
              type="danger"
              class="header-badge"
            />
            <el-badge
              v-if="warningCount > 0"
              :value="warningCount"
              type="warning"
              class="header-badge"
            />
          </div>
        </template>

        <div class="validation-content" v-if="hasIssues">
          <div
            v-for="(issue, index) in sortedIssues"
            :key="index"
            :class="['issue-item', `issue-${issue.level}`]"
            @click="handleIssueClick(issue)"
          >
            <el-icon :class="['issue-icon', `icon-${issue.level}`]">
              <component :is="getIcon(issue.level)" />
            </el-icon>
            <div class="issue-body">
              <div class="issue-location">
                <el-tag size="small" type="info" v-if="issue.rowIndex >= 0">
                  第 {{ issue.rowIndex + 1 }} 行
                </el-tag>
                <el-tag size="small" type="info" v-else>全局</el-tag>
                <span class="issue-field">{{ issue.fieldLabel || issue.field }}</span>
              </div>
              <div class="issue-message">{{ issue.message }}</div>
              <div class="issue-suggestion" v-if="issue.suggestion && showSuggestion">
                💡 {{ issue.suggestion }}
              </div>
            </div>
          </div>
        </div>

        <div class="validation-empty" v-else>
          <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
          <span>{{ emptyText }}</span>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import {
  CircleCloseFilled,
  WarningFilled,
  InfoFilled,
  CircleCheckFilled,
} from '@element-plus/icons-vue';
import type { ValidationIssue, ValidationLevel } from './types';

const props = withDefaults(
  defineProps<{
    /** 校验问题列表 */
    issues: ValidationIssue[];
    /** 面板标题 */
    title?: string;
    /** 始终显示面板 */
    alwaysShow?: boolean;
    /** 有问题时自动展开 */
    autoExpand?: boolean;
    /** 显示修复建议 */
    showSuggestion?: boolean;
    /** 空状态文本 */
    emptyText?: string;
    /** 最大高度 */
    maxHeight?: string | number;
  }>(),
  {
    alwaysShow: false,
    autoExpand: true,
    showSuggestion: true,
    emptyText: '校验通过，配置正确',
    maxHeight: 240,
  }
);

const emit = defineEmits<{
  /** 点击问题项 */
  'issue-click': [issue: ValidationIssue];
}>();

const activeNames = ref<string[]>([]);

// 监听问题变化，自动展开
watch(
  () => props.issues,
  (newIssues) => {
    if (props.autoExpand && newIssues.length > 0) {
      activeNames.value = ['validation'];
    }
  },
  { immediate: true }
);

const hasIssues = computed(() => props.issues.length > 0);

const errorCount = computed(() => props.issues.filter((i) => i.level === 'error').length);

const warningCount = computed(() => props.issues.filter((i) => i.level === 'warning').length);

const sortedIssues = computed(() => {
  const levelPriority: Record<ValidationLevel, number> = {
    error: 0,
    warning: 1,
    info: 2,
  };
  return [...props.issues].sort((a, b) => {
    const levelDiff = levelPriority[a.level] - levelPriority[b.level];
    if (levelDiff !== 0) return levelDiff;
    return a.rowIndex - b.rowIndex;
  });
});

const summaryText = computed(() => {
  if (!hasIssues.value) return '校验通过';
  const parts = [];
  if (errorCount.value > 0) parts.push(`${errorCount.value} 个错误`);
  if (warningCount.value > 0) parts.push(`${warningCount.value} 个警告`);
  return `诊断结果：${parts.join('，')}`;
});

const summaryIcon = computed(() => {
  if (errorCount.value > 0) return CircleCloseFilled;
  if (warningCount.value > 0) return WarningFilled;
  return CircleCheckFilled;
});

const summaryIconClass = computed(() => {
  if (errorCount.value > 0) return 'icon-error';
  if (warningCount.value > 0) return 'icon-warning';
  return 'icon-success';
});

const getIcon = (level: ValidationLevel) => {
  const iconMap = {
    error: CircleCloseFilled,
    warning: WarningFilled,
    info: InfoFilled,
  };
  return iconMap[level] || InfoFilled;
};

const handleIssueClick = (issue: ValidationIssue) => {
  emit('issue-click', issue);
};

const contentStyle = computed(() => ({
  maxHeight: typeof props.maxHeight === 'number' ? `${props.maxHeight}px` : props.maxHeight,
}));
</script>

<style lang="less" scoped>
.vxe-validation-panel {
  margin-top: 12px;
  border-radius: 4px;
  overflow: hidden;
}

.validation-collapse {
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;

  :deep(.el-collapse-item__header) {
    padding: 0 12px;
    background: var(--el-fill-color-light);
    height: 40px;
    line-height: 40px;
  }

  :deep(.el-collapse-item__content) {
    padding: 0;
  }
}

.validation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;

  .header-icon {
    font-size: 16px;

    &.icon-error {
      color: var(--el-color-danger);
    }
    &.icon-warning {
      color: var(--el-color-warning);
    }
    &.icon-success {
      color: var(--el-color-success);
    }
  }

  .header-badge {
    margin-left: 4px;
    :deep(.el-badge__content) {
      height: 18px;
      line-height: 18px;
      padding: 0 6px;
    }
  }
}

.validation-content {
  max-height: v-bind('contentStyle.maxHeight');
  overflow-y: auto;
}

.issue-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background 0.2s;

  &:last-child {
    border-bottom: none;
  }
  &:hover {
    background: var(--el-fill-color-light);
  }

  &.issue-error {
    background: var(--el-color-danger-light-9);
    &:hover {
      background: var(--el-color-danger-light-8);
    }
  }

  &.issue-warning {
    background: var(--el-color-warning-light-9);
    &:hover {
      background: var(--el-color-warning-light-8);
    }
  }
}

.issue-icon {
  flex-shrink: 0;
  font-size: 16px;
  margin-right: 10px;
  margin-top: 2px;

  &.icon-error {
    color: var(--el-color-danger);
  }
  &.icon-warning {
    color: var(--el-color-warning);
  }
  &.icon-info {
    color: var(--el-color-info);
  }
}

.issue-body {
  flex: 1;
  min-width: 0;
}

.issue-location {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;

  .issue-field {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.issue-message {
  font-size: 13px;
  color: var(--el-text-color-primary);
  line-height: 1.5;
}

.issue-suggestion {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.validation-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--el-color-success);
  font-size: 14px;

  .success-icon {
    font-size: 20px;
  }
}
</style>
