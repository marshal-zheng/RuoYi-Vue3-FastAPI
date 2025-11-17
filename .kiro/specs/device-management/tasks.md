# Device Management Implementation Tasks

- [x] 1. 创建数据库表和菜单配置
  - 创建设备分类表、设备表、设备接口表的SQL脚本
  - 创建设备中心菜单配置SQL脚本
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 2. 实现后端数据模型层
  - [x] 2.1 创建设备分类DO模型
    - 创建 `device_category_do.py` 包含所有字段和关系
    - _Requirements: 1.1, 1.2_
  
  - [x] 2.2 创建设备DO模型
    - 创建 `device_do.py` 和 `device_interface_do.py`
    - 定义设备与接口的一对多关系
    - _Requirements: 2.1, 3.1_
  
  - [x] 2.3 创建设备分类VO模型
    - 创建 `device_category_vo.py` 包含查询和响应模型
    - _Requirements: 1.1, 1.3_
  
  - [x] 2.4 创建设备VO模型
    - 创建 `device_vo.py` 包含设备和接口的VO模型
    - _Requirements: 2.1, 3.1_

- [ ] 3. 实现后端DAO层
  - [x] 3.1 实现设备分类DAO
    - 创建 `device_category_dao.py`
    - 实现分页查询、详情查询、新增、修改、删除方法
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 3.2 实现设备DAO
    - 创建 `device_dao.py`
    - 实现设备及接口的联合查询、新增、修改、删除方法
    - _Requirements: 2.1, 2.2, 3.1, 3.11_

- [ ] 4. 实现后端Service层
  - [x] 4.1 实现设备分类Service
    - 创建 `device_category_service.py`
    - 实现业务逻辑和数据验证
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3_
  
  - [x] 4.2 实现设备Service
    - 创建 `device_service.py`
    - 实现设备和接口的联合保存逻辑
    - _Requirements: 2.1, 3.1, 3.11, 9.1, 9.2_

- [ ] 5. 实现后端Controller层
  - [x] 5.1 实现设备分类Controller
    - 创建 `device_category_controller.py`
    - 实现所有API端点并添加权限装饰器
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3_
  
  - [x] 5.2 实现设备Controller
    - 创建 `device_controller.py`
    - 实现设备CRUD和导出API端点
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.10, 6.4, 6.5, 6.6, 6.7_

- [x] 6. 注册后端路由
  - 在 `server.py` 中注册设备分类和设备的路由
  - _Requirements: 1.1, 2.1_

- [ ] 7. 实现前端API服务层
  - [x] 7.1 创建设备分类API
    - 创建 `ruoyi-fastapi-frontend/src/api/device/category.js`
    - 实现所有API调用方法
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 7.2 创建设备API
    - 创建 `ruoyi-fastapi-frontend/src/api/device/device.js`
    - 实现设备CRUD和导出API调用
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.10_

- [ ] 8. 实现设备分类管理页面
  - [x] 8.1 创建分类列表页面
    - 创建 `ruoyi-fastapi-frontend/src/views/device/category/index.vue`
    - 实现表格、搜索、筛选、分页功能
    - _Requirements: 1.1, 1.8, 1.9, 10.1, 10.2, 10.3_
  
  - [x] 8.2 创建分类对话框组件
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/DeviceCategoryDialog.vue`
    - 实现表单验证和提交
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 8.6_

- [ ] 9. 实现设备列表管理页面
  - [x] 9.1 创建设备列表页面
    - 创建 `ruoyi-fastapi-frontend/src/views/device/list/index.vue`
    - 实现表格、搜索、筛选、分页、导出功能
    - _Requirements: 2.1, 2.2, 2.6, 2.7, 2.8, 2.9, 2.10, 10.1, 10.2, 10.3_

- [ ] 10. 实现设备详情配置页面
  - [x] 10.1 创建设备详情页面
    - 创建 `ruoyi-fastapi-frontend/src/views/device/detail/index.vue`
    - 实现X6画布、设备节点渲染、端口管理
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.11, 3.12, 3.13, 8.3, 8.4, 8.5_
  
  - [x] 10.2 创建端口编辑对话框
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/PortEditDialog.vue`
    - 实现端口基本信息编辑
    - _Requirements: 3.5, 3.6, 3.7, 7.4, 7.5_
  
  - [x] 10.3 创建端口配置抽屉
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/PortConfigDrawer.vue`
    - 实现参数和协议配置的Tab切换
    - _Requirements: 3.10, 4.6, 5.6, 8.1, 8.2_
  
  - [x] 10.4 创建参数配置Tab组件
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/ParamsConfigTab.vue`
    - 实现不同总线类型的参数配置表单
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 10.5 创建协议配置Tab组件
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/MessageConfigTab.vue`
    - 实现协议头和字段配置
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 10.6 创建协议列表抽屉
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/ProtocolListDrawer.vue`
    - 实现所有端口协议的展示和导航
    - _Requirements: 5.7, 5.8_

- [ ] 11. 创建选择器组件
  - [x] 11.1 创建总线类型选择器
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/selector/InterfaceTypeSelector.vue`
    - _Requirements: 3.5, 4.1_
  
  - [ ] 11.2 创建端口位置选择器
    - 创建 `ruoyi-fastapi-frontend/src/components/business/Device/selector/PositionSelector.vue`
    - _Requirements: 3.5_

- [ ] 12. 配置前端路由
  - 在路由配置中添加设备中心相关路由
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 13. 执行数据库初始化
  - 运行SQL脚本创建表和菜单
  - 插入默认设备分类数据
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 14. 集成测试和验证
  - 测试设备分类的增删改查功能
  - 测试设备列表的搜索、筛选、分页功能
  - 测试设备详情的端口配置功能
  - 测试权限控制是否正常工作
  - _Requirements: All_
