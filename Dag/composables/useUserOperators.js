import { computed, unref } from 'vue'

/**
 * 通用数据转换 Composable
 * 将简单数据格式转换为组件所需的完整格式
 * @param {Array|Ref<Array>} operators - 数据源 [{name: string, value?: string, category?: string, ...}]
 * @returns {Object} 处理后的数据和工具方法
 */
export function useUserOperators(operators) {
  // 生成唯一ID
  const generateId = (() => {
    let counter = 0
    return (prefix = 'node') => `${prefix}-${Date.now()}-${++counter}`
  })()

  // 标准化数据格式
  const processedOperators = computed(() => {
    const data = unref(operators)
    
    if (!Array.isArray(data) || data.length === 0) {
      return []
    }

    return data
      .filter(item => item && typeof item === 'object' && item.name)
      .map(item => ({
        key: generateId('operator'),
        title: item.name,
        shortDesc: item.value || item.name,
        // 若无分类则保持为空字符串，便于后续判断是否需要展示一级分类
        category: (typeof item.category === 'string' ? item.category : '').trim(),
        originalData: item,
        ...item // 保留用户的其他自定义字段
      }))
  })

  // 是否存在至少一个有分类的项
  const showCategory = computed(() => {
    return processedOperators.value.some(op => op.category && op.category.length > 0)
  })

  // 按分类分组（当存在分类时才分组）
  const categoryGroups = computed(() => {
    if (!showCategory.value) return []

    const groups = {}

    processedOperators.value.forEach(op => {
      const displayCategory = op.category && op.category.length > 0 ? op.category : '未分类'
      if (!groups[displayCategory]) {
        groups[displayCategory] = {
          key: displayCategory,
          title: displayCategory,
          items: []
        }
      }
      groups[displayCategory].items.push(op)
    })

    return Object.values(groups)
  })

  // 统计信息
  const stats = computed(() => ({
    total: processedOperators.value.length,
    categories: categoryGroups.value.length
  }))

  return {
    // 兼容字段
    operators: processedOperators,
    processedOperators,
    categoryGroups,
    showCategory,
    stats,
    generateId
  }
}
