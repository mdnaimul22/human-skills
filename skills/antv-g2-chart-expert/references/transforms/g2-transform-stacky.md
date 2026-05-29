---
id: "g2-transform-stacky"
title: "G2 StackY Stack Transform"
description: |
  StackY is a Mark Transform in G2 v5 used to implement data stacking,
  stacking multiple values at the same x position sequentially to generate a y0/y1 range.
  Configured in the transform array (at the same level as data and encode), it is a core dependency for stacked bar charts, stacked area charts, and pie charts.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "StackY"
  - "stack"
  - "stackY"
  - "mark transform"
  - "stacked bar chart"
  - "stacked area chart"
  - "spec"

related:
  - "g2-mark-interval-stacked"
  - "g2-mark-area-stacked"
  - "g2-transform-normalizey"
  - "g2-transform-dodgex"
  - "g2-data-fold"

use_cases:
  - "Create stacked bar charts"
  - "Create stacked area charts"
  - "Create pie charts (with theta coordinate system)"

difficulty: "beginner"
completeness: "partial"
created: "2024-01-01"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/stack-y"
---

## Core Concepts

**StackY is a Mark Transform, not a Data Transform**

- Mark transform is configured in the `transform` array (at the same level as `data` and `encode`)
- Executed during the mark rendering process, modifying visual channel values
- **Do not** place it in `data.transform`

StackY performs cumulative calculations on data within each x group:
- Input: `y` values (raw numerical values of sub-categories)
- Output: `y0` (bottom position) and ` y1` (top position), driving the start and end positions of bars/areas

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],  // ✅ Mark Transform: at the same level as data/encode
});
```

## Basic Usage (Spec Mode)

```javascript
import { Chart } from '@antv/g2';

// Stacked Bar Chart
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', type: 'A', value: 100 },
    { month: 'Jan', type: 'B', value: 200 },
    { month: 'Feb', type: 'A', value: 120 },
    { month: 'Feb', type: 'B', value: 180 },
  ],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],   // Declare stacking transformation
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    {
      type: 'stackY',
      orderBy: null,     // null | 'value' | 'sum' | 'series' — Controls the stacking order
      reverse: false,    // Whether to reverse the stacking order
      y: 'y',            // Input y channel name (default 'y')
      y1: 'y1',          // Output bottom channel name (default 'y1')
    },
  ],
});
```

## Combination with normalizeY (Percentage Stacking)

```javascript
// transform array supports multiple transformations in a chain
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    { type: 'stackY' },       // Stack first
    { type: 'normalizeY' },   // Then normalize to [0, 1]
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});
```

## For Pie Charts (with theta coordinate system)

```javascript
chart.options({
  type: 'interval',
  data: [
    { type: 'Category One', value: 40 },
    { type: 'Category Two', value: 30 },
    { type: 'Category Three', value: 30 },
  ],
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],           // Convert values to angular intervals
  coordinate: { type: 'theta', outerRadius: 0.8 },
});
```

## For Stacked Area Charts

```javascript
chart.options({
  type: 'area',
  data: [...],
  encode: { x: 'date', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
});
```

## Common Errors and Fixes

### Error 1: stackY placed in data.transform

```javascript
// ❌ Incorrect: stackY is a Mark Transform and cannot be placed in data.transform
chart.options({
  type: 'interval',
  {
    type: 'inline',
    value: data,
    transform: [{ type: 'stackY' }],  // ❌ Incorrect location
  },
});

// ✅ Correct: stackY placed in mark's transform (same level as data/encode)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],  // ✅ Correct
});
```

### Error 2: `transform` written as an object instead of an array
```javascript
// ❌ Incorrect: `transform` must be an array
chart.options({ transform: { type: 'stackY' } });

// ✅ Correct
chart.options({ transform: [{ type: 'stackY' }] });
```

### Error 3: Forgot to stackY in Pie Chart
```javascript
// ❌ Incorrect: No stackY in theta coordinate, all sectors start from 0 and completely overlap
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  coordinate: { type: 'theta' },
  // Missing transform!
});

// ✅ Correct
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],   // Mandatory!
  coordinate: { type: 'theta' },
});
```

### Error 4: Multiple Series Data Not Stacked Directly Displayed Leading to Overlap
```javascript
// ❌ Error: Multiple type intervals without stackY or dodgeX, bars stacked at the same position
chart.options({
  type: 'interval',
  data: multiTypeData,
  encode: { x: 'month', y: 'value', color: 'type' },
  // Neither stackY (stack) nor dodgeX (dodge) is applied
});

// ✅ Stacked Display
chart.options({ transform: [{ type: 'stackY' }], ... });

// ✅ Dodged Display
chart.options({ transform: [{ type: 'dodgeX' }], ... });
```