---
id: "g2-transform-sample"
title: "G2 Sample Data Transformation"
description: |
  The sample transformation automatically downsamples data when it exceeds a threshold (default 2000 entries),
  preventing slow rendering or overly dense visualizations for large datasets.
  Supports multiple strategies including first, last, min, max, median, and lttb (Largest Triangle Three Buckets, preserves trends).

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "sample"
  - "sampling"
  - "big data"
  - "performance optimization"
  - "lttb"
  - "downsampling"
  - "transform"

related:
  - "g2-mark-line-basic"
  - "g2-transform-filter"

use_cases:
  - "Sampling line charts with over 2000 data points while preserving visual trends"
  - "Performance optimization for real-time data streams"
  - "Large time-series visualizations such as stock K-line charts"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/sample"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Simulate 5000 time series data points
const data = Array.from({ length: 5000 }, (_, i) => ({
  time: new Date(2020, 0, 1 + Math.floor(i / 10)).toISOString(),
  value: Math.sin(i / 50) * 100 + Math.random() * 20,
}));

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'time', y: 'value' },
  transform: [
    {
      type: 'sample',
      thresholds: 500,     // Trigger sampling only when exceeding 500 data points
      strategy: 'lttb',   // Largest Triangle Three Buckets sampling, best for preserving visual trends
    },
  ],
});

chart.render();
```

## Sampling Strategy Comparison

```javascript
// lttb (recommended): Largest Triangle Three Buckets algorithm, highest visual fidelity
transform: [{ type: 'sample', strategy: 'lttb', thresholds: 500 }]

// median: Takes the median of each bucket, smooth but may lose extreme values
transform: [{ type: 'sample', strategy: 'median', thresholds: 1000 }]

// min/max: Retains the minimum/maximum value of each bucket, suitable for preserving extreme values
transform: [{ type: 'sample', strategy: 'max', thresholds: 800 }]

// first/last: Takes the first/last item of each bucket, best performance but lowest accuracy
transform: [{ type: 'sample', strategy: 'first', thresholds: 2000 }]
```

## Multi-Series Group Sampling

```javascript
// groupBy specifies the grouping field, each series is sampled independently
chart.options({
  type: 'line',
  data: multiSeriesData,
  encode: { x: 'time', y: 'value', color: 'series' },
  transform: [
    {
      type: 'sample',
      thresholds: 300,
      strategy: 'lttb',
      groupBy: ['series', 'color'],  // Group by series, each group is downsampled independently
    },
  ],
});
```

## Configuration Options

```javascript
transform: [
  {
    type: 'sample',
    strategy: 'median',   // Sampling strategy: 'first'|'last'|'min'|'max'|'median'|'lttb'|function
                          // Default: 'median'
    thresholds: 2000,     // Data volume threshold to trigger sampling, default: 2000
    groupBy: ['series', 'color'],  // Grouping fields, default: ['series', 'color']
  },
]
```

## Common Errors and Fixes

### Error 1: Thresholds Set Too High—Large Data Does Not Trigger Sampling
```javascript
// ❌ 10,000 data points, thresholds is the default 2000, but the strategy is incorrect
transform: [{ type: 'sample' }]  // Default thresholds: 2000, strategy: 'median'
// ⚠️ Reducing 10,000 data points to only 2,000 might still be too many

// ✅ Explicitly set thresholds based on the rendering target
transform: [{ type: 'sample', thresholds: 300, strategy: 'lttb' }]
```

### Error 2: Using `sample` on Bar Charts—Disrupts Complete Categorization
```javascript
// ❌ Sampling in bar charts causes some categories to disappear, creating visual discontinuity
chart.options({
  type: 'interval',
  encode: { x: 'category', y: 'value' },
  transform: [{ type: 'sample' }],  // ❌ Sampling is typically unnecessary for bar charts
});

// ✅ `sample` is primarily used for line charts and other continuous data
chart.options({
  type: 'line',
  encode: { x: 'time', y: 'value' },
  transform: [{ type: 'sample', strategy: 'lttb' }],  // ✅
});
```