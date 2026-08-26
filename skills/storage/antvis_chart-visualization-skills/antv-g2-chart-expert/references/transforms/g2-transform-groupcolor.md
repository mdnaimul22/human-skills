---
id: "g2-transform-groupcolor"
title: "G2 GroupColor Transform"
description: |
  Group and aggregate data by the color channel. Commonly used in categorical aggregation scenarios,
  such as calculating sums, averages, etc., by category.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "grouping"
  - "aggregation"
  - "color"
  - "categorical statistics"

related:
  - "g2-transform-groupx"
  - "g2-transform-groupy"
  - "g2-transform-group"

use_cases:
  - "Calculate sums by category"
  - "Aggregate data by color dimension"
  - "Compute averages, maximum values by category"

anti_patterns:
  - "Should not be used when retaining original data is required"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

GroupColor Transform groups data by the value of the `color` channel and then performs aggregation calculations on each group.

**Supported Aggregation Functions:**
- `sum`：sum
- `mean`：mean
- `median`：median
- `max`：maximum
- `min`：minimum
- `count`：count
- `first`：first value
- `last`：last value

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
    { category: 'A', type: 'X', value: 10 },
    { category: 'A', type: 'Y', value: 20 },
    { category: 'B', type: 'X', value: 15 },
    { category: 'B', type: 'Y', value: 25 },
  ],
  encode: {
    x: 'category',
    y: 'value',
    color: 'type',  // Group by type
  },
  transform: [
    {
      type: 'groupColor',
      y: 'sum',  // Sum each group
    },
  ],
});

chart.render();
```

## Common Variants

### Calculate the Mean

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  transform: [
    { type: 'groupColor', y: 'mean' },
  ],
});
```

### Multi-Channel Aggregation

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type', size: 'count' },
  transform: [
    {
      type: 'groupColor',
      y: 'sum',
      size: 'count',  // Aggregate size channel simultaneously
    },
  ],
});
```

### Custom Aggregation Function

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  transform: [
    {
      type: 'groupColor',
      y: (I, V) => {
        // I: Array of indices within the group
        // V: Array of values for this channel
        return I.reduce((sum, i) => sum + V[i], 0) / I.length;
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface GroupColorTransform {
  type: 'groupColor';
  y?: 'sum' | 'mean' | 'median' | 'max' | 'min' | 'count' | 'first' | 'last' | ((I: number[], V: any[]) => any);
  // Other channels can also be aggregated
  [channel: string]: Reducer;
}

type Reducer = 'sum' | 'mean' | 'median' | 'max' | 'min' | 'count' | 'first' | 'last' | ((I: number[], V: any[]) => any);
```

## Common Errors and Fixes

### Error 1: Color Channel Not Specified

```javascript
// ❌ Error: No color channel, groupColor is invalid
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [{ type: 'groupColor', y: 'sum' }],
});

// ✅ Correct: Add color channel
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  transform: [{ type: 'groupColor', y: 'sum' }],
});
```

### Error 2: Incorrect Spelling of Aggregation Function Name

```javascript
// ❌ Incorrect
transform: [{ type: 'groupColor', y: 'average' }]

// ✅ Correct
transform: [{ type: 'groupColor', y: 'mean' }]
```