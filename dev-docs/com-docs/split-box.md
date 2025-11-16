# ZxSplitBox

可调整尺寸的分割容器组件,支持水平/垂直分割。

## 基础用法

```vue
<!-- 水平分割(左右) -->
<zx-split-box>
  <template #first>
    <div>左侧内容</div>
  </template>
  <template #second>
    <div>右侧内容</div>
  </template>
</zx-split-box>
```

## 垂直分割

```vue
<!-- 上下分割 -->
<zx-split-box direction="vertical">
  <template #first>
    <div>顶部内容</div>
  </template>
  <template #second>
    <div>底部内容</div>
  </template>
</zx-split-box>
```

## 尺寸控制

```vue
<!-- 初始尺寸和范围限制 -->
<zx-split-box
  v-model:size="splitSize"
  size="300px"
  min="200px"
  :max="0.8"
>
  <template #first>左侧</template>
  <template #second>右侧</template>
</zx-split-box>

<script setup>
const splitSize = ref('300px')
</script>
```

## 展开方向

```vue
<!-- 左侧可折叠 -->
<zx-split-box expand-direction="left">
  <template #first>可折叠的左侧</template>
  <template #second>主内容区</template>
</zx-split-box>

<!-- 右侧可折叠 -->
<zx-split-box expand-direction="right">
  <template #first>主内容区</template>
  <template #second>可折叠的右侧</template>
</zx-split-box>
```

## 隐藏面板

```vue
<!-- 不显示第一个面板 -->
<zx-split-box :not-show-first="true">
  <template #first>隐藏的侧边栏</template>
  <template #second>全屏主内容</template>
</zx-split-box>
```

## Props

- `v-model:size`: 双向绑定第一个容器的尺寸
- `size`: 左侧/顶部容器尺寸,默认'300px'
- `min`: 最小尺寸,默认'200px'
- `max`: 最大尺寸,数字表示比例,字符串表示像素,默认0.8
- `direction`: 分割方向 'horizontal'|'vertical',默认'horizontal'
- `expand-direction`: 展开方向 'left'|'right'|'top',默认'left'
- `disabled`: 禁用调整,默认false
- `first-container-class`: 第一个容器类名
- `second-container-class`: 第二个容器类名
- `not-show-first`: 不显示第一个面板,默认false

## Events

- `@update:size`: 尺寸变化,参数 `(size: string | number)`
- `@expand-change`: 展开状态变化,参数 `(expanded: boolean)`

## Slots

- `first`: 第一个容器内容(左侧或顶部)
- `second`: 第二个容器内容(右侧或底部)

## 使用场景

```vue
<!-- 侧边栏布局 -->
<zx-split-box size="250px" min="200px" max="400px">
  <template #first>
    <aside>导航菜单</aside>
  </template>
  <template #second>
    <main>主内容区</main>
  </template>
</zx-split-box>

<!-- 代码编辑器布局 -->
<zx-split-box direction="vertical" size="50%">
  <template #first>
    <div>代码编辑器</div>
  </template>
  <template #second>
    <div>预览区域</div>
  </template>
</zx-split-box>
```
