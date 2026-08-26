---
id: "g2-transform-sorty"
title: "G2 SortY Transformation for Sorting by Y Values"
description: |
  sortY sorts data records by y values within each x group, commonly used in stacked charts to control the stacking order of categories,
  ensuring larger values are at the bottom or top. sortX sorts global data by x channel values,
  while sortColor sorts by color channel values.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "sortY"
  - "sortX"
  - "sorting"
  - "stacking order"
  - "transform"

related:
  - "g2-transform-sortx"
  - "g2-transform-stacky"
  - "g2-mark-interval-stacked"

use_cases:
  - "Controlling stacking order in stacked bar charts (larger values at the bottom)"
  - "Ensuring visually stable stacked layouts"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/sort"
---

## Minimum Viable Example (Stacked Bar Chart Sorting)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', type: 'A', value: 100 },
  { month: 'Jan', type: 'B', value: 200 },
  { month: 'Jan', type: 'C', value: 50 },
  { month: 'Feb', type: 'A', value: 120 },
  { month: 'Feb', type: 'B', value: 80 },
  { month: 'Feb', type: 'C', value: 180 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    { type: 'sortY', reverse: false },  // Sort each x group in ascending order by y value
    { type: 'stackY' },                 // Then stack (larger values on top)
  ],
});

chart.render();
```

## sortX (Global Sorting by X Value)

```javascript
// Bar chart sorted in descending order by value (maximum value at the top)
chart.options({
  type: 'interval',
  data: rankingData,
  encode: { x: 'name', y: 'value' },
  transform: [
    { type: 'sortX', by: 'y', reverse: true },  // Sort in descending order by y value
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

## Configuration Options

```javascript
// sortY: Sort within each x group
transform: [
  {
    type: 'sortY',
    reverse: false,   // false = ascending (smaller values first), true = descending (larger values first), default false
    by: 'y',          // sorting channel, default 'y'
  },
]

// sortX: Global sorting by x channel values
transform: [
  {
    type: 'sortX',
    by: 'y',          // sorting basis: 'x' (by x values) or 'y' (by y values),
    reverse: true,    // true = descending, default false
  },
]
```

## Common Errors and Fixes

### Error: sortY Executed After stackY—Y Values Changed After Stacking, Incorrect Sorting Criteria
```javascript
// ❌ Incorrect Order: Y values after stackY are cumulative, sortY sorts based on cumulative values
transform: [
  { type: 'stackY' },  // ❌ Stack first
  { type: 'sortY' },   // ❌ Sort after, at this point y is already cumulative
]

// ✅ Correct: Sort Before Stacking
transform: [
  { type: 'sortY' },   // ✅ Sort by original y values first
  { type: 'stackY' },  // ✅ Stack after (stacking order follows sorting result)
]
```