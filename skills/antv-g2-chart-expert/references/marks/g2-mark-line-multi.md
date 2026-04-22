---
id: "g2-mark-line-multi"
title: "G2 Multi-Series Line Chart"
description: |
  Implement multi-series line charts by encoding categorical fields through the color channel, where each line represents a category.
  G2 automatically generates independent lines for each color value.
  Commonly used for trend comparisons and displaying multiple metrics over time.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "line chart"
  - "multi-series"
  - "line"
  - "time series"
  - "trend comparison"
  - "multi-line"

related:
  - "g2-mark-line-basic"
  - "g2-mark-area-stacked"
  - "g2-transform-select"

use_cases:
  - "Sales trend comparison for multiple products"
  - "Temperature changes over time across multiple regions"
  - "Multi-metric KPI line comparison"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/line/"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', city: 'Beijing', temp: -3 },
  { month: 'Feb', city: 'Beijing', temp: 0 },
  { month: 'Mar', city: 'Beijing', temp: 9 },
  { month: 'Apr', city: 'Beijing', temp: 18 },
  { month: 'Jan', city: 'Shanghai', temp: 5 },
  { month: 'Feb', city: 'Shanghai', temp: 7 },
  { month: 'Mar', city: 'Shanghai', temp: 13 },
  { month: 'Apr', city: 'Shanghai', temp: 20 },
  { month: 'Jan', city: 'Guangzhou', temp: 15 },
  { month: 'Feb', city: 'Guangzhou', temp: 16 },
  { month: 'Mar', city: 'Guangzhou', temp: 21 },
  { month: 'Apr', city: 'Guangzhou', temp: 26 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: {
    x: 'month',
    y: 'temp',
    color: 'city',   // Key: Color by city, automatically generating multiple lines
  },
  style: { lineWidth: 2 },
  legend: { color: { position: 'top' } },
});

chart.render();
```

## Line + Scatter Combination (Highlighting Data Points)

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'city' },
      style: { lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { x: 'month', y: 'value', color: 'city', shape: 'circle' },
      style: { r: 4, lineWidth: 1.5, fill: '#fff' },
    },
  ],
});
```

## Line + End Label

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data,
      encode: { x: 'month', y: 'value', color: 'city' },
    },
    {
      type: 'text',
      data,
      encode: {
        x: 'month',
        y: 'value',
        color: 'city',
        text: 'city',
      },
      transform: [{ type: 'selectX', selector: 'last' }],  // Only select the end of each line
      style: { textAnchor: 'start', dx: 6, fontSize: 12 },
    },
  ],
});
```

## Smooth Curve

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  style: {
    lineWidth: 2,
    shape: 'smooth',   // Smooth curve (replaces line segments)
  },
});
```

## Common Errors and Fixes

### Error: Multiple Series Data Using Wide Table Format - Should Use Long Table Format
```javascript
// ❌ Wrong: Wide table format, G2 cannot automatically color by series
const wrongData = [
  { month: 'Jan', 北京: -3, 上海: 5, 广州: 15 },
  { month: 'Feb', 北京: 0,  上海: 7, 广州: 16 },
];

// ✅ Correct: Long table format (one data point per series per record)
const correctData = [
  { month: 'Jan', city: '北京', value: -3 },
  { month: 'Jan', city: '上海', value: 5 },
  // ...
];
chart.options({
  encode: { x: 'month', y: 'value', color: 'city' },  // ✅ color binds to categorical field
});
```