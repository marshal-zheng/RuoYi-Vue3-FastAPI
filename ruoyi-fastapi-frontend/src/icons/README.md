# 业务图标配置

## 普通业务控件

`element.ts` 是现有 Element Plus 字符串图标的有限登记入口，目前为 46 个实际使用名称。`main.ts` 将同一份表交给 ZXUI capabilities，并登记必要的原生 Element Plus 全局组件，覆盖既有 `icon="Download"`、`prefix-icon="Search"` 等调用。

新增控件优先直接传组件引用，或在 Vue 模板中使用图标组件，由现有 resolver 自动按名称导入。继续使用字符串时，在 `element.ts` 增加明确导入和表项即可；不要恢复整集 `import *` 注册。

`vite/plugins/components.ts` 的 `entry: 'core'` 选择公开核心组件。组件库自行管理通用组合和固定图标；业务无需覆盖 ZXUI 内部路径。Vite 配置中用于识别组件名称的图标集合只在构建进程运行，不进入浏览器注册表。

## 导航菜单

`navigation.ts` 继续管理业务菜单标识与本地 SVG 的映射。动态菜单保存值、自定义 SVG、`svg-icon:` 协议与 Material Symbols 资产策略保持原契约。不要把这些名称、路由或映射放入 ZXUI。

## 表单设计器

`element-names.json` 只是固定版本 `@element-plus/icons-vue` 的 293 个导出名称，不包含图形实现。升级该依赖时，在前端目录执行以下命令更新名称元数据：

```sh
node --input-type=module -e "import * as icons from '@element-plus/icons-vue'; import {writeFileSync} from 'node:fs'; writeFileSync('src/icons/element-names.json', JSON.stringify(Object.keys(icons).sort(), null, 2) + '\\n')"
```

完整图形目录由 `src/views/tool/build/element-catalog.ts` 使用官方独立 `global` 出口提供，供设计器异步使用；不安装其全量插件。独立出口防止打包器把完整目录与普通具名导入合并成首包共享依赖。

选择器只在打开时挂载。旧设计仍保存字符串，`src/utils/generator/icons.ts` 在预览边界解析：常用名称同步取有限表，其他有效名称异步取目录，未知名称保持空图标。生成的 Vue 文件直接导入所选组件并绑定 props。

这里的动态兜底是功能级加载：第一次使用非常用的已保存图标或打开完整选择器，会加载整份目录；不是为任意配置逐图标分块。普通页面和常用设计不会为它预先加载图形实现。

## 构建复核

不能只看首页：普通异步路由的静态依赖也必须检查。源码直连复核用以下命令，或将已有构建目录传给 `yarn icons:check <目录>`：

```sh
VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --manifest
yarn icons:check
```

检查器遍历入口和各业务视图的静态依赖闭包；完整目录只允许作为设计器选择器的显式异步能力。它也统计输出中的 EP 图标定义，检查新增 namespace 导入是否把整集内联回来。源码别名必须沿用 ZXUI 的公开 source plugin，以保留库声明的副作用和样式转接入口，业务不要写全局关闭 tree-shaking 的配置。
