---
id: "g2-transform-jittery"
title: "G2 JitterY Transform"
description: |
  Applies jittering to data in the Y direction to prevent point overlap.
  Commonly used in scatter plots to disperse categorized data points.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "jitter"
  - "scatter plot"
  - "overlap prevention"
  - "Y-axis"

related:
  - "g2-transform-jitter"
  - "g2-transform-jitterx"
  - "g2-mark-point-scatter"

use_cases:
  - "Preventing point overlap in categorized scatter plots"
  - "Displaying the distribution of categorized data in the horizontal direction"
  - "Jittering in transposed coordinate systems"

anti_patterns:
  - "Continuous numerical data does not require jittering"
  - "Jittering is less effective with a small number of points"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

The JitterY Transform applies random offsets to data points in the Y direction, dispersing overlapping points for better visibility. Symmetrical to JitterX, it is suitable for cases where the Y-axis represents categorical data.

**How It Works:**
1. Determine the range for each category based on the Y-axis scale
2. Randomly offset the Y position of each point within the range
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
    { value: 10, category: 'A' },
    { value: 12, category: 'A' },
    { value: 11, category: 'A' },
    { value: 20, category: 'B' },
    { value: 22, category: 'B' },
  ],
  encode: {
    x: 'value',
    y: 'category',
  },
  transform: [
    { type: 'jitterY' },
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
  encode: { x: 'value', y: 'category' },
  transform: [
    {
      type: 'jitterY',
      padding: 0.2,  // Jitter range ratio
    },
  ],
});
```

### Using with JitterX

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'categoryX', y: 'categoryY' },
  transform: [
    { type: 'jitterX' },
    { type: 'jitterY' },
  ],
});
```

### Custom Random Function

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    {
      type: 'jitterY',
      random: () => Math.random(),
    },
  ],
});
```

## Complete Type Reference

```typescript
interface JitterYTransform {
  type: 'jitterY';
  padding?: number;      // Padding for the jitter range, default is 0
  random?: () => number; // Random number generation function, default is Math.random
}
```

## Comparison with Jitter/JitterX

| Transform | Jitter Direction | Common Use Cases |
|-----------|------------------|------------------|
| jitter    | X and Y          | 2D categorical data |
| jitterX   | X only           | X-axis categorical data |
| jitterY   | Y only           | Y-axis categorical data |

## Common Errors and Fixes

### Error 1: Using Jitter on Continuous Data

```javascript
// ❌ Not Recommended: Jitter on the Y-axis with continuous values may cause misinterpretation
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'continuousValue' },
  transform: [{ type: 'jitterY' }],
});

// ✅ Correct: Use jitter when the Y-axis represents categorical data
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [{ type: 'jitterY' }],
});
```

### Error 2: Excessive padding value

```javascript
// ❌ Incorrect: Excessive padding causes points to overflow into adjacent categories
transform: [{ type: 'jitterY', padding: 0.8 }]

// ✅ Correct: Appropriate padding value
transform: [{ type: 'jitterY', padding: 0.2 }]
```