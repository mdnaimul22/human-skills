---
id: "g2-mark-area-basic"
title: "G2 Basic Area Chart (Area Mark)"
description: |
  Create an area chart using Area Mark, filling the area below the line in a line chart,
  to emphasize the magnitude and trend of the data. This article uses the Spec mode, covering single series, gradient fill, and other usage scenarios.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "area"
tags:
  - "area chart"
  - "Area"
  - "area chart"
  - "trend"
  - "magnitude"
  - "fill"
  - "spec"

related:
  - "g2-mark-line-basic"
  - "g2-mark-area-stacked"
  - "g2-core-encode-channel"

use_cases:
  - "Display the trend of numerical values over time while emphasizing magnitude"
  - "Use as background fill when overlaying multiple lines"
  - "Compare the total distribution of multiple series"

anti_patterns:
  - "In multi-series area charts (without stacking), series may overlap each other; consider using stacked area charts or line charts instead"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/area/basic"
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
  type: 'area',
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

## Gradient Filled Area Chart

```javascript
chart.options({
  type: 'area',
  data,
  encode: { x: 'month', y: 'value' },
  style: {
    fill: 'linear-gradient(180deg, #1890ff 0%, rgba(24,144,255,0.1) 100%)',
    fillOpacity: 0.8,
  },
});
```

## Area Chart + Line (Overlay)

```javascript
// Area provides background volume, line provides precise trend
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'area',
      encode: { x: 'month', y: 'value' },
      style: { fillOpacity: 0.2, fill: '#1890ff' },
    },
    {
      type: 'line',
      encode: { x: 'month', y: 'value' },
      style: { stroke: '#1890ff', lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { x: 'month', y: 'value', shape: 'circle' },
      style: { fill: '#1890ff', r: 4 },
    },
  ],
});
```

## Smooth Curve Area Chart

```javascript
chart.options({
  type: 'area',
  data,
  encode: {
    x: 'month',
    y: 'value',
    shape: 'smooth',    // Smooth interpolation
  },
  style: { fillOpacity: 0.6 },
});
```

## Time Series Area Chart

```javascript
chart.options({
  type: 'area',
  data: [
    { date: new Date('2024-01'), value: 100 },
    { date: new Date('2024-02'), value: 130 },
    { date: new Date('2024-03'), value: 90  },
    { date: new Date('2024-04'), value: 160 },
    { date: new Date('2024-05'), value: 145 },
  ],
  encode: { x: 'date', y: 'value' },
  axis: {
    x: { labelFormatter: 'YYYY-MM' },
  },
});
```

## Common Errors and Fixes

### Error: Multiple Series Area Charts Without stackY Result in Overlapping
```javascript
// ❌ Problem: Multiple series areas overlap, with later series obscuring earlier ones
chart.options({
  type: 'area',
  data: multiSeriesData,
  encode: { x: 'month', y: 'value', color: 'type' },
  // Without stackY, each series starts stacking from y=0, causing mutual overlap
});

// ✅ Solution 1: Stacked Area Chart (see g2-mark-area-stacked)
chart.options({
  type: 'area',
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
});

// ✅ Solution 2: Switch to Line Chart for Multi-Series Comparison
chart.options({
  type: 'line',
  encode: { x: 'month', y: 'value', color: 'type' },
});
```