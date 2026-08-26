---
id: "g2-transform-bin"
title: "G2 Bin / BinX Numerical Binning Transformation (Histogram)"
description: |
  binX divides the continuous numerical x channel into several intervals (bins), counts the data volume in each interval,
  and is the core transformation for histograms. bin simultaneously bins both the x and y directions, generating a two-dimensional frequency matrix.
  The number of bins is controlled by thresholds, and the y channel specifies the aggregation method (count/sum, etc.).

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "bin"
  - "binX"
  - "binning"
  - "histogram"
  - "frequency distribution"
  - "transform"

related:
  - "g2-transform-groupx"
  - "g2-mark-interval-basic"
  - "g2-mark-cell-heatmap"

use_cases:
  - "Creating histograms (numerical distribution frequency)"
  - "Two-dimensional frequency heatmaps (bin simultaneously bins x/y)"
  - "Converting continuous numerical values into discrete grouped statistics"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/bin"
---

## Minimum Viable Example (Histogram)

```javascript
import { Chart } from '@antv/g2';

// Continuous numerical data, no need to pre-calculate frequency
const rawData = Array.from({ length: 1000 }, () => ({
  age: Math.floor(Math.random() * 50 + 20),  // Random age between 20~70
}));

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data: rawData,
  encode: {
    x: 'age',   // Continuous value → automatic binning
    y: '★',     // Placeholder, binX will calculate count
  },
  transform: [
    {
      type: 'binX',
      y: 'count',        // Aggregation method: count per bin
      thresholds: 15,    // Number of bins (approximate), default is auto-calculated
    },
  ],
  style: { inset: 1 },  // 1px gap between bars
  axis: { y: { title: 'Number of People' } },
});

chart.render();
```

## BinX Configuration Options

```javascript
transform: [
  {
    type: 'binX',
    thresholds: 20,  // Number of bins (integer) or an array of thresholds (e.g., [0, 25, 50, 75, 100])
    y: 'count',      // Aggregation: 'count' | 'sum' | 'mean' | 'min' | 'max' | function
    // groupBy: 'color',  // Group bins by color (used for grouped histograms)
  },
]
```

## 2D Frequency Heatmap (bin)

```javascript
// bin divides both x and y directions into buckets, generating a 2D frequency matrix
chart.options({
  type: 'cell',
  data: scatterData,
  encode: {
    x: 'x',
    y: 'y',
    color: '★',
  },
  transform: [
    {
      type: 'bin',
      color: 'count',    // Counts the number of points in each cell (mapped to color)
      thresholds: [20, 20],  // [Number of buckets in x direction, Number of buckets in y direction]
    },
  ],
  scale: { color: { type: 'sequential', palette: 'ylOrRd' } },
  style: { lineWidth: 0 },
});
```

## Grouped Histogram (Bucketed by Color)

```javascript
chart.options({
  type: 'interval',
  data: employeeData,
  encode: { x: 'salary', y: '★', color: 'dept' },
  transform: [
    { type: 'binX', y: 'count', thresholds: 12 },
    { type: 'stackY' },   // Stacked
  ],
});
```

## Common Errors and Fixes

### Error 1: Using binX for Categorical Field x——Categorical Application groupX
```javascript
// ❌ Error: x is a string category, binX cannot bucket strings
chart.options({
  encode: { x: 'department', y: '★' },   // department is a string
  transform: [{ type: 'binX', y: 'count' }],  // ❌
});

// ✅ Use groupX for string categories
chart.options({
  encode: { x: 'department', y: '★' },
  transform: [{ type: 'groupX', y: 'count' }],  // ✅
});

// ✅ binX used for continuous numerical values
chart.options({
  encode: { x: 'age', y: '★' },   // age is a number
  transform: [{ type: 'binX', y: 'count' }],  // ✅
});
```

### Error 2: Excessive Thresholds—Too Many Tiny Bins
```javascript
// ❌ 1000 data points with 500 bins, 2 points per bin, histogram lacks statistical significance
transform: [{ type: 'binX', y: 'count', thresholds: 500 }]  // ❌

// ✅ Histogram bin count typically ranges from 10 to 50
transform: [{ type: 'binX', y: 'count', thresholds: 20 }]  // ✅
```