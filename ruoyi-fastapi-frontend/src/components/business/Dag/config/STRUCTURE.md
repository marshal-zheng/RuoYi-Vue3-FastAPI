# DAG 配置文件结构

```
src/components/business/Dag/config/
│
├── index.js                    # 📦 统一入口（推荐导入路径）
│   └── 导出所有配置和工具函数
│
├── nodeConfig.js               # 🔷 节点配置
│   ├── DAG_NODE_CONFIG
│   │   ├── size.horizontal    → 横向布局节点尺寸
│   │   ├── size.vertical      → 纵向布局节点尺寸
│   │   └── shape              → 节点形状名称
│   └── getNodeSize()          → 根据方向获取节点尺寸
│
├── edgeConfig.js               # 🔗 边配置
│   ├── DAG_EDGE_CONFIG
│   │   ├── shape              → 边形状名称
│   │   ├── style.normal       → 默认样式（颜色、宽度）
│   │   ├── style.hover        → 悬停样式
│   │   ├── style.selected     → 选中样式（含阴影）
│   │   ├── label.weight       → 权重标签样式
│   │   └── label.position     → 标签位置
│   └── getEdgeStyle()         → 根据状态获取边样式
│
├── layoutConfig.js             # 📐 布局配置
│   ├── DAG_LAYOUT_CONFIG
│   │   ├── ranksep            → 层级间距（220）
│   │   ├── nodesep            → 同层节点间距（100）
│   │   └── defaultDirection   → 默认布局方向（TB）
│   └── getLayoutConfig()      → 获取布局配置（支持覆盖）
│
├── connectorConfig.js          # 🎯 连接器配置
│   └── DAG_CONNECTOR_CONFIG
│       ├── name               → 连接器名称
│       ├── minControl         → 最小控制距离（50）
│       └── controlFactor      → 控制点距离系数（0.5）
│
├── portConfig.js               # 🔌 端口配置
│   └── DAG_PORT_CONFIG
│       ├── radius             → 端口半径（8）
│       ├── strokeWidth        → 边框宽度（2）
│       ├── strokeColor        → 边框颜色
│       ├── fillColor          → 填充颜色
│       ├── defaultOpacity     → 默认透明度（0 - 隐藏）
│       └── activeOpacity      → 激活透明度（1 - 显示）
│
├── interactionConfig.js        # 🖱️ 交互配置
│   └── DAG_INTERACTION_CONFIG
│       ├── snapline           → 对齐线配置
│       └── zoom               → 缩放配置
│
├── dagConfig.js                # ⚠️  向后兼容入口（已废弃）
│   └── 重新导出 index.js 的所有内容
│
└── README.md                   # 📖 配置文档
    └── 详细使用说明和示例
```

## 🎯 配置文件职责

| 文件 | 职责 | 主要配置项 |
|------|------|-----------|
| `index.js` | 统一入口，聚合所有配置 | - |
| `nodeConfig.js` | 节点外观和尺寸 | 宽度、高度、形状 |
| `edgeConfig.js` | 边的样式和标签 | 颜色、宽度、标签样式 |
| `layoutConfig.js` | 布局算法参数 | 层级间距、节点间距、方向 |
| `connectorConfig.js` | 连线曲线参数 | 控制距离、弯曲系数 |
| `portConfig.js` | 连接桩样式 | 半径、颜色、透明度 |
| `interactionConfig.js` | 用户交互行为 | 对齐线、缩放范围 |

## 🔄 依赖关系

```
业务代码
    ↓
config/index.js (统一入口)
    ↓
├── nodeConfig.js
├── edgeConfig.js
├── layoutConfig.js
├── connectorConfig.js
├── portConfig.js
└── interactionConfig.js
```

## 📝 修改配置的步骤

1. **确定要修改的配置类型**
   - 节点尺寸？→ `nodeConfig.js`
   - 边宽度/颜色？→ `edgeConfig.js`
   - 节点间距？→ `layoutConfig.js`

2. **打开对应的配置文件**

3. **修改配置值**

4. **刷新页面查看效果**

5. **无需修改业务代码！** ✨

## 🚀 快速定位

想修改什么？快速找到对应文件：

- **节点太小/太大** → `nodeConfig.js` 的 `size`
- **节点间距太窄** → `layoutConfig.js` 的 `ranksep` 或 `nodesep`
- **边太细/太粗** → `edgeConfig.js` 的 `style.normal.strokeWidth`
- **边选中不明显** → `edgeConfig.js` 的 `style.selected`
- **权重标签太小** → `edgeConfig.js` 的 `label.weight.fontSize`
- **连接桩太小** → `portConfig.js` 的 `radius`
- **曲线太直/太弯** → `connectorConfig.js` 的 `controlFactor`

