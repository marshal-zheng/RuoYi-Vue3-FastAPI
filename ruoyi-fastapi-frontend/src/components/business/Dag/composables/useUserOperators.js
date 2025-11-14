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
        category: item.category || '默认分类',
        ...item // 保留用户的其他自定义字段
      }))
  })

  // 按分类分组
  const categoryGroups = computed(() => {
    const groups = {}
    
    processedOperators.value.forEach(op => {
      const category = op.category
      if (!groups[category]) {
        groups[category] = {
          key: category,
          title: category,
          items: []
        }
      }
      groups[category].items.push(op)
    })

    return Object.values(groups)
  })

  // 统计信息
  const stats = computed(() => ({
    total: processedOperators.value.length,
    categories: categoryGroups.value.length
  }))

  return {
    operators: processedOperators,
    categoryGroups,
    stats,
    generateId
  }
}
