---
id: "g2-mark-histogram"
title: "G2 Histogram Mark"
description: |
  Histogram Mark. Uses the rect mark in conjunction with the binX transform to display the distribution of continuous numerical data.
  Suitable for statistical analysis, data distribution exploration, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "histogram"
  - "distribution"
  - "statistics"

related:
  - "g2-mark-boxplot"
  - "g2-transform-binx"

use_cases:
  - "Data distribution analysis"
  - "Statistical analysis"
  - "Frequency statistics"

anti_patterns:
  - "Bar charts should be used for categorical data comparison"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/histogram"
---

## Core Concepts

Histograms are used to display the distribution of continuous numerical data. Unlike bar charts:
- Histograms use the `rect` mark, supporting `x` and `x1` channels to represent intervals
- They must be used with the `binX` transform for automatic binning and statistics
- There are no gaps between bars, indicating continuous data

**Key Elements:**
- `rect` mark: Supports interval representation
- `binX` transform: Automatic binning and statistics
- `x1` channel: Represents the end position of the interval

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'rect',
  data: {
    type: 'fetch',
    value: 'https://gw.alipayobjects.com/os/antvdemo/assets/data/diamond.json',
  },
  encode: {
    x: 'carat',
    y: 'count',
  },
  transform: [
    { type: 'binX', y: 'count' },
  ],
  style: {
    fill: '#1890FF',
    fillOpacity: 0.9,
  },
});

chart.render();
```

## Common Variants

### Specify the Number of Bins

```javascript
chart.options({
  type: 'rect',
  data,
  encode: { x: 'value', y: 'count' },
  transform: [
    { type: 'binX', y: 'count', thresholds: 30 },  // Specify the number of bins
  ],
});
```

### Multi-Distribution Comparison

```javascript
chart.options({
  type: 'rect',
  data,
  encode: {
    x: 'price',
    y: 'count',
    color: 'group',
  },
  transform: [
    { type: 'binX', y: 'count', groupBy: ['group'] },
  ],
  style: { fillOpacity: 0.7 },
});
```

### With Axis Titles

```javascript
chart.options({
  type: 'rect',
  data,
  encode: { x: 'carat', y: 'count' },
  transform: [{ type: 'binX', y: 'count' }],
  axis: {
    x: { title: 'Diamond Weight (Carat)' },
    y: { title: 'Frequency' },
  },
});
```

## Complete Type Reference

```typescript
interface HistogramOptions {
  type: 'rect';
  encode: {
    x: string;           // Continuous numerical field
    y: 'count';          // Count statistic
    color?: string;      // Grouping field
  };
  transform: [
    {
      type: 'binX';
      y: 'count';
      thresholds?: number;  // Number of bins
      groupBy?: string[];   // Grouping field
    }
  ];
}
```

## Histogram vs Bar Chart

| Feature | Histogram | Bar Chart |
|---------|----------|----------|
| Data Type | Continuous Numerical | Categorical Data |
| Mark Type | `rect` | `interval` |
| Bar Spacing | No Spacing | With Spacing |
| X-Axis | Continuous Range | Discrete Categories |

## Common Errors and Fixes

### Error 1: Using the `interval` Mark

```javascript
// ❌ Issue: `interval` does not support range representation
type: 'interval'

// ✅ Correct: Use the `rect` mark
type: 'rect'
```

### Error 2: Missing binX Transformation

```javascript
// ❌ Problem: No binning statistics
encode: { x: 'value', y: 'count' }

// ✅ Correct: Add binX transformation
transform: [{ type: 'binX', y: 'count' }]
```

### Error 3: Insufficient Data Volume

```javascript
// ⚠️ Note: Histograms require a sufficient amount of data
// It is recommended to have at least 50 data points
```