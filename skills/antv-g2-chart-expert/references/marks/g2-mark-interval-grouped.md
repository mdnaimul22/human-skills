---
id: "g2-mark-interval-grouped"
title: "G2 Grouped Bar Chart"
description: |
  Use Interval Mark with dodgeX Transform to create a grouped bar chart.
  A grouped bar chart displays multiple series of data within the same category side by side, facilitating horizontal comparison of absolute values across sub-categories.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "interval"
tags:
  - "grouped bar chart"
  - "grouped bar"
  - "dodgeX"
  - "multiple series"
  - "side by side"
  - "comparison"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-interval-stacked"
  - "g2-transform-dodgex"

use_cases:
  - "Comparing absolute values of multiple sub-metrics within the same category"
  - "Sales comparison across different product lines over various time periods"
  - "Side-by-side display of multi-dimensional data"

anti_patterns:
  - "Bars become too thin and readability decreases when the number of series exceeds 4-5"
  - "Use a stacked bar chart when focusing on proportional relationships"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/bar/grouped"
---

## Core Concepts

Grouped Bar Chart = `type: 'interval'` + `transform: [{ type: 'dodgeX'}]`.  
`dodgeX` arranges multiple series of bars at the same x-position in a staggered manner horizontally, preventing overlap.

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
    { month: 'Jan', type: 'Product A', value: 100 },
    { month: 'Jan', type: 'Product B', value: 130 },
    { month: 'Jan', type: 'Product C', value: 90  },
    { month: 'Feb', type: 'Product A', value: 120 },
    { month: 'Feb', type: 'Product B', value: 100 },
    { month: 'Feb', type: 'Product C', value: 150 },
    { month: 'Mar', type: 'Product A', value: 80  },
    { month: 'Mar', type: 'Product B', value: 140 },
    { month: 'Mar', type: 'Product C', value: 110 },
  ],
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',
  },
  transform: [{ type: 'dodgeX' }],   // Key: Grouping transformation
});

chart.render();
```

## Grouped Bar Chart (Horizontal)

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

## Grouped Bar Chart + Data Labels

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
  labels: [
    {
      text: 'value',
      position: 'outside',
      style: { fontSize: 11 },
    },
  ],
});
```

## Adjust Group Spacing

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    {
      type: 'dodgeX',
      padding: 0.1,       // Intra-group bar spacing (0-1), default 0
      paddingOuter: 0.1,  // Inter-group spacing
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Forgetting dodgeX, Bars Overlapping
```javascript
// ❌ Incorrect: Multiple series data without dodgeX, bars stacking at the same position
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  // Missing transform!
});

// ✅ Correct
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
});
```

### Error 2: Using `stackY` and `dodgeX` Simultaneously
```javascript
// ❌ Incorrect: Two transformations conflict, leading to unpredictable behavior
chart.options({
  transform: [{ type: 'stackY' }, { type: 'dodgeX' }],
});

// ✅ Correct: Stacking and dodging are mutually exclusive, choose one
chart.options({ transform: [{ type: 'stackY' }] });   // Stacking
chart.options({ transform: [{ type: 'dodgeX' }] });   // Dodging
```