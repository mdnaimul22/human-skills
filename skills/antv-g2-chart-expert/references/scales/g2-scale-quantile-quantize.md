---
id: "g2-scale-quantile-quantize"
title: "G2 Quantile Scale (quantile) and Quantize Scale (quantize)"
description: |
  quantile: Groups data by quantiles based on actual data distribution, with an equal number of data points in each group (equal-frequency grouping).
  quantize: Divides the numerical range into equal intervals, with equal width for each segment (equal-interval grouping).
  Both map continuous values to discrete outputs (e.g., colors) and are commonly used for map classification coloring.
  The difference from threshold is: threshold manually specifies breakpoints, while quantile/quantize automatically calculates them.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "quantile"
  - "quantize"
  - "quantile"
  - "equal-frequency"
  - "equal-interval"
  - "scale"
  - "classification coloring"

related:
  - "g2-scale-threshold"
  - "g2-scale-ordinal"
  - "g2-mark-cell-heatmap"

use_cases:
  - "Map classification coloring: Automatic grouping by data distribution (quantile)"
  - "Equal-interval classification coloring (quantize)"
  - "Color grading for heatmaps"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/quantile"
---
## Quantile vs Quantize vs Threshold Comparison

| Scale | Grouping Method | Suitable Scenarios |
|--------|---------|---------|
| `threshold` | Manually specify breakpoints | Fixed grading with business meaning (e.g., 60 points = passing) |
| `quantize` | Equal-distance segmentation of numerical range | Equal-distance grading for uniformly distributed data |
| `quantile` | Grouping by actual data quantiles | Equal-frequency grading for skewed data distribution (equal number of items per group) |

## Quantile Scale

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 300 });

chart.options({
  type: 'cell',
  data,
  encode: { x: 'week', y: 'day', color: 'count' },
  scale: {
    color: {
      type: 'quantile',
      // Automatically group data by quantiles, with equal number of records in each group
      range: ['#ebedf0', '#c6e48b', '#7bc96f', '#196127'],
      // No need to specify domain, it is automatically calculated from the data
    },
  },
  style: { lineWidth: 2, stroke: '#fff' },
});
```

## quantize scale

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'hour', y: 'day', color: 'value' },
  scale: {
    color: {
      type: 'quantize',
      domain: [0, 100],  // Explicitly specify the numerical range (will be divided into N equal segments)
      range: ['#fee0d2', '#fc9272', '#de2d26'],  // 3 colors = 3 segments
    },
  },
});
```

## Common Errors and Fixes

### Error: Poor visual effect when quantile data is extremely skewed——Use threshold to manually set
```javascript
// ⚠️  Highly skewed data (e.g., 95% of data concentrated at low values), quantile grouping is reasonable but visually
// most areas have similar colors, with only a few high-value areas having vivid colors, which is not intuitive
chart.options({ scale: { color: { type: 'quantile' } } });  // ⚠️  Poor effect with skewed data

// ✅ For skewed data, use a log scale with sequential, or manually set key nodes using threshold
chart.options({
  scale: {
    color: {
      type: 'threshold',
      domain: [10, 100, 1000],  // Set breakpoints by logarithmic scale
      range: ['#eee', '#fee', '#f66', '#c00'],
    },
  },
});
```

### Error: quantize without specifying domain—automatically inferred from data, may have boundary issues
```javascript
// ⚠️  When domain is not specified, quantize infers from data min/max,
// new data outside this range will exceed the color scale
chart.options({ scale: { color: { type: 'quantize' } } });  // ⚠️  Depends on data range

// ✅ Explicitly specify domain with business meaning
chart.options({
  scale: { color: { type: 'quantize', domain: [0, 100] } },  // ✅ Explicitly 0~100
});
```