---
id: "g2-scale-point"
title: "G2 Point Scale"
description: |
  Point scale, maps discrete categories to uniformly distributed points.
  Similar to Band Scale, but with a fixed bandwidth of 0, commonly used for position mapping in scatter plots.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "scale"
  - "point"
  - "discrete"
  - "position"

related:
  - "g2-scale-band"
  - "g2-scale-ordinal"
  - "g2-mark-point-scatter"

use_cases:
  - "X/Y axis position mapping in scatter plots"
  - "Position mapping for categorical data"
  - "Uniformly distributed discrete data"

anti_patterns:
  - "Continuous numerical data should use Linear Scale"
  - "Scenarios requiring bandwidth should use Band Scale"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale"
---

## Core Concepts

Point Scale is a discrete scale:
- Maps categories to uniformly distributed point positions
- Bandwidth is fixed at 0
- Each category corresponds to an exact position point

**Difference from Band Scale:**
- Band Scale: Each category occupies a range (with bandwidth)
- Point Scale: Each category corresponds to an exact point (without bandwidth)

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'point',
  data: [
    { category: 'A', value: 10 },
    { category: 'B', value: 20 },
    { category: 'C', value: 15 },
  ],
  encode: {
    x: 'category',
    y: 'value',
  },
  scale: {
    x: { type: 'point' },
  },
});

chart.render();
```

## Common Variants

### Set Inner Padding

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  scale: {
    x: {
      type: 'point',
      padding: 0.5,  // Inner padding at both ends, range [0, 1]
    },
  },
});
```

### Set Alignment

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  scale: {
    x: {
      type: 'point',
      align: 0.5,  // 0: Left align, 0.5: Center, 1: Right align
    },
  },
});
```

### Specify domain

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  scale: {
    x: {
      type: 'point',
      domain: ['A', 'B', 'C', 'D'],  // Explicitly specify category order
    },
  },
});
```

### Specify range

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  scale: {
    x: {
      type: 'point',
      range: [0.1, 0.9],  // Mapping range, default is [0, 1]
    },
  },
});
```

## Complete Type Reference

```typescript
interface PointScaleOption {
  type: 'point';
  domain?: string[] | number[];  // Category domain
  range?: [number, number];      // Output range, default [0, 1]
  padding?: number;              // Padding, default 0
  align?: number;                // Alignment, default 0.5
  round?: boolean;               // Whether to round, default false
}
```

## Comparison with Band Scale

| Feature | Point Scale | Band Scale |
|------|-------------|------------|
| Bandwidth | 0 | Has bandwidth |
| Output | Precise point position | Interval start point |
| Application | Scatter plot, dot plot | Bar chart, column chart |
| Padding | Single value | paddingInner + paddingOuter |

## Auto Inference

G2 automatically infers the scale based on the mark type:
- Categorical axis of `interval` mark → Band Scale
- Categorical axis of `point` mark → Point Scale
- Categorical axis of `line` mark → Band Scale

```javascript
// Automatically inferred as Point Scale
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  // scale: { x: { type: 'point' } }  // Can be omitted
});
```

## Common Errors and Fixes

### Error 1: Using `point` scale for marks requiring bandwidth (bar charts, heatmaps)

The `point` scale has a bandwidth of 0. Marks like `interval` (bar charts) and `cell` (heatmaps) rely on bandwidth to render shapes with area. Using the `point` scale for these marks results in bars/cells with a width of 0, making the shapes invisible.

```javascript
// ❌ Error: Bar chart using point scale, bar width is 0
chart.options({
  type: 'interval',
  encode: { x: 'category', y: 'value' },
  scale: { x: { type: 'point' } },  // ❌ bandwidth=0, bars disappear
});

// ❌ Error: Heatmap using point scale, cell width is 0 (common misuse: "ensure uniform distribution")
chart.options({
  type: 'cell',
  encode: { x: 'date', y: 'month', color: 'value' },
  scale: {
    x: { type: 'point' },  // ❌ cell requires bandwidth
    y: { type: 'point' },  // ❌
  },
});

// ✅ Correct: Use band scale (or omit, G2 infers automatically) for interval and cell marks
chart.options({
  type: 'cell',
  encode: { x: 'date', y: 'month', color: 'value' },
  scale: {
    x: { type: 'band' },   // ✅ has bandwidth, cells visible
    y: { type: 'band' },   // ✅
  },
  // or simply omit scale, cell mark defaults to band
});
```

**Marks suitable for `point` scale**: `point` (scatter plots), `line` (line charts with categorical x-axis).

### Error 2: Excessive padding Value

```javascript
// ❌ Incorrect: padding exceeds the valid range
scale: { x: { type: 'point', padding: 1.5 } }

// ✅ Correct: padding within the [0, 1] range
scale: { x: { type: 'point', padding: 0.5 } }
```

### Error 3: Incorrect `align` Value

```javascript
// ❌ Incorrect: `align` exceeds the valid range
scale: { x: { type: 'point', align: 2 } }

// ✅ Correct: `align` within the range [0, 1]
scale: { x: { type: 'point', align: 0.5 } }
```