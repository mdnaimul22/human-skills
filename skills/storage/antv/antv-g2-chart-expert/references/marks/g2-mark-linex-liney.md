---
id: "g2-mark-linex-liney"
title: "G2 LineX / LineY Reference Lines"
description: |
  lineX draws vertical reference lines (specified by x values), lineY draws horizontal reference lines (specified by y values).
  Commonly used for annotating mean lines, target lines, threshold lines, etc.,
  typically placed in the same view's children as the main chart.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "lineX"
  - "lineY"
  - "reference lines"
  - "mean lines"
  - "target lines"
  - "annotation"
  - "marking"

related:
  - "g2-comp-annotation"
  - "g2-mark-rangex"
  - "g2-mark-line-basic"

use_cases:
  - "Drawing X/Y mean lines in scatter plots"
  - "Adding target value horizontal reference lines"
  - "Marking threshold warning lines"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/annotation/line/"
---

## Minimum Viable Example (Mean Reference Line)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', value: 83 },
  { month: 'Feb', value: 60 },
  { month: 'Mar', value: 95 },
  { month: 'Apr', value: 72 },
  { month: 'May', value: 110 },
];

const avg = data.reduce((sum, d) => sum + d.value, 0) / data.length;

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'view',
  data,
  children: [
    // Main bar chart
    {
      type: 'interval',
      encode: { x: 'month', y: 'value', color: 'month' },
    },
    // Horizontal mean reference line
    {
      type: 'lineY',
      data: [{ y: avg }],  // Reference line's y value
      encode: { y: 'y' },
      style: {
        stroke: '#F4664A',
        lineWidth: 1.5,
        lineDash: [6, 3],  // Dashed line style
      },
      labels: [
        {
          text: `Mean: ${avg.toFixed(1)}`,
          position: 'right',
          style: { fill: '#F4664A', fontSize: 12 },
        },
      ],
    },
  ],
});

chart.render();
```

## lineX (Vertical Reference Line)

```javascript
// Add X-axis mean line in a scatter plot
const meanX = data.reduce((sum, d) => sum + d.x, 0) / data.length;

{
  type: 'lineX',
  data: [{ x: meanX }],
  encode: { x: 'x' },
  style: { stroke: '#5B8FF9', lineWidth: 1.5, lineDash: [4, 4] },
  labels: [{ text: `x̄=${meanX.toFixed(1)}`, position: 'top' }],
}
```

## Target Line (Fixed Value)

```javascript
{
  type: 'lineY',
  data: [{ y: 100 }],    // Fixed target value 100
  encode: { y: 'y' },
  style: {
    stroke: '#52c41a',
    lineWidth: 2,
  },
  labels: [
    { text: 'Target Line 100', position: 'right', style: { fill: '#52c41a' } },
  ],
}
```

## Common Errors and Fixes

### ❌ Error: Using Non-existent `ruleX` / `ruleY` Types
```javascript
// ❌ Error: `ruleX`, `ruleY` are Vega-Lite concepts and do not exist in G2
chart.options({ type: 'ruleX', ... });
chart.options({ type: 'ruleY', ... });

// ✅ Correct: Use `lineX` / `lineY` in G2
chart.options({ type: 'lineX', data: [{ x: 5 }], encode: { x: 'x' } });
chart.options({ type: 'lineY', data: [{ y: 100 }], encode: { y: 'y' } });
```

### Error: Inconsistent y field name in data and encode.y
```javascript
// ❌ Error: The field in the data is 'value', but encode.y is written as 'y'
chart.options({
  type: 'lineY',
  data: [{ value: 100 }],
  encode: { y: 'y' },     // ❌ Incorrect field name, cannot find 'y' field
});

// ✅ Correct: Field name matches the data
chart.options({
  type: 'lineY',
  data: [{ value: 100 }],
  encode: { y: 'value' }, // ✅
});
// Or use 'y' field name directly:
chart.options({
  type: 'lineY',
  data: [{ y: 100 }],
  encode: { y: 'y' },     // ✅ Consistent field name
});
```

### Error: lineY placed outside the view - does not share the main chart scale, causing position offset
```javascript
// ❌ The reference line is not in the same view as the main chart, and the y-axis range is not shared
chart.options({
  type: 'view',
  children: [
    { type: 'interval', encode: { x: 'month', y: 'sales' } },
  ],
});
// Adding lineY separately (not in children) - this will not work

// ✅ The reference line must be placed in the children array of the same view
chart.options({
  type: 'view',
  children: [
    { type: 'interval', encode: { x: 'month', y: 'sales' } },
    { type: 'lineY', data: [{ y: 100 }], encode: { y: 'y' } },  // ✅
  ],
});
```