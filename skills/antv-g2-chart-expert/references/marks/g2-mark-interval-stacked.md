---
id: "g2-mark-interval-stacked"
title: "G2 Stacked Bar Chart"
description: |
  Use Interval Mark with stackY Transform to create a stacked bar chart.
  In Spec mode, add the stackY transformation through the transform array.
  Stacked bar charts are used to show the relationship between parts and the whole, as well as the proportion changes of sub-categories in the total amount.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "interval"
tags:
  - "stacked bar chart"
  - "stacked bar"
  - "StackY"
  - "stacking"
  - "part-to-whole"
  - "multi-series"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-interval-grouped"
  - "g2-mark-interval-normalized"
  - "g2-transform-stacky"

use_cases:
  - "Display the composition of multiple sub-categories at each time point"
  - "Compare the proportions of sub-items in different categories"
  - "Visualize the relationship between the total amount and sub-items"

anti_patterns:
  - "Stacked charts are difficult to read when sub-categories exceed 5-7, consider using grouped bar charts"
  - "Not suitable for comparing trends of individual sub-categories (difficult to align baselines)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/bar/stacked"
---

## Core Concepts

Stacked Bar Chart = `type: 'interval'` + `transform: [{ type: 'stackY' }]`.  
`stackY` aggregates multiple values at the same x-position to calculate the y0/y1 range,  
allowing sub-categories to stack vertically in sequence.

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
    { month: 'Feb', type: 'A', value: 120 },
    { month: 'Feb', type: 'B', value: 180 },
    { month: 'Feb', type: 'C', value: 160 },
    { month: 'Mar', type: 'A', value: 90 },
    { month: 'Mar', type: 'B', value: 220 },
    { month: 'Mar', type: 'C', value: 130 },
  ],
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',
  },
  transform: [{ type: 'stackY' }],   // Key: Stack transformation
});

chart.render();
```

## Stacked Column Chart with Data Labels

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  labels: [
    {
      text: 'value',
      position: 'inside',     // Label inside the column
      style: { fontSize: 11, fill: 'white' },
    },
  ],
});
```

## Stacked Bar Chart (Horizontal)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { transform: [{ type: 'transpose' }] },   // Transpose to horizontal bar chart
});
```

## Controlling Stack Order

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY', orderBy: 'value' }],  // Sort stacking by value size
});
```

## Percentage Stacked Bar Chart

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    { type: 'stackY' },
    { type: 'normalizeY' },  // Normalize to [0, 1], i.e., percentage stacking
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});
```

## Common Errors and Fixes

### Error 1: Forgetting to transform stackY
```javascript
// ❌ Incorrect: Multiple series data will not stack automatically, and bars will overlap at the same position
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  // Missing transform!
});

// ✅ Correct: Must explicitly declare stackY
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],   // Required!
});
```

### Error 2: Duplicate Data Rows for the Same (x, color) Combination
```javascript
// ❌ Incorrect: Two data entries for the same month and type, causing stackY to overlap repeatedly
const badData = [
  { month: 'Jan', type: 'A', value: 100 },
  { month: 'Jan', type: 'A', value: 50 },  // Duplicate!
];

// ✅ Correct: Each (x, color) combination has only one data entry; aggregate at the data layer if merging is required
```

### Error 3: `transform` written as an object instead of an array
```javascript
// ❌ Incorrect: `transform` must be an array
chart.options({ transform: { type: 'stackY' } });

// ✅ Correct: `transform` is an array, supporting multiple chained transformations
chart.options({ transform: [{ type: 'stackY' }] });
```