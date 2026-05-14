---
id: "g2-mark-area-stacked"
title: "G2 Stacked Area Chart"
description: |
  Use Area Mark with stackY Transform to create a stacked area chart,
  simultaneously displaying the trend changes of each series and the cumulative effect of the total amount. The area of each series starts filling from the top of the previous series.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "area"
tags:
  - "stacked area chart"
  - "stacked area"
  - "stackY"
  - "multi-series"
  - "trend"
  - "total amount"
  - "spec"

related:
  - "g2-mark-area-basic"
  - "g2-transform-stacky"
  - "g2-mark-interval-stacked"

use_cases:
  - "Display the total amount changes of multiple series over time"
  - "Focus on both individual series trends and overall scale"
  - "Scenarios like traffic sources, revenue composition, etc."

anti_patterns:
  - "Colors become difficult to distinguish when there are more than 5 series"
  - "Switch to line charts when precise comparison of individual series changes is needed (non-unified baselines)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/area/stacked"
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
    { month: 'Jan', type: 'A', value: 100 },
    { month: 'Jan', type: 'B', value: 200 },
    { month: 'Jan', type: 'C', value: 150 },
    { month: 'Feb', type: 'A', value: 120 },
    { month: 'Feb', type: 'B', value: 180 },
    { month: 'Feb', type: 'C', value: 160 },
    { month: 'Mar', type: 'A', value: 90  },
    { month: 'Mar', type: 'B', value: 220 },
    { month: 'Mar', type: 'C', value: 130 },
  ],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
});

chart.render();
```

## Smooth Stacked Area Chart

```javascript
chart.options({
  type: 'area',
  data,
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',
    shape: 'smooth',
  },
  transform: [{ type: 'stackY' }],
  style: { fillOpacity: 0.85 },
});
```

## Stacked Area + Line Stroke

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'area',
      encode: { x: 'month', y: 'value', color: 'type' },
      transform: [{ type: 'stackY' }],
      style: { fillOpacity: 0.7 },
    },
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'type', series: 'type' },
      transform: [{ type: 'stackY' }],
      style: { lineWidth: 1.5 },
    },
  ],
});
```

## Percentage Stacked Area Chart

```javascript
chart.options({
  type: 'area',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    { type: 'stackY' },
    { type: 'normalizeY' },
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});
```

## Common Errors and Fixes

### Error: Forgetting stackY causes series to overlap each other
```javascript
// ❌ Error: Each series area starts from y=0, overlapping each other
chart.options({
  type: 'area',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  // No transform!
});

// ✅ Correct
chart.options({
  type: 'area',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
});
```