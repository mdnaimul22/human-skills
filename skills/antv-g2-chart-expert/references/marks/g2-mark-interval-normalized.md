---
id: "g2-mark-interval-normalized"
title: "G2 Percentage Stacked Bar Chart"
description: |
  Use Interval Mark with stackY + normalizeY Transform to create a percentage stacked bar chart.
  The total height of each group of bars is normalized to 100%, focusing on the proportion changes of sub-categories,
  eliminating the interference of total quantity differences, and facilitating cross-group comparison of structural distribution.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "interval"
tags:
  - "percentage stacked"
  - "normalized"
  - "normalizeY"
  - "proportion"
  - "structural analysis"
  - "100% stacked bar"
  - "spec"

related:
  - "g2-mark-interval-stacked"
  - "g2-mark-interval-grouped"
  - "g2-transform-normalizey"
  - "g2-transform-stacky"

use_cases:
  - "Comparing the proportion distribution of sub-categories across different groups"
  - "Focusing on structural changes rather than absolute values"
  - "Eliminating total quantity differences to highlight proportions"

anti_patterns:
  - "When absolute value changes are needed, use a regular stacked bar chart instead"
  - "When there are only two sub-categories, a simple line chart or area chart is more intuitive"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/bar/normalized"
---

## Core Concepts

Percentage Stacking = `stackY` + `normalizeY` executed in sequence:
1. `stackY`: First, stack the values of each sub-category into the y0/y1 range
2. `normalizeY`: Then, normalize the y values of each group to [0, 1]

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', type: 'A', value: 100 },
    { month: 'Jan', type: 'B', value: 200 },
    { month: 'Jan', type: 'C', value: 150 },
    { month: 'Feb', type: 'A', value: 80  },
    { month: 'Feb', type: 'B', value: 220 },
    { month: 'Feb', type: 'C', value: 100 },
    { month: 'Mar', type: 'A', value: 130 },
    { month: 'Mar', type: 'B', value: 180 },
    { month: 'Mar', type: 'C', value: 90  },
  ],
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',
  },
  transform: [
    { type: 'stackY' },      // 1. Stack first
    { type: 'normalizeY' },  // 2. Then normalize to percentage
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});

chart.render();
```

## With Percentage Data Labels

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }, { type: 'normalizeY' }],
  labels: [
    {
      text: (d) => `${(d.value * 100).toFixed(1)}%`,  // Note: After normalization, value is already between 0-1
      position: 'inside',
      style: {
        fill: 'white',
        fontSize: 11,
        fontWeight: 'bold',
      },
      // Filter out labels with small percentages (to avoid clutter)
      filter: (d) => d.value > 0.05,
    },
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});
```

## Horizontal Percentage Stacked Bar Chart

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }, { type: 'normalizeY' }],
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: {
    x: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});
```

## Common Errors and Fixes

### Error: Transform Order Reversed
```javascript
// ❌ Incorrect: normalizeY before stackY, resulting in incorrect output
chart.options({
  transform: [{ type: 'normalizeY' }, { type: 'stackY' }],
});

// ✅ Correct: stackY must come before normalizeY
chart.options({
  transform: [{ type: 'stackY' }, { type: 'normalizeY' }],
});
```