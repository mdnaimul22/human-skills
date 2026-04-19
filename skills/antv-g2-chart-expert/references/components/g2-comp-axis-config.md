---
id: "g2-comp-axis-config"
title: "G2 Axis Configuration (axis)"
description: |
  Detailed explanation of the axis field configuration in G2 v5 Spec mode, covering axis title, ticks, label formatting,
  grid lines, axis line style, etc., supporting independent configuration for x and y axes.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "axis"
  - "coordinate axis"
  - "axis title"
  - "ticks"
  - "label formatting"
  - "grid lines"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-scale-linear"
  - "g2-scale-time"
  - "g2-scale-band"

use_cases:
  - "Customizing coordinate axis title"
  - "Formatting axis tick labels (percentage, currency, date, etc.)"
  - "Controlling the number of ticks and grid lines"
  - "Hiding coordinate axis"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/axis"
---

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'revenue' },
  axis: {
    x: { title: 'Month' },
    y: { title: 'Revenue (10,000 Yuan)' },
  },
});

chart.render();
```

---

## Incremental Configuration Modification

If a chart already exists and you only want to modify a specific configuration item (such as label color), you can use the following methods:

```javascript
// Method 1: Re-call options, passing only the configuration to be modified
chart.options({
  axis: {
    y: {
      labelFill: 'red',  // Only modify label color
    },
  },
});
chart.render();  // Re-rendering is required

// Method 2: Modify after complete configuration
const options = {
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: { x: { title: 'Date' } },
};
chart.options(options);

// Subsequent modification
options.axis = { y: { labelFill: 'red' } };
chart.options(options);
chart.render();
```

---

## Complete Configuration Options Reference

### General Configuration

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `position` | Axis position | `'left' \| 'right' \| 'top' \| 'bottom'` | x: `'bottom'`, y: `'left'` |
| `animate` | Whether to enable animation | `boolean` | - |

### Axis Title Style (title)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `title` | Title content | `string \| false` | - |
| `titleSpacing` | Distance from the title to the axis | `number` | `10` |
| `titlePosition` | Position of the title relative to the axis | `'top' \| 'bottom' \| 'left' \| 'right'` | `'lb'` |
| `titleFontSize` | **Title font size** | `number` | - |
| `titleFontWeight` | Title font weight | `number \| string` | - |
| `titleFontFamily` | Title font family | `string` | - |
| `titleLineHeight` | Title line height | `number` | `1` |
| `titleTextAlign` | Title text horizontal alignment | `string` | `'start'` |
| `titleTextBaseline` | Title text vertical baseline | `string` | `'middle'` |
| `titleFill` | **Title text fill color** | `string` | - |
| `titleFillOpacity` | Title text fill opacity | `number` | `1` |
| `titleStroke` | Title text stroke color | `string` | `transparent` |
| `titleStrokeOpacity` | Title text stroke opacity | `number` | `1` |
| `titleLineWidth` | Title text stroke width | `number` | `0` |
| `titleLineDash` | Title text stroke dash configuration | `number[]` | `[]` |
| `titleOpacity` | Overall title text opacity | `number` | `1` |
| `titleShadowColor` | Title text shadow color | `string` | `transparent` |
| `titleShadowBlur` | Title text shadow blur factor | `number` | `0` |
| `titleShadowOffsetX` | Title text shadow horizontal offset | `number` | `0` |
| `titleShadowOffsetY` | Title text shadow vertical offset | `number` | `0` |
| `titleCursor` | Title text mouse cursor style | `string` | `default` |
| `titleDx` | Title text horizontal offset | `number` | `0` |
| `titleDy` | Title text vertical offset | `number` | `0` |

### Axis Line Style (line)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `line` | Whether to display the axis line | `boolean` | `false` |
| `arrow` | Whether to display the arrow | `boolean` | `true` |
| `lineExtension` | Extension lines on both sides of the axis line | `[number, number]` | - |
| `lineArrow` | Shape of the axis line arrow | `DisplayObject` | - |
| `lineArrowOffset` | Arrow offset length | `number` | `15` |
| `lineArrowSize` | Arrow size | `number` | - |
| `lineStroke` | **Axis line stroke color** | `string` | - |
| `lineStrokeOpacity` | Axis line stroke opacity | `number` | - |
| `lineLineWidth` | **Axis line stroke width** | `number` | - |
| `lineLineDash` | Axis line stroke dash configuration | `[number, number]` | - |
| `lineOpacity` | Overall opacity of the axis line | `number` | `1` |
| `lineShadowColor` | Axis line shadow color | `string` | - |
| `lineShadowBlur` | Axis line shadow blur factor | `number` | - |
| `lineShadowOffsetX` | Axis line shadow horizontal offset | `number` | - |
| `lineShadowOffsetY` | Axis line shadow vertical offset | `number` | - |
| `lineCursor` | Axis line mouse cursor style | `string` | `default` |

### Tick Style (tick)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `tick` | Whether to display ticks | `boolean` | `true` |
| `tickCount` | Recommended number of ticks to generate | `number` | - |
| `tickMethod` | Custom tick generation method | `(start, end, count) => number[]` | - |
| `tickFilter` | Tick filtering | `(datum, index, data) => boolean` | - |
| `tickFormatter` | Tick formatting | `(datum, index, data, Vector) => DisplayObject` | - |
| `tickDirection` | Tick direction | `'positive' \| 'negative'` | `'positive'` |
| `tickLength` | **Tick length** | `number` | `15` |
| `tickStroke` | **Tick stroke color** | `string` | - |
| `tickStrokeOpacity` | Tick stroke opacity | `number` | - |
| `tickLineWidth` | Tick stroke width | `number` | - |
| `tickLineDash` | Tick stroke dash configuration | `[number, number]` | - |
| `tickOpacity` | Overall tick opacity | `number` | - |
| `tickShadowColor` | Tick shadow color | `string` | - |
| `tickShadowBlur` | Tick shadow blur factor | `number` | - |
| `tickShadowOffsetX` | Tick shadow horizontal offset | `number` | - |
| `tickShadowOffsetY` | Tick shadow vertical offset | `number` | - |
| `tickCursor` | Tick cursor style | `string` | `default` |
### 刻度标签样式（label）

| 属性 | 描述 | 类型 | 默认值 |
|------|------|------|--------|
| `labelFormatter` | **标签格式化** | `string \| (datum, index, data) => string` | - |
| `labelFilter` | 标签过滤 | `(datum, index, data) => boolean` | - |
| `labelAutoRotate` | 标签过长时自动旋转 | `boolean` | - |
| `labelAutoHide` | 标签过密时自动隐藏 | `boolean` | - |
| `labelSpacing` | 标签与刻度线的间距 | `number` | - |
| `labelFontSize` | **标签文字大小** | `number` | - |
| `labelFontWeight` | 标签文字字体粗细 | `number \| string` | - |
| `labelFontFamily` | 标签文字字体 | `string` | - |
| `labelLineHeight` | 标签文字行高 | `number` | - |
| `labelTextAlign` | 标签文字水平对齐方式 | `string` | - |
| `labelTextBaseline` | 标签文字垂直基线 | `string` | - |
| `labelFill` | **标签文字填充色** | `string` | - |
| `labelFillOpacity` | 标签文字填充透明度 | `number` | - |
| `labelStroke` | 标签文字描边颜色 | `string` | - |
| `labelStrokeOpacity` | 标签文字描边透明度 | `number` | - |
| `labelLineWidth` | 标签文字描边宽度 | `number` | - |
| `labelLineDash` | 标签文字描边虚线配置 | `number[]` | - |
| `labelOpacity` | 标签文字整体透明度 | `number` | - |
| `labelShadowColor` | 标签文字阴影颜色 | `string` | - |
| `labelShadowBlur` | 标签文字阴影模糊系数 | `number` | - |
| `labelShadowOffsetX` | 标签文字阴影水平偏移量 | `number` | - |
| `labelShadowOffsetY` | 标签文字阴影垂直偏移量 | `number` | - |
| `labelCursor` | 标签文字鼠标样式 | `string` | `default` |
| `labelDx` | 标签文字水平偏移量 | `number` | - |
| `labelDy` | 标签文字垂直偏移量 | `number` | - |

### 刻度标签样式（label，补充）

| 属性 | 描述 | 类型 | 默认值 |
|------|------|------|--------|
| `labelRender` | 自定义标签渲染，支持 HTML 字符串，用法同 `labelFormatter` | `string \| (datum, index, array) => string` | - |
| `labelAlign` | 刻度值对齐方式 | `'horizontal' \| 'parallel' \| 'perpendicular'` | `'parallel'` |
| `labelDirection` | 刻度值相对轴线的位置 | `'positive' \| 'negative'` | `'positive'` |
| `labelAutoEllipsis` | 自动缩略过长的刻度值 | `boolean` | - |
| `labelAutoWrap` | 自动换行刻度值 | `boolean` | - |

### 网格线样式（grid）

| 属性 | 描述 | 类型 | 默认值 |
|------|------|------|--------|
| `grid` | 是否显示网格线 | `boolean` | - |
| `gridAreaFill` | **网格线区域填充色**，支持交替颜色数组或函数 | `string \| string[] \| (datum, index, data) => string` | - |
| `gridFilter` | 网格线过滤，返回 false 隐藏该网格线 | `(datum, index, data) => boolean` | - |
| `gridLength` | 网格线长度 | `number` | `0` |
| `gridStroke` | **网格线描边颜色** | `string` | - |
| `gridStrokeOpacity` | 网格线描边透明度 | `number` | - |
| `gridLineWidth` | **网格线描边宽度** | `number` | - |
| `gridLineDash` | **网格线描边虚线配置** | `[number, number]` | - |
| `gridOpacity` | 网格线整体透明度 | `number` | - |
| `gridShadowColor` | 网格线阴影颜色 | `string` | - |
| `gridShadowBlur` | 网格线阴影模糊系数 | `number` | - |
| `gridShadowOffsetX` | 网格线阴影水平偏移量 | `number` | - |
| `gridShadowOffsetY` | 网格线阴影垂直偏移量 | `number` | - |
| `gridCursor` | 网格线鼠标样式 | `string` | `default` |

---

## 常用配置示例

### 完整配置示例

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: {
    x: {
      title: '日期',
      titleFontSize: 14,
      titleFill: '#666',
      tickCount: 6,
      labelFormatter: 'YYYY-MM',
      labelFontSize: 11,
      labelFill: '#888',
      tick: true,
      tickLength: 5,
      line: true,
      grid: true,
      gridLineDash: [4, 4],
    },
    y: {
      title: '收入（万元）',
      labelFormatter: (v) => `¥${v}`,
    },
  },
});
```

### 刻度相关配置职责速查

刻度控制有三个配置项，职责不同，不能混用：

| 配置项 | 签名 | 职责 | 使用频率 |
|--------|------|------|---------|
| `labelFormatter` | `(value, index, array) => string` | 刻度**文字内容** | ⭐ 最常用 |
| `tickMethod` | `(start, end, tickCount) => number[]` | 刻度**数值位置** | 偶尔使用 |
| `tickFormatter` | `(datum, index, array, vector) => DisplayObject` | 刻度**线图形** | 极少使用 |

> ❌ 常见错误：把 `tickFormatter` 当 `labelFormatter` 用——`tickFormatter` 返回的是图形对象，不是字符串，用错会导致标签不显示。

### 常用格式化场景

```javascript
// 数值格式化
axis: { y: { labelFormatter: (v) => `${(v / 1000).toFixed(0)}K` } }

// 百分比格式化
axis: { y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` } }

// 货币格式化
axis: { y: { labelFormatter: (v) => `¥${v.toLocaleString()}` } }

// 日期格式化（x 轴为 Date 类型）
axis: { x: { labelFormatter: 'MM/DD' } }

// 保留两位小数（纯 d3-format，不能追加文字单位）
axis: { y: { labelFormatter: '.2f' } }         // ✅ 纯 d3-format
// axis: { y: { labelFormatter: '.2f 元' } }   // ❌ 无效！d3-format 后不能加文字
```

### 隐藏坐标轴

```javascript
// 完全隐藏某轴
axis: { x: false }

// 只隐藏标题
axis: { y: { title: false } }

// 只隐藏网格线
axis: { y: { grid: false } }
```

### 修改坐标轴文本配色

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: {
    x: {
      labelFill: '#8c8c8c',        // 标签文字颜色
      labelFontSize: 12,
      titleFill: '#595959',        // 标题文字颜色
      titleFontSize: 13,
      titleFontWeight: 'bold',
    },
    y: {
      labelFill: '#8c8c8c',
      titleFill: '#595959',
    },
  },
});
```

### 网格线区域交替填充（gridAreaFill）

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },
  axis: {
    y: {
      grid: true,
      gridAreaFill: ['rgba(0,0,0,0.04)', 'transparent'],  // 交替填充，增强可读性
      gridLineWidth: 0,   // 隐藏网格线本身，只显示区域色
    },
  },
});

// 也可以用函数控制
axis: {
  y: {
    gridAreaFill: (datum, index) => index % 2 === 0 ? 'rgba(0,0,0,0.04)' : '',
  },
}
```

### 断轴（breaks）—— 跳过数据空洞

```javascript
// 当数据中某段范围远超其他值，用断轴压缩该区间
chart.options({
  type: 'interval',
  data: [
    { x: 'A', y: 100 },
    { x: 'B', y: 200 },
    { x: 'C', y: 95000 },  // 异常值，导致其他柱看不清
    { x: 'D', y: 150 },
  ],
  encode: { x: 'x', y: 'y' },
  axis: {
    y: {
      breaks: [
        {
          start: 500,     // 断轴起点
          end: 90000,     // 断轴终点（跳过这段区间）
          gap: '3%',      // 断轴占画布高度比例
        },
      ],
    },
  },
});
```

### 双 y 轴

```javascript
// 使用 view 容器 + 不同 y 比例尺实现双轴
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'revenue' },
      axis: { y: { title: '收入', position: 'left' } },
    },
    {
      type: 'line',
      encode: { x: 'month', y: 'growth' },
      scale: { y: { key: 'right' } },
      axis: { y: { title: '增速', position: 'right' } },
    },
  ],
});
```

---

## 常见错误与修正

### 错误 1：axis 写在 encode 或 scale 里

```javascript
// ❌ 错误：axis 是独立的顶级字段
chart.options({
  encode: { x: 'month', y: 'value' },
  scale: { x: { title: '月份' } },   // title 不在 scale 里
});

// ✅ 正确：axis 是与 encode/scale 平级的字段
chart.options({
  encode: { x: 'month', y: 'value' },
  axis: { x: { title: '月份' } },
});
```

### 错误 2：样式属性名错误

```javascript
// ❌ 错误的属性名
axis: { x: { fontSize: 12 } }  // 不存在

// ✅ 正确的属性名（带前缀）
axis: { x: { labelFontSize: 12 } }  // 标签字体大小
axis: { x: { titleFontSize: 14 } }  // 标题字体大小
```

### 错误 3：混淆轴标题与图表标题

```javascript
// ❌ 轴标题写在 title 里
title: { title: '月份' }  // 这是图表标题

// ✅ 轴标题在 axis 里
axis: { x: { title: '月份' } }  // 这是 X 轴标题
```

### 错误 4：用 tickFormatter 格式化标签文字

```javascript
// ❌ 错误：tickFormatter 返回的是 DisplayObject（图形对象），不是字符串
axis: {
  y: {
    tickFormatter: (v) => `${v / 1000}K`,  // ❌ 返回字符串给 tickFormatter 无效
  },
}

// ✅ 正确：标签文字格式化用 labelFormatter
axis: {
  y: {
    labelFormatter: (v) => `${v / 1000}K`,  // ✅ labelFormatter 返回 string
  },
}
```

### 错误 5：在 scale.tickMethod 里格式化标签或接收 scale 对象

```javascript
// ❌ 错误：tickMethod 参数不是 scale 对象，返回值不是对象数组
scale: {
  y: {
    tickMethod: (scale) => {              // ❌ 参数不是 scale 对象
      return scale.ticks().map(v => ({    // ❌ scale.ticks() 不存在
        value: v, text: `${v}K`          // ❌ 不能返回对象，只能返回 number[]
      }));
    },
  },
}

// ✅ 正确：tickMethod 签名是 (min, max, count) => number[]
// 格式化文字另用 labelFormatter
scale: {
  y: {
    tickMethod: (min, max, count) => [100, 500, 1000, 5000, 10000],  // ✅ number[]
  },
},
axis: {
  y: {
    labelFormatter: (v) => `${v / 1000}K`,  // ✅ 文字格式化在 axis
  },
}
```

### 错误 6：labelFormatter 用 d3-format 字符串拼接单位

`labelFormatter` 与 `tooltip.items[].valueFormatter` 一样，支持函数或 d3-format 字符串两种形式。**d3-format 字符串只格式化数字，不能在后面追加文字单位**——`'.2f 元'`、`'.0f 米'` 是无效写法。

```javascript
// ❌ 错误：d3-format 字符串后追加文字单位
axis: {
  y: { labelFormatter: '.2f 元' },   // ❌ d3-format 不支持拼接文字，标签异常
  x: { labelFormatter: '.0f 米' },   // ❌ 同上
}

// ✅ 正确：需要拼接单位时必须用函数形式
axis: {
  y: { labelFormatter: (v) => `${v.toFixed(2)} 元` },   // ✅ 函数，可拼接任意文字
  x: { labelFormatter: (v) => `${Math.round(v)} 米` },  // ✅ 函数
}

// ✅ 纯数字格式化（不加单位）可用 d3-format 字符串
axis: {
  y: { labelFormatter: '.2f' },    // ✅ 保留两位小数
  x: { labelFormatter: ',.0f' },  // ✅ 千分位整数
  z: { labelFormatter: '.1%' },   // ✅ 百分比
}
```

### 错误 7：labelFormatter 回调函数签名错误

`labelFormatter` 的回调函数签名应为 `(datum, index, array) => string`，其中：

- `datum`: 当前刻度值（通常是数值或字符串）
- `index`: 当前刻度索引
- `array`: 所有刻度值组成的数组

```javascript
// ❌ 错误：参数顺序错误或使用了不存在的参数
axis: {
  x: {
    labelFormatter: (task, item) => {  // ❌ item 参数不存在
      return `${item.data.stage}-${task}`;
    }
  }
}

// ✅ 正确：使用正确的参数签名
axis: {
  x: {
    labelFormatter: (datum, index, array) => {
      // 注意：此时 datum 是原始数据中的字段值，不是整个数据项
      return `${datum}`;  // 返回字符串即可
    }
  }
}

// ✅ 更推荐的做法：在 encode 中预处理复合标签
chart.options({
  encode: {
    x: (d) => `${d.stage} - ${d.task}`,  // 在 encode 中构造复合标签
    y: 'start',
    y1: 'end'
  },
  axis: {
    x: {
      labelTransform: 'rotate(30)'  // 如需旋转标签防止重叠
    }
  }
});
```

### 错误 8：legend.labelFormatter 与 axis.labelFormatter 混淆

虽然两者都用于格式化标签，但它们作用的对象不同。`legend.labelFormatter` 用于图例标签，而 `axis.labelFormatter` 用于坐标轴刻度标签。

```javascript
// ❌ 错误：在 legend 中使用 axis.labelFormatter
legend: {
  color: {
    labelFormatter: '.0%'  // ❌ legend 不支持 axis 的 labelFormatter
  }
}

// ✅ 正确：legend 使用自己的 labelFormatter
legend: {
  color: {
    labelFormatter: (value) => `${Math.round(value)}%`  // ✅ 函数形式
  }
}
```

### 错误 9：tooltip.valueFormatter 与 axis.labelFormatter 混淆

`tooltip.valueFormatter` 用于格式化提示框中的值，而 `axis.labelFormatter` 用于坐标轴标签。

```javascript
// ❌ 错误：在 tooltip.items 中使用 axis.labelFormatter
tooltip: {
  items: [
    { channel: 'y', labelFormatter: '.2f' }  // ❌ tooltip.items 不支持 labelFormatter
  ]
}

// ✅ 正确：tooltip.items 使用 valueFormatter
tooltip: {
  items: [
    { channel: 'y', valueFormatter: '.2f' }  // ✅ 使用 valueFormatter
  ]
}
```

### 错误 10：cell 图表中 style.inset 设置不当导致渲染空白

在 `cell` 类型图表中，`style.inset` 控制单元格的内边距。如果设置过大，可能导致单元格不可见。

```javascript
// ❌ 错误：inset 设置过大
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  style: {
    inset: 10  // ❌ inset 太大，可能使矩形不可见
  }
});

// ✅ 正确：合理设置 inset
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  style: {
    inset: 0.5  // ✅ 合理的 inset 值
  }
});
```

### 错误 11：legend.layout 配置错误导致布局异常

`legend.layout` 使用 Flexbox 布局模型，若配置不当会影响图例排版。

```javascript
// ❌ 错误：justifyContent 写错或不支持的值
legend: {
  color: {
    layout: { justifyContent: 'centered' }  // ❌ 不支持的值
  }
}

// ✅ 正确：使用合法的 Flexbox 值
legend: {
  color: {
    layout: { justifyContent: 'center' }  // ✅ 正确值
  }
}
```