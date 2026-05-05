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

### Scale Label Style (label)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `labelFormatter` | **Label Formatting** | `string \| (datum, index, data) => string` | - |
| `labelFilter` | Label Filtering | `(datum, index, data) => boolean` | - |
| `labelAutoRotate` | Auto Rotate Labels When Too Long | `boolean` | - |
| `labelAutoHide` | Auto Hide Labels When Too Dense | `boolean` | - |
| `labelSpacing` | Spacing Between Label and Scale Line | `number` | - |
| `labelFontSize` | **Label Font Size** | `number` | - |
| `labelFontWeight` | Label Font Weight | `number \| string` | - |
| `labelFontFamily` | Label Font Family | `string` | - |
| `labelLineHeight` | Label Line Height | `number` | - |
| `labelTextAlign` | Label Text Horizontal Alignment | `string` | - |
| `labelTextBaseline` | Label Text Vertical Baseline | `string` | - |
| `labelFill` | **Label Text Fill Color** | `string` | - |
| `labelFillOpacity` | Label Text Fill Opacity | `number` | - |
| `labelStroke` | Label Text Stroke Color | `string` | - |
| `labelStrokeOpacity` | Label Text Stroke Opacity | `number` | - |
| `labelLineWidth` | Label Text Stroke Width | `number` | - |
| `labelLineDash` | Label Text Stroke Dash Configuration | `number[]` | - |
| `labelOpacity` | Overall Label Text Opacity | `number` | - |
| `labelShadowColor` | Label Text Shadow Color | `string` | - |
| `labelShadowBlur` | Label Text Shadow Blur Factor | `number` | - |
| `labelShadowOffsetX` | Label Text Shadow Horizontal Offset | `number` | - |
| `labelShadowOffsetY` | Label Text Shadow Vertical Offset | `number` | - |
| `labelCursor` | Label Text Cursor Style | `string` | `default` |
| `labelDx` | Label Text Horizontal Offset | `number` | - |
| `labelDy` | Label Text Vertical Offset | `number` | - |

### Scale Label Style (label, Supplement)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `labelRender` | Custom label rendering, supports HTML strings, usage is the same as `labelFormatter` | `string \| (datum, index, array) => string` | - |
| `labelAlign` | Scale value alignment method | `'horizontal' \| 'parallel' \| 'perpendicular'` | `'parallel'` |
| `labelDirection` | Position of the scale value relative to the axis line | `'positive' \| 'negative'` | `'positive'` |
| `labelAutoEllipsis` | Automatically abbreviate overly long scale values | `boolean` | - |
| `labelAutoWrap` | Automatically wrap scale values | `boolean` | - |

### Grid Line Style (grid)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `grid` | Whether to display grid lines | `boolean` | - |
| `gridAreaFill` | **Grid line area fill color**, supports alternating color arrays or functions | `string \| string[] \| (datum, index, data) => string` | - |
| `gridFilter` | Grid line filter, return false to hide the grid line | `(datum, index, data) => boolean` | - |
| `gridLength` | Grid line length | `number` | `0` |
| `gridStroke` | **Grid line stroke color** | `string` | - |
| `gridStrokeOpacity` | Grid line stroke opacity | `number` | - |
| `gridLineWidth` | **Grid line stroke width** | `number` | - |
| `gridLineDash` | **Grid line stroke dash configuration** | `[number, number]` | - |
| `gridOpacity` | Overall grid line opacity | `number` | - |
| `gridShadowColor` | Grid line shadow color | `string` | - |
| `gridShadowBlur` | Grid line shadow blur factor | `number` | - |
| `gridShadowOffsetX` | Grid line shadow horizontal offset | `number` | - |
| `gridShadowOffsetY` | Grid line shadow vertical offset | `number` | - |
| `gridCursor` | Grid line mouse cursor style | `string` | `default` |

---

## Common Configuration Examples

### Complete Configuration Example

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: {
    x: {
      title: 'Date',
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
      title: 'Revenue (Ten Thousand Yuan)',
      labelFormatter: (v) => `¥${v}`,
    },
  },
});
```

### Scale-Related Configuration Responsibilities Quick Reference

Scale control has three configuration items with different responsibilities and should not be mixed:

| Configuration Item | Signature | Responsibility | Usage Frequency |
|--------------------|-----------|----------------|-----------------|
| `labelFormatter` | `(value, index, array) => string` | Scale **text content** | ⭐ Most common |
| `tickMethod` | `(start, end, tickCount) => number[]` | Scale **numeric position** | Occasionally used |
| `tickFormatter` | `(datum, index, array, vector) => DisplayObject` | Scale **line graphic** | Rarely used |

> ❌ Common mistake: Using `tickFormatter` as `labelFormatter`——`tickFormatter` returns a graphic object, not a string, and misusing it will result in labels not being displayed.

### Common Formatting Scenarios

```javascript
// Numerical Formatting
axis: { y: { labelFormatter: (v) => `${(v / 1000).toFixed(0)}K` } }

// Percentage Formatting
axis: { y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` } }

// Currency Formatting
axis: { y: { labelFormatter: (v) => `¥${v.toLocaleString()}` } }

// Date Formatting (x-axis is of Date type)
axis: { x: { labelFormatter: 'MM/DD' } }

// Keep Two Decimal Places (Pure d3-format, cannot append text units)
axis: { y: { labelFormatter: '.2f' } }         // ✅ Pure d3-format
// axis: { y: { labelFormatter: '.2f 元' } }   // ❌ Invalid! Cannot add text after d3-format
```

### Hide Axis

```javascript
// Completely hide an axis
axis: { x: false }

// Hide only the title
axis: { y: { title: false } }

// Hide only the grid lines
axis: { y: { grid: false } }
```

### Modify Axis Text Color

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: {
    x: {
      labelFill: '#8c8c8c',        // Label text color
      labelFontSize: 12,
      titleFill: '#595959',        // Title text color
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

### Grid Area Alternate Fill (gridAreaFill)

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },
  axis: {
    y: {
      grid: true,
      gridAreaFill: ['rgba(0,0,0,0.04)', 'transparent'],  // Alternate fill to enhance readability
      gridLineWidth: 0,   // Hide grid lines themselves, only show area colors
    },
  },
});

// Can also be controlled using a function
axis: {
  y: {
    gridAreaFill: (datum, index) => index % 2 === 0 ? 'rgba(0,0,0,0.04)' : '',
  },
}
```

### Breaks - Skip Data Voids

```javascript
// When a certain range in the data far exceeds other values, use breaks to compress that interval
chart.options({
  type: 'interval',
  data: [
    { x: 'A', y: 100 },
    { x: 'B', y: 200 },
    { x: 'C', y: 95000 },  // Outlier, making other bars hard to see
    { x: 'D', y: 150 },
  ],
  encode: { x: 'x', y: 'y' },
  axis: {
    y: {
      breaks: [
        {
          start: 500,     // Break start point
          end: 90000,     // Break end point (skip this interval)
          gap: '3%',      // Break height as a percentage of canvas height
        },
      ],
    },
  },
});
```

### Dual Y-Axis

```javascript
// Implement dual axis using view container + different y scales
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'revenue' },
      axis: { y: { title: 'Revenue', position: 'left' } },
    },
    {
      type: 'line',
      encode: { x: 'month', y: 'growth' },
      scale: { y: { key: 'right' } },
      axis: { y: { title: 'Growth Rate', position: 'right' } },
    },
  ],
});
```

---

## Common Errors and Fixes

### Error 1: Placing `axis` inside `encode` or `scale`

```javascript
// ❌ Incorrect: `axis` is an independent top-level field
chart.options({
  encode: { x: 'month', y: 'value' },
  scale: { x: { title: 'Month' } },   // title does not belong in scale
});

// ✅ Correct: `axis` is a field at the same level as `encode`/`scale`
chart.options({
  encode: { x: 'month', y: 'value' },
  axis: { x: { title: 'Month' } },
});
```

### Error 2: Incorrect Style Property Name

```javascript
// ❌ Incorrect property name
axis: { x: { fontSize: 12 } }  // Does not exist

// ✅ Correct property name (with prefix)
axis: { x: { labelFontSize: 12 } }  // Label font size
axis: { x: { titleFontSize: 14 } }  // Title font size
```

### Error 3: Confusing Axis Title with Chart Title

```javascript
// ❌ Axis title written in title
title: { title: 'Month' }  // This is the chart title

// ✅ Axis title in axis
axis: { x: { title: 'Month' } }  // This is the X-axis title
```

### Error 4: Using tickFormatter to Format Label Text

```javascript
// ❌ Incorrect: tickFormatter returns a DisplayObject (graphic object), not a string
axis: {
  y: {
    tickFormatter: (v) => `${v / 1000}K`,  // ❌ Returning a string to tickFormatter is invalid
  },
}

// ✅ Correct: Use labelFormatter for label text formatting
axis: {
  y: {
    labelFormatter: (v) => `${v / 1000}K`,  // ✅ labelFormatter returns a string
  },
}
```

### Error 5: Formatting Labels or Receiving Scale Object in scale.tickMethod

```javascript
// ❌ Incorrect: tickMethod parameter is not a scale object, and the return value is not an array of objects
scale: {
  y: {
    tickMethod: (scale) => {              // ❌ Parameter is not a scale object
      return scale.ticks().map(v => ({    // ❌ scale.ticks() does not exist
        value: v, text: `${v}K`          // ❌ Cannot return an object, only number[]
      }));
    },
  },
}

// ✅ Correct: tickMethod signature is (min, max, count) => number[]
// Use labelFormatter for text formatting
scale: {
  y: {
    tickMethod: (min, max, count) => [100, 500, 1000, 5000, 10000],  // ✅ number[]
  },
},
axis: {
  y: {
    labelFormatter: (v) => `${v / 1000}K`,  // ✅ Text formatting in axis
  },
}
```

### Error 6: Using d3-format Strings to Concatenate Units in labelFormatter

`labelFormatter` and `tooltip.items[].valueFormatter` both support two forms: functions or d3-format strings. **d3-format strings only format numbers and cannot append text units**——`'.2f 元'`, `'.0f 米'` are invalid formats.

```javascript
// ❌ Error: Appending text units to d3-format strings
axis: {
  y: { labelFormatter: '.2f 元' },   // ❌ d3-format does not support concatenation, causing label errors
  x: { labelFormatter: '.0f 米' },   // ❌ Same issue
}

// ✅ Correct: Use function form when concatenating units
axis: {
  y: { labelFormatter: (v) => `${v.toFixed(2)} 元` },   // ✅ Function, allows concatenation of any text
  x: { labelFormatter: (v) => `${Math.round(v)} 米` },  // ✅ Function
}

// ✅ Pure number formatting (without units) can use d3-format strings
axis: {
  y: { labelFormatter: '.2f' },    // ✅ Two decimal places
  x: { labelFormatter: ',.0f' },  // ✅ Thousands separator for integers
  z: { labelFormatter: '.1%' },   // ✅ Percentage
}
```
### Error 7: Incorrect `labelFormatter` Callback Signature

The callback signature for `labelFormatter` should be `(datum, index, array) => string`, where:

- `datum`: The current scale value (usually a number or string)
- `index`: The index of the current scale
- `array`: An array of all scale values

```javascript
// ❌ Incorrect: Wrong parameter order or using non-existent parameters
axis: {
  x: {
    labelFormatter: (task, item) => {  // ❌ `item` parameter does not exist
      return `${item.data.stage}-${task}`;
    }
  }
}

// ✅ Correct: Using the correct parameter signature
axis: {
  x: {
    labelFormatter: (datum, index, array) => {
      // Note: Here, `datum` is the field value from the original data, not the entire data item
      return `${datum}`;  // Return a string
    }
  }
}

// ✅ Recommended Approach: Preprocess composite labels in `encode`
chart.options({
  encode: {
    x: (d) => `${d.stage} - ${d.task}`,  // Construct composite labels in `encode`
    y: 'start',
    y1: 'end'
  },
  axis: {
    x: {
      labelTransform: 'rotate(30)'  // Rotate labels to prevent overlap if needed
    }
  }
});
```

### Error 8: Confusion between `legend.labelFormatter` and `axis.labelFormatter`

Although both are used for formatting labels, they apply to different objects. `legend.labelFormatter` is used for legend labels, while `axis.labelFormatter` is used for axis tick labels.

```javascript
// ❌ Error: Using axis.labelFormatter in legend
legend: {
  color: {
    labelFormatter: '.0%'  // ❌ legend does not support axis's labelFormatter
  }
}

// ✅ Correct: Legend uses its own labelFormatter
legend: {
  color: {
    labelFormatter: (value) => `${Math.round(value)}%`  // ✅ Function form
  }
}
```

### Error 9: Confusion between `tooltip.valueFormatter` and `axis.labelFormatter`

`tooltip.valueFormatter` is used to format values in the tooltip, while `axis.labelFormatter` is used for axis labels.

```javascript
// ❌ Incorrect: Using axis.labelFormatter in tooltip.items
tooltip: {
  items: [
    { channel: 'y', labelFormatter: '.2f' }  // ❌ labelFormatter is not supported in tooltip.items
  ]
}

// ✅ Correct: Using valueFormatter in tooltip.items
tooltip: {
  items: [
    { channel: 'y', valueFormatter: '.2f' }  // ✅ Use valueFormatter
  ]
}
```

### Error 10: Improper `style.inset` Setting Causes Blank Rendering in Cell Charts

In `cell` type charts, `style.inset` controls the inner padding of cells. If set too large, it may cause cells to become invisible.

```javascript
// ❌ Error: inset set too large
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  style: {
    inset: 10  // ❌ inset is too large, may make rectangles invisible
  }
});

// ✅ Correct: Reasonable inset setting
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  style: {
    inset: 0.5  // ✅ Reasonable inset value
  }
});
```

### Error 11: Abnormal Layout Caused by Incorrect `legend.layout` Configuration

`legend.layout` uses the Flexbox layout model. Improper configuration can affect legend layout.

```javascript
// ❌ Error: Incorrect or unsupported value for justifyContent
legend: {
  color: {
    layout: { justifyContent: 'centered' }  // ❌ Unsupported value
  }
}

// ✅ Correct: Using a valid Flexbox value
legend: {
  color: {
    layout: { justifyContent: 'center' }  // ✅ Correct value
  }
}
```