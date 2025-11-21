# API 集成

## Axios 封装

### 请求配置

**文件**: `src/utils/request.ts`

```typescript
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/modules/user'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API,
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 添加 Token
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }
    
    // 添加其他请求头
    config.headers['Content-Type'] = 'application/json;charset=utf-8'
    
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    const code = res.code || 200
    
    // 获取错误信息
    const msg = res.msg || '系统未知错误,请反馈给管理员'
    
    // 二进制数据直接返回
    if (response.request.responseType === 'blob' || response.request.responseType === 'arraybuffer') {
      return res
    }
    
    // 未设置状态码则默认成功状态
    if (code === 200) {
      return res
    } else if (code === 401) {
      // Token 过期
      ElMessageBox.confirm('登录状态已过期,您可以继续留在该页面,或者重新登录', '系统提示', {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        const userStore = useUserStore()
        userStore.logout().then(() => {
          location.href = '/login'
        })
      })
      return Promise.reject('无效的会话,或者会话已过期,请重新登录。')
    } else if (code === 500) {
      ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    } else if (code === 601) {
      ElMessage.warning(msg)
      return Promise.reject(new Error(msg))
    } else if (code !== 200) {
      ElMessage.error(msg)
      return Promise.reject('error')
    }
  },
  (error) => {
    console.error('响应错误:', error)
    let { message } = error
    
    if (message === 'Network Error') {
      message = '后端接口连接异常'
    } else if (message.includes('timeout')) {
      message = '系统接口请求超时'
    } else if (message.includes('Request failed with status code')) {
      message = '系统接口' + message.substr(message.length - 3) + '异常'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
```

## API 模块化

### API 目录结构

```
src/api/
├── login.ts              # 登录相关
├── system/               # 系统管理
│   ├── user.ts          # 用户管理
│   ├── role.ts          # 角色管理
│   ├── menu.ts          # 菜单管理
│   ├── dept.ts          # 部门管理
│   ├── dict.ts          # 字典管理
│   └── config.ts        # 参数配置
├── monitor/              # 系统监控
│   ├── operlog.ts       # 操作日志
│   └── logininfor.ts    # 登录日志
├── project/              # 项目管理
│   └── project.ts
├── protocol/             # 协议管理
│   └── protocol.ts
└── device/               # 设备管理
    └── device.ts
```

### 用户管理 API

**文件**: `src/api/system/user.ts`

```typescript
import request from '@/utils/request'

// 类型定义
export interface UserQuery {
  pageNum: number
  pageSize: number
  userName?: string
  phonenumber?: string
  status?: string
  deptId?: number
  beginTime?: string
  endTime?: string
}

export interface UserForm {
  userId?: number
  userName: string
  nickName: string
  password?: string
  phonenumber?: string
  email?: string
  sex?: string
  status: string
  deptId?: number
  postIds?: number[]
  roleIds?: number[]
  remark?: string
}

export interface UserVO {
  userId: number
  userName: string
  nickName: string
  email?: string
  phonenumber?: string
  sex?: string
  avatar?: string
  status: string
  delFlag: string
  loginIp?: string
  loginDate?: string
  createBy?: string
  createTime?: string
  updateBy?: string
  updateTime?: string
  remark?: string
  dept?: any
  roles?: any[]
}

// 查询用户列表
export function listUser(query: UserQuery) {
  return request({
    url: '/system/user/list',
    method: 'get',
    params: query
  })
}

// 查询用户详细
export function getUser(userId: number) {
  return request({
    url: '/system/user/' + userId,
    method: 'get'
  })
}

// 新增用户
export function addUser(data: UserForm) {
  return request({
    url: '/system/user',
    method: 'post',
    data: data
  })
}

// 修改用户
export function updateUser(data: UserForm) {
  return request({
    url: '/system/user',
    method: 'put',
    data: data
  })
}

// 删除用户
export function delUser(userIds: number | number[]) {
  return request({
    url: '/system/user/' + userIds,
    method: 'delete'
  })
}

// 重置密码
export function resetUserPwd(userId: number, password: string) {
  return request({
    url: '/system/user/resetPwd',
    method: 'put',
    params: { userId, password }
  })
}

// 用户状态修改
export function changeUserStatus(userId: number, status: string) {
  return request({
    url: '/system/user/changeStatus',
    method: 'put',
    params: { userId, status }
  })
}

// 查询用户个人信息
export function getUserProfile() {
  return request({
    url: '/system/user/profile',
    method: 'get'
  })
}

// 修改用户个人信息
export function updateUserProfile(data: any) {
  return request({
    url: '/system/user/profile',
    method: 'put',
    data: data
  })
}

// 用户密码重置
export function updateUserPwd(oldPassword: string, newPassword: string) {
  return request({
    url: '/system/user/profile/updatePwd',
    method: 'put',
    params: { oldPassword, newPassword }
  })
}

// 用户头像上传
export function uploadAvatar(data: FormData) {
  return request({
    url: '/system/user/profile/avatar',
    method: 'post',
    data: data
  })
}

// 下载用户导入模板
export function importTemplate() {
  return request({
    url: '/system/user/importTemplate',
    method: 'post',
    responseType: 'blob'
  })
}
```

### 登录 API

**文件**: `src/api/login.ts`

```typescript
import request from '@/utils/request'

export interface LoginForm {
  username: string
  password: string
  code: string
  uuid: string
}

export interface UserInfo {
  user: {
    userId: number
    userName: string
    nickName: string
    email: string
    phonenumber: string
    sex: string
    avatar: string
    status: string
    createTime: string
  }
  roles: string[]
  permissions: string[]
}

// 登录方法
export function login(username: string, password: string, code: string, uuid: string) {
  const data = {
    username,
    password,
    code,
    uuid
  }
  return request({
    url: '/login',
    method: 'post',
    data: data
  })
}

// 获取用户详细信息
export function getInfo() {
  return request({
    url: '/getInfo',
    method: 'get'
  })
}

// 退出方法
export function logout() {
  return request({
    url: '/logout',
    method: 'post'
  })
}

// 获取验证码
export function getCodeImg() {
  return request({
    url: '/captchaImage',
    method: 'get',
    timeout: 20000
  })
}
```

## 在组件中使用 API

### 1. 基本使用

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listUser, delUser } from '@/api/system/user'
import type { UserQuery, UserVO } from '@/api/system/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const userList = ref<UserVO[]>([])
const total = ref(0)
const loading = ref(false)

const queryParams = ref<UserQuery>({
  pageNum: 1,
  pageSize: 10
})

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const res = await listUser(queryParams.value)
    userList.value = res.rows
    total.value = res.total
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 删除用户
const handleDelete = async (row: UserVO) => {
  try {
    await ElMessageBox.confirm('是否确认删除用户"' + row.userName + '"?', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await delUser(row.userId)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
    }
  }
}

onMounted(() => {
  getList()
})
</script>
```

### 2. 使用 Loading

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { ElLoading } from 'element-plus'
import { addUser } from '@/api/system/user'

const handleSubmit = async () => {
  const loading = ElLoading.service({
    lock: true,
    text: '提交中...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  
  try {
    await addUser(form.value)
    ElMessage.success('新增成功')
  } finally {
    loading.close()
  }
}
</script>
```

### 3. 错误处理

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { updateUser } from '@/api/system/user'
import { ElMessage } from 'element-plus'

const handleUpdate = async () => {
  try {
    await updateUser(form.value)
    ElMessage.success('修改成功')
  } catch (error: any) {
    // 统一错误处理已在 request.ts 中完成
    // 这里可以添加特殊的错误处理逻辑
    console.error('修改失败:', error)
  }
}
</script>
```

## 文件上传

### 1. 图片上传

```vue
<template>
  <el-upload
    class="avatar-uploader"
    :action="uploadUrl"
    :headers="headers"
    :show-file-list="false"
    :on-success="handleSuccess"
    :before-upload="beforeUpload"
  >
    <img v-if="imageUrl" :src="imageUrl" class="avatar" />
    <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
  </el-upload>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getToken } from '@/utils/auth'

const imageUrl = ref('')

const uploadUrl = computed(() => {
  return import.meta.env.VITE_APP_BASE_API + '/common/upload'
})

const headers = computed(() => {
  return {
    Authorization: 'Bearer ' + getToken()
  }
})

const beforeUpload = (file: File) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('上传图片只能是 JPG/PNG 格式!')
  }
  if (!isLt2M) {
    ElMessage.error('上传图片大小不能超过 2MB!')
  }
  return isJPG && isLt2M
}

const handleSuccess = (response: any) => {
  if (response.code === 200) {
    imageUrl.value = response.data.url
    ElMessage.success('上传成功')
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}
</script>
```

### 2. 文件下载

```typescript
// src/utils/download.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'

export function download(url: string, params: any, filename: string) {
  return axios({
    url: import.meta.env.VITE_APP_BASE_API + url,
    method: 'get',
    params: params,
    headers: {
      'Authorization': 'Bearer ' + getToken()
    },
    responseType: 'blob'
  }).then(async (response) => {
    const isBlob = response.data.type !== 'application/json'
    if (isBlob) {
      const blob = new Blob([response.data])
      saveAs(blob, filename)
    } else {
      const resText = await response.data.text()
      const rspObj = JSON.parse(resText)
      const errMsg = rspObj.msg || '下载文件出现错误,请联系管理员!'
      ElMessage.error(errMsg)
    }
  }).catch((error) => {
    console.error('下载文件出现错误:', error)
    ElMessage.error('下载文件出现错误,请联系管理员!')
  })
}

function saveAs(blob: Blob, filename: string) {
  const link = document.createElement('a')
  link.href = window.URL.createObjectURL(blob)
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(link.href)
}
```

使用下载:

```vue
<script setup lang="ts">
import { download } from '@/utils/download'

const handleExport = () => {
  download('/system/user/export', queryParams.value, '用户数据.xlsx')
}
</script>
```

## API Mock

### 使用 Mock.js

```typescript
// mock/user.ts
import Mock from 'mockjs'

export default [
  {
    url: '/api/system/user/list',
    method: 'get',
    response: () => {
      return {
        code: 200,
        msg: '操作成功',
        data: {
          rows: Mock.mock({
            'list|10': [{
              'userId|+1': 1,
              userName: '@name',
              nickName: '@cname',
              email: '@email',
              phonenumber: /^1[3-9]\d{9}$/,
              sex: '@pick(["0", "1"])',
              status: '@pick(["0", "1"])',
              createTime: '@datetime'
            }]
          }).list,
          total: 100
        }
      }
    }
  }
]
```

## 最佳实践

### 1. 统一响应格式
```typescript
interface Response<T = any> {
  code: number
  msg: string
  data: T
}
```

### 2. 类型定义
- 为每个 API 定义请求和响应类型
- 使用 TypeScript 接口

### 3. 错误处理
- 统一在拦截器中处理
- 特殊错误在组件中处理

### 4. Loading 状态
- 列表查询显示 loading
- 提交操作显示 loading

### 5. 请求取消
```typescript
import axios from 'axios'

const CancelToken = axios.CancelToken
const source = CancelToken.source()

request({
  url: '/api/data',
  cancelToken: source.token
})

// 取消请求
source.cancel('操作被用户取消')
```

## 下一步

- [权限系统](./06-权限系统.md) - 理解权限控制
- [开发规范](./07-开发规范.md) - 编码标准
