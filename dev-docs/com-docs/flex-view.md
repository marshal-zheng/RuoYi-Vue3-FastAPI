# ZxFlexView

## 核心用法
```vue
<zx-flex-view column v--align-content="center" h-align-content="center">
  <div>内容</div>
</zx-flex-view>

<zx-flex-view wrap :grow="1" :shrink="0" basis="200px">
  <div>子元素</div>
</zx-flex-view>
```

## Props
- `column` (Boolean): flex-direction: column
- `vAlignContent` (String): 垂直对齐 `top | center | bottom`
- `hAlignContent` (String): 水平对齐 `left | center | right`
- `wrap` (Boolean): 换行
- `grow` (Boolean | Number): flex-grow
- `shrink` (Boolean | Number): flex-shrink
- `basis` (String | Number): flex-basis
- `marginLeft/Top/Right/Bottom` (String | Number): 外边距
- `height` (String | Number): 高度
- `width` (String | Number): 宽度
