import request from '@/utils/request'

// 查询设备分类列表
export function listDeviceCategory(query) {
  return request({
    url: '/device/category/list',
    method: 'get',
    params: query
  })
}

// 查询设备分类详细
export function getDeviceCategory(categoryId) {
  return request({
    url: '/device/category/' + categoryId,
    method: 'get'
  })
}

// 新增设备分类
export function addDeviceCategory(data) {
  return request({
    url: '/device/category',
    method: 'post',
    data: data
  })
}

// 修改设备分类
export function updateDeviceCategory(data) {
  return request({
    url: '/device/category',
    method: 'put',
    data: data
  })
}

// 删除设备分类
export function delDeviceCategory(categoryId) {
  return request({
    url: '/device/category/' + categoryId,
    method: 'delete'
  })
}

// 导出设备分类数据
export function exportDeviceCategory(query) {
  return request({
    url: '/device/category/export',
    method: 'post',
    params: query,
    responseType: 'blob'
  })
}

// 获取设备分类选项(用于下拉选择)
export function getDeviceCategoryOptions(businessType = '9999') {
  return request({
    url: '/device/category/list',
    method: 'get',
    params: {
      business_type: businessType
    }
  })
}

// 检查分类名称是否唯一
export function checkCategoryNameUnique(name, categoryId) {
  return request({
    url: '/device/category/checkNameUnique',
    method: 'get',
    params: {
      name: name,
      categoryId: categoryId
    }
  })
}
