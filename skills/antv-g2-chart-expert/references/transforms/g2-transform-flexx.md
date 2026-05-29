---
id: "g2-transform-flexx"
title: "G2 FlexX Elastic Width Transform (Mosaic Chart / Uneven Bar Width)"
description: |
  flexX dynamically adjusts the flex property of the x-axis scale based on data values, making each bar's width proportional to its value.
  Commonly used in Mosaic charts (Marimekko chart): bar width represents one dimension, and bar height represents another.
  Specify the field controlling the width via field, and the aggregation method via reducer.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "flexX"
  - "uneven bar width"
  - "mosaic chart"
  - "Marimekko"
  - "elastic width"
  - "transform"

related:
  - "g2-transform-stacky"
  - "g2-mark-interval-stacked"

use_cases:
  - "Mosaic Chart (Dual-dimension proportion: bar width × bar height)"
  - "Uneven Bar Chart (bar width represents sample size/weight)"
  - "Market Share Chart (width = market size, height = proportion)"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/flex-x"
---

## Minimum Viable Example (Mosaic Plot)

```javascript
import { Chart } from '@antv/g2';

// Mosaic Plot: x category, y sub-category proportion, value controls bar width (market size)
const data = [
  { region: 'North China', type: 'Online', revenue: 300, share: 0.6 },
  { region: 'North China', type: 'Offline', revenue: 300, share: 0.4 },
  { region: 'East China', type: 'Online', revenue: 500, share: 0.7 },
  { region: 'East China', type: 'Offline', revenue: 500, share: 0.3 },
  { region: 'South China', type: 'Online', revenue: 200, share: 0.5 },
  { region: 'South China', type: 'Offline', revenue: 200, share: 0.5 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data,
  encode: {
    x: 'region',
    y: 'share',
    color: 'type',
  },
  transform: [
    {
      type: 'flexX',
      field: 'revenue',    // Field controlling bar width
      reducer: 'sum',      // Aggregation method (same x category may have multiple rows, requires sum)
    },
    { type: 'stackY' },   // Then stack in the y direction (percentage)
  ],
  axis: {
    y: { labelFormatter: (v) => `${(v * 100).toFixed(0)}%` },
  },
});

chart.render();
```

## Configuration Options

```javascript
transform: [
  {
    type: 'flexX',
    field: 'sampleSize',  // Field name controlling width (weight of each x category)
    channel: 'y',         // Channel value used to calculate elasticity (default 'y')
    reducer: 'sum',       // Aggregation method for field values under the same x category ('sum' is most commonly used)
  },
]
```

## Common Errors and Fixes

### Error: Incorrect Order of flexX and stackY—stackY Should Come Before flexX
```javascript
// ❌ Incorrect: flexX should come before stackY
transform: [
  { type: 'stackY' },   // ❌ stackY is executed first, flexX adjusts width later, causing proportion errors
  { type: 'flexX', field: 'revenue' },
]

// ✅ Correct Order: flexX (set elastic width) first, then stackY (stack height)
transform: [
  { type: 'flexX', field: 'revenue', reducer: 'sum' },  // ✅ Set elastic width first
  { type: 'stackY' },                                     // ✅ Then stack
]
```

### Error: No Reducer Set - Inconsistent Width Calculation When Multiple Rows Share the Same X Value
```javascript
// ❌ No reducer set, multiple rows (online/offline) in the same region, flexX doesn't know how to aggregate width
transform: [{ type: 'flexX', field: 'revenue' }]  // ❌ Missing reducer

// ✅ Set reducer: 'sum' to sum the field for the same x
transform: [{ type: 'flexX', field: 'revenue', reducer: 'sum' }]  // ✅
```