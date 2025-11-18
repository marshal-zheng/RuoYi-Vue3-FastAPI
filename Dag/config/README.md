# DAG 图形配置中心

统一管理 DAG 图的所有可配置项，方便维护和自定义。

## 📁 文件说明

### 配置文件（按模块组织）

- **`index.js`**: 统一入口，导出所有配置和工具函数 ⭐ **推荐导入**
- **`nodeConfig.js`**: 节点配置（尺寸、形状）
- **`edgeConfig.js`**: 边配置（样式、标签）
- **`layoutConfig.js`**: 布局配置（间距、方向）
- **`connectorConfig.js`**: 连接器配置（贝塞尔曲线参数）
- **`portConfig.js`**: 端口配置（连接桩样式）
- **`interactionConfig.js`**: 交互配置（对齐线、缩放）
- **`dagConfig.js`**: 向后兼容文件（已废弃，建议使用 `index.js`）

## 🎯 配置项说明

### 1. 布局配置 (`DAG_LAYOUT_CONFIG`)

控制图形布局的间距和方向。

```javascript
import { DAG_LAYOUT_CONFIG } from './dagConfig.js'

// 可配置项：
{
  ranksep: 220,           // 层级间距（不同层级节点之间的距离）
  nodesep: 100,           // 同层节点间距（同一层级内节点之间的距离）
  defaultDirection: 'TB'  // 默认布局方向 ('LR' | 'TB')
}
```

### 2. 节点配置 (`DAG_NODE_CONFIG`)

控制节点的尺寸和形状。

```javascript
import { DAG_NODE_CONFIG } from './dagConfig.js'

// 可配置项：
{
  size: {
    horizontal: { width: 200, height: 38 },  // 横向布局节点尺寸
    vertical: { width: 45, height: 200 }     // 纵向布局节点尺寸
  },
  shape: 'dag-node'  // 节点形状名称
}
```

### 3. 边配置 (`DAG_EDGE_CONFIG`)

控制连线的样式和标签。

```javascript
import { DAG_EDGE_CONFIG } from './dagConfig.js'

// 可配置项：
{
  shape: 'dag-edge',
  style: {
    normal: {                              // 默认状态
      stroke: '#C2C8D5',
      strokeWidth: 4
    },
    hover: {                               // 悬停状态
      stroke: '#66b1ff',
      strokeWidth: 5
    },
    selected: {                            // 选中状态
      stroke: '#409eff',
      strokeWidth: 6,
      shadow: {
        dx: 0, dy: 0, blur: 6,
        color: 'rgba(24, 144, 255, 0.4)'
      }
    }
  },
  label: {
    weight: {                              // 权重标签样式
      fill: '#409eff',
      fontSize: 13,
      fontWeight: 600,
      textAnchor: 'middle',
      textVerticalAnchor: 'middle',
      cursor: 'pointer'
    },
    position: {                            // 标签位置
      distance: 0.5,                       // 在边的中点
      offset: { x: 0, y: 0 }
    }
  }
}
```

### 4. 连接器配置 (`DAG_CONNECTOR_CONFIG`)

控制连线的贝塞尔曲线参数。

```javascript
import { DAG_CONNECTOR_CONFIG } from './dagConfig.js'

// 可配置项：
{
  name: 'dag-connector',
  minControl: 50,        // 最小控制距离（避免节点过近时曲线太扁）
  controlFactor: 0.5     // 控制点距离系数（控制曲线弯曲程度）
}
```

### 5. 端口配置 (`DAG_PORT_CONFIG`)

控制连接桩的样式。

```javascript
import { DAG_PORT_CONFIG } from './dagConfig.js'

// 可配置项：
{
  radius: 8,                // 端口半径
  strokeWidth: 2,           // 端口边框宽度
  strokeColor: '#31d0c6',   // 端口边框颜色
  fillColor: '#fff',        // 端口填充颜色
  defaultOpacity: 0,        // 默认透明度（隐藏状态）
  activeOpacity: 1          // 激活时透明度（显示状态）
}
```

### 6. 交互配置 (`DAG_INTERACTION_CONFIG`)

控制用户交互行为。

```javascript
import { DAG_INTERACTION_CONFIG } from './dagConfig.js'

// 可配置项：
{
  snapline: {               // 对齐线配置
    enabled: true,
    tolerance: 15,
    sharp: false
  },
  zoom: {                   // 缩放配置
    factor: 1.05,
    minScale: 0.1,
    maxScale: 3
  }
}
```

## 🔧 使用方法

### 方法 1：从统一入口导入（推荐）⭐

```javascript
import { 
  DAG_LAYOUT_CONFIG, 
  DAG_EDGE_CONFIG,
  DAG_NODE_CONFIG 
} from '@/components/business/Dag/config'

// 使用配置
const ranksep = DAG_LAYOUT_CONFIG.ranksep
const edgeStroke = DAG_EDGE_CONFIG.style.normal.stroke
const nodeWidth = DAG_NODE_CONFIG.size.horizontal.width
```

### 方法 2：从具体模块导入（明确性更好）

```javascript
// 只导入需要的配置模块
import { DAG_EDGE_CONFIG } from '@/components/business/Dag/config/edgeConfig'
import { DAG_NODE_CONFIG } from '@/components/business/Dag/config/nodeConfig'
import { DAG_LAYOUT_CONFIG } from '@/components/business/Dag/config/layoutConfig'

// 使用配置
const edgeWidth = DAG_EDGE_CONFIG.style.normal.strokeWidth
```

### 方法 3：使用工具函数

```javascript
import { getNodeSize, getEdgeStyle, getLayoutConfig } from '@/components/business/Dag/config'

// 获取节点尺寸
const nodeSize = getNodeSize('TB')  // 根据方向获取节点尺寸

// 获取边样式
const hoverStyle = getEdgeStyle('hover')  // 获取悬停状态样式

// 获取布局配置（可覆盖默认值）
const layoutConfig = getLayoutConfig({ ranksep: 300 })
```

### 方法 4：默认导出（所有配置）

```javascript
import dagConfig from '@/components/business/Dag/config'

const ranksep = dagConfig.layout.ranksep
const nodeSize = dagConfig.getNodeSize('LR')
const edgeWidth = dagConfig.edge.style.normal.strokeWidth
```

## 🎨 自定义配置示例

### 示例 1：调整节点间距

```javascript
// 在 layoutConfig.js 中修改
export const DAG_LAYOUT_CONFIG = {
  ranksep: 300,  // 增加层级间距
  nodesep: 150,  // 增加同层节点间距
  defaultDirection: 'LR'  // 改为横向布局
}
```

### 示例 2：修改边的颜色和宽度

```javascript
// 在 edgeConfig.js 中修改
export const DAG_EDGE_CONFIG = {
  style: {
    normal: {
      stroke: '#67C23A',  // 改为绿色
      strokeWidth: 6      // 增加宽度
    },
    // ...
  }
}
```

### 示例 3：调整节点尺寸

```javascript
// 在 nodeConfig.js 中修改
export const DAG_NODE_CONFIG = {
  size: {
    horizontal: {
      width: 250,   // 增加宽度
      height: 50    // 增加高度
    },
    vertical: {
      width: 60,
      height: 250
    }
  }
}
```

## ✨ 最佳实践

1. **模块化管理**: 
   - 节点相关配置修改 `nodeConfig.js`
   - 边相关配置修改 `edgeConfig.js`
   - 布局相关配置修改 `layoutConfig.js`
   - 不要在业务代码中硬编码配置值

2. **统一导入**: 
   - 推荐从 `config/index.js` 导入（简洁）
   - 也可从具体模块导入（明确性更好）

3. **向后兼容**: 
   - 已有代码会自动使用新配置，无需修改
   - `dagConfig.js` 作为向后兼容入口保留

4. **类型安全**: 
   - 配置项都有详细的 JSDoc 注释
   - 支持 IDE 自动补全和类型检查

5. **关注点分离**: 
   - 配置按功能独立成文件，便于查找和维护
   - 每个配置文件职责单一

## 📝 注意事项

- 修改配置后需要刷新页面才能看到效果
- 节点尺寸的修改会影响布局计算
- 边宽度的修改会影响选中状态的视觉效果
- 建议在修改前备份原有配置

## 🔗 相关文件

- `src/components/business/Dag/utils/layout.js` - 使用布局配置
- `src/components/business/Dag/shapes/registerDagShapes.js` - 使用节点、边、连接器、端口配置
- `src/components/business/Dag/utils/nodeGeometry.js` - 使用节点尺寸配置
- `src/components/business/Dag/components/DagInitData.vue` - 使用端口配置

