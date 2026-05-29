---
id: "g2-transform-groupy"
title: "G2 GroupY Transform"
description: |
  Group and aggregate data by the Y channel. Symmetrical to GroupX,
  it is used for scenarios where data is aggregated by the Y dimension.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "grouping"
  - "aggregation"
  - "Y-axis"
  - "statistics"

related:
  - "g2-transform-groupx"
  - "g2-transform-groupcolor"
  - "g2-transform-group"

use_cases:
  - "Statistics by Y dimension"
  - "Horizontal bar chart aggregation"
  - "Group aggregation under transposed coordinate systems"

anti_patterns:
  - "Poor grouping effect when Y channel is a continuous value"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

The GroupY Transform groups data by the values of the `y` channel, while considering the `color` and `series` channels, and then performs aggregation calculations on each group.

**Grouping Dimensions:**
- Primary Dimension: `y` channel
- Additional Dimensions: `color`, `series`

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
  coordinate: { transform: [{ type: 'transpose' }] },  // Transpose to horizontal bar chart
  data: [
    { category: 'A', group: 'X', value: 10 },
    { category: 'A', group: 'Y', value: 20 },
    { category: 'B', group: 'X', value: 15 },
    { category: 'B', group: 'Y', value: 25 },
  ],
  encode: {
    x: 'value',
    y: 'category',
    color: 'group',
  },
  transform: [
    {
      type: 'groupY',
      x: 'sum',  // Sum each group
    },
  ],
});

chart.render();
```

## Common Variants

### Calculate Average

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: { x: 'value', y: 'category', color: 'group' },
  transform: [
    { type: 'groupY', x: 'mean' },
  ],
});
```

### Count Statistics

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    { type: 'groupY', x: 'count' },
  ],
});
```

### Multi-Channel Aggregation

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: { x: 'value', y: 'category', size: 'count' },
  transform: [
    {
      type: 'groupY',
      x: 'sum',
      size: 'count',
    },
  ],
});
```

## Complete Type Reference

```typescript
interface GroupYTransform {
  type: 'groupY';
  x?: Reducer;
  // Other channels can also be aggregated
  [channel: string]: Reducer;
}

type Reducer = 'sum' | 'mean' | 'median' | 'max' | 'min' | 'count' | 'first' | 'last' | ((I: number[], V: any[]) => any);
```

## Comparison with GroupX

| Feature | GroupX | GroupY |
|---------|--------|--------|
| Grouping Dimensions | x, color, series | y, color, series |
| Common Use Cases | Vertical Bar Chart | Horizontal Bar Chart |
| Aggregation Channel | Typically y | Typically x |

## Common Errors and Fixes

### Error 1: Using in Non-Transposed Coordinate Systems

```javascript
// ⚠️ Note: In a regular coordinate system, GroupY is typically used when Y is a categorical axis
// If Y is a numerical axis, grouping may not make sense

// ✅ Correct: Transposed Coordinate System + GroupY
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: { x: 'value', y: 'category' },
  transform: [{ type: 'groupY', x: 'sum' }],
});
```