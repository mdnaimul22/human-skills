---
id: "g2-transform-binx"
title: "G2 BinX Binning Transform (Histogram)"
description: |
  BinX groups continuous x values into specified bins and automatically counts the number of records (or aggregated values) in each bin. 
  It is the core Transform for creating frequency histograms. When combined with Interval Mark, it can directly generate histograms using raw data.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "BinX"
  - "Histogram"
  - "histogram"
  - "binning"
  - "distribution"
  - "frequency"
  - "transform"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-transform-stacky"

use_cases:
  - "Displaying frequency distribution of continuous numerical data"
  - "Exploring data distribution patterns (normal, skewed, etc.)"

anti_patterns:
  - "BinX is not needed for discrete categorical data; use interval directly instead"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/bin-x"
---

## Minimum Viable Example (Histogram)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 400,
});

// Raw continuous numerical data
const rawData = Array.from({ length: 200 }, () => ({
  value: Math.random() * 100,
}));

chart.options({
  type: 'interval',
  data: rawData,
  encode: { x: 'value' },
  transform: [
    {
      type: 'binX',
      y: 'count',      // Count the number of records in each bin, store the result in the y channel
      thresholds: 20,  // Divide into approximately 20 bins
    },
  ],
  style: { inset: 0.5 },    // Leave a small gap between bars
});

chart.render();
```

## Configuration Options

```javascript
transform: [
  {
    type: 'binX',
    // Statistical target
    y: 'count',       // 'count' (default, count) | 'sum' | 'mean' | 'max' | 'min'
    // If using sum/mean, also specify the aggregated field:
    // y: 'sum', field: 'amount',

    // Binning control (choose one)
    thresholds: 20,           // Target number of bins (approximate, adjusted automatically by the library)
    // domain: [0, 100],      // Specify value domain range
    // step: 5,               // Width of each bin (mutually exclusive with thresholds)
  },
],
```

## Grouped Histogram (Colored by Category)

```javascript
chart.options({
  type: 'interval',
  data,  // [{ value: 42, group: 'A' }, ...]
  encode: { x: 'value', color: 'group' },
  transform: [
    { type: 'binX', y: 'count', thresholds: 15 },
    { type: 'stackY' },   // Stack counts of different groups within the same bin
  ],
});
```

## Common Errors and Fixes

### Error: Using binX for Discrete Categorical Data
```javascript
// ❌ Error: genre is a categorical field and does not require binX
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre' },
  transform: [{ type: 'binX', y: 'count' }],  // Unnecessary!
});

// ✅ Correct: Use interval directly for categorical data, no binX needed
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'count' },
});
```

### Error: Forgot to Specify y Metric
```javascript
// ❌ Error: No y parameter, don't know what to calculate
chart.options({ transform: [{ type: 'binX', thresholds: 20 }] });

// ✅ Correct: Must specify y
chart.options({ transform: [{ type: 'binX', y: 'count', thresholds: 20 }] });
```