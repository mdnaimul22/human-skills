---
id: "g2-transform-jitterx"
title: "G2 JitterX Transform"
description: |
  Applies jittering to data in the X direction to prevent point overlap.
  Commonly used in scatter plots to disperse categorical data points.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "jitter"
  - "scatter plot"
  - "overlap prevention"
  - "X-axis"

related:
  - "g2-transform-jitter"
  - "g2-transform-jittery"
  - "g2-mark-point-scatter"

use_cases:
  - "Preventing point overlap in categorical scatter plots"
  - "Visualizing the distribution density of categorical data"
  - "One-dimensional data distribution visualization"

anti_patterns:
  - "Jittering is unnecessary for continuous numerical data"
  - "Jittering effect is insignificant with too few points"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

The JitterX Transform applies a random offset to data points along the X-axis, dispersing overlapping points for better visibility. This is particularly useful for scatter plots with categorical data.

**How it works:**
1. Determine the range for each category based on the X-axis scale
2. Randomly offset the X position of each point within the range
3. Control the offset range using `padding`

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
    { category: 'A', value: 12 },
    { category: 'A', value: 11 },
    { category: 'B', value: 20 },
    { category: 'B', value: 22 },
  ],
  encode: {
    x: 'category',
    y: 'value',
  },
  transform: [
    { type: 'jitterX' },
  ],
});

chart.render();
```

## Common Variants

### Control Jitter Range

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'jitterX',
      padding: 0.2,  // Jitter range ratio, default 0
    },
  ],
});
```

### Custom Random Function

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'jitterX',
      random: () => Math.random(),  // Default Math.random
    },
  ],
});
```

### Using with JitterY

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'category2' },
  transform: [
    { type: 'jitterX' },
    { type: 'jitterY' },
  ],
});
```

## Complete Type Reference

```typescript
interface JitterXTransform {
  type: 'jitterX';
  padding?: number;      // Padding for the jitter range, default 0
  random?: () => number; // Random number generation function, default Math.random
}
```

## Comparison with Jitter/JitterY

| Transform | Jitter Direction | Common Use Cases |
|-----------|------------------|------------------|
| jitter    | X and Y          | 2D categorical data |
| jitterX   | X only           | X-axis categorical data |
| jitterY   | Y only           | Y-axis categorical data |

## Common Errors and Fixes

### Error 1: Using Jitter for Continuous Data

```javascript
// ❌ Not Recommended: Jitter on continuous X-axis may cause misinterpretation
chart.options({
  type: 'point',
  data,
  encode: { x: 'continuousValue', y: 'value' },
  transform: [{ type: 'jitterX' }],
});

// ✅ Correct: Use jitter when X-axis is categorical
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [{ type: 'jitterX' }],
});
```

### Error 2: Excessive padding value

```javascript
// ❌ Incorrect: Excessive padding causes points to overflow into adjacent categories
transform: [{ type: 'jitterX', padding: 0.8 }]

// ✅ Correct: Appropriate padding value
transform: [{ type: 'jitterX', padding: 0.2 }]
```