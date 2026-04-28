---
id: "g2-mark-line-basic"
title: "G2 Basic Line Chart (Line Mark)"
description: |
  Create a line chart using Line Mark to display the trend of data changes over time or ordered categories.
  This article uses the Spec mode (chart.options({})), supporting common variants such as single series, multiple series, and smooth curves.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "line"
tags:
  - "line chart"
  - "trend"
  - "time series"
  - "Line"
  - "line chart"
  - "curve"
  - "multiple series"
  - "spec"

related:
  - "g2-mark-area-basic"
  - "g2-core-encode-channel"
  - "g2-scale-time"
  - "g2-interaction-tooltip"

use_cases:
  - "Displaying data trends over time"
  - "Comparing trends of multiple metrics or dimensions"
  - "Showing changes in continuous numerical values"

anti_patterns:
  - "Line charts are not intuitive with fewer data points (< 5), use bar charts instead"
  - "Unordered data (unordered categories) are not suitable for line charts"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/line/basic"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'line',
  data: [
    { month: 'Jan', value: 33 },
    { month: 'Feb', value: 78 },
    { month: 'Mar', value: 56 },
    { month: 'Apr', value: 91 },
    { month: 'May', value: 67 },
    { month: 'Jun', value: 45 },
  ],
  encode: { x: 'month', y: 'value' },
});

chart.render();
```

## Time Series Line Chart

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: [
    { date: new Date('2024-01-01'), value: 100 },
    { date: new Date('2024-02-01'), value: 130 },
    { date: new Date('2024-03-01'), value: 110 },
    { date: new Date('2024-04-01'), value: 160 },
    { date: new Date('2024-05-01'), value: 145 },
  ],
  encode: {
    x: 'date',     // Date type automatically uses Time Scale
    y: 'value',
  },
  axis: {
    x: {
      tickCount: 5,
      labelFormatter: 'YYYY-MM',  // Date formatting
    },
  },
});

chart.render();
```

## Multi-Series Line Chart

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

chart.options({
  type: 'line',
  data: [
    { month: 'Jan', type: 'Product A', value: 33 },
    { month: 'Jan', type: 'Product B', value: 55 },
    { month: 'Feb', type: 'Product A', value: 78 },
    { month: 'Feb', type: 'Product B', value: 62 },
    { month: 'Mar', type: 'Product A', value: 56 },
    { month: 'Mar', type: 'Product B', value: 89 },
    { month: 'Apr', type: 'Product A', value: 91 },
    { month: 'Apr', type: 'Product B', value: 74 },
  ],
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',   // color channel automatically splits multiple lines by type
  },
});

chart.render();
```

## Smooth Curve

```javascript
chart.options({
  type: 'line',
  data: [...],
  encode: {
    x: 'month',
    y: 'value',
    shape: 'smooth',    // 'line' | 'smooth' | 'hv' | 'vh' | 'hvh' | 'vhv'
  },
});
```

## Line + Data Points (Layer Combination)

```javascript
// Multiple Marks are overlaid using the children array in the Spec
chart.options({
  type: 'view',               // view container
   [...],
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'type' },
    },
    {
      type: 'point',
      encode: {
        x: 'month',
        y: 'value',
        color: 'type',
        shape: 'circle',
      },
      style: { r: 4 },
    },
  ],
});
```

## Line + Area Fill (Layer Combination)

```javascript
chart.options({
  type: 'view',
  data: [...],
  children: [
    {
      type: 'area',
      encode: { x: 'month', y: 'value' },
      style: { fillOpacity: 0.2 },
    },
    {
      type: 'line',
      encode: { x: 'month', y: 'value' },
      style: { stroke: '#1890ff', lineWidth: 2 },
    },
  ],
});
```

## With Tooltip and End Label

```javascript
chart.options({
  type: 'line',
  data: [...],
  encode: { x: 'month', y: 'value' },
  tooltip: {
    items: [{ field: 'value', name: 'Value' }],
  },
  labels: [
    {
      text: 'value',
      selector: 'last',    // Display label only on the last point
      style: { fontSize: 12, fill: '#1890ff' },
    },
  ],
});
```

## Wide Table Data + fold to Long Table

Each row in a wide table contains multiple metric columns. Use the `fold` transform to convert it into a long table and then plot multiple series:

```javascript
const wideData = [
  { date: '2024-01', DAU: 12000, MAU: 45000 },
  { date: '2024-02', DAU: 13500, MAU: 47000 },
  { date: '2024-03', DAU: 11800, MAU: 44500 },
];

chart.options({
  type: 'line',
  data: wideData,
  transform: [
    {
      type: 'fold',
      fields: ['DAU', 'MAU'],   // Columns to transform
      key: 'metric',             // New column name (stores original field names)
      value: 'count',            // New column name (stores original field values)
    },
  ],
  encode: {
    x: 'date',
    y: 'count',      // Use the value field name after fold
    color: 'metric', // Use the key field name after fold
  },
  labels: [
    { text: 'metric', selector: 'last', position: 'right' },
  ],
});
```

## Dual Y-Axis (Different Orders of Magnitude Series)

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data: revenueData,
      encode: { x: 'date', y: 'revenue', color: () => 'Revenue (10,000 Yuan)' },
      scale: { y: { key: 'revenue' } },   // Unique key → Independent y-axis
    },
    {
      type: 'line',
      data: userCountData,
      encode: { x: 'date', y: 'count', color: () => 'User Count' },
      scale: { y: { key: 'count' } },
      axis: { y: { position: 'right' } },  // Right y-axis
    },
  ],
});
```

## Multi-Series Tooltip Configuration

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value', color: 'series' },
  tooltip: {
    title: (d) => {
      const date = new Date(d.date);
      return `${date.getFullYear()}年${date.getMonth() + 1}月`;
    },
    items: [
      { field: 'series', name: 'Series' },
      { field: 'value', name: 'Value', valueFormatter: (v) => v.toLocaleString() },
    ],
  },
  interaction: [{ type: 'tooltip' }],
});
```
## Spec Field Quick Reference

| Field | Example Value | Description |
|------|--------|------|
| `encode.x` | `'month'` | X-axis field |
| `encode.y` | `'value'` | Y-axis field |
| `encode.color` | `'type'` | Color/series distinction |
| `encode.shape` | `'smooth'` | Line type |
| `style.lineWidth` | `2` | Line width |
| `style.stroke` | `'#f00'` | Line color (fixed) |
| `labels` | `[{ text: 'value', selector: 'last' }]` | Data labels |
| `tooltip` | `{ items: [{ field: 'value' }] }` | Tooltip |

## Common Errors and Fixes

### Error 1: Missing color channel for multi-series data
```javascript
// ❌ Incorrect: Multi-series data without color, all points are incorrectly connected into a messy line
chart.options({
  type: 'line',
  data: multiSeriesData,
  encode: { x: 'month', y: 'value' },  // Missing color!
});

// ✅ Correct
chart.options({
  type: 'line',
  data: multiSeriesData,
  encode: { x: 'month', y: 'value', color: 'type' },
});
```

### Error 2: Time Field is a String
```javascript
// ❌ Not Recommended: String time axis sorting may be incorrect
const data = [{ date: '2024-03-01', value: 100 }];

// ✅ Correct: Convert to Date object, or explicitly configure scale type
const data = [{ date: new Date('2024-03-01'), value: 100 }];
// or:
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
});
```

### Error 3: Forgetting to Use the View Container for Multiple Mark Overlays
```javascript
// ❌ Incorrect: Directly calling options twice will overwrite
chart.options({ type: 'line', ... });
chart.options({ type: 'point', ... });  // Overwrites the above!

// ✅ Correct: Use type: 'view' + children array
chart.options({
  type: 'view',
  data: [...],
  children: [
    { type: 'line', encode: { x: 'month', y: 'value' } },
    { type: 'point', encode: { x: 'month', y: 'value' }, style: { r: 4 } },
  ],
});
```