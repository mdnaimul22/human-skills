---
id: "g2-transform-selecty"
title: "G2 SelectY Transform"
description: |
  Select a subset of data by the Y channel. Used to filter specific data points for each Y category,
  such as maximum, minimum, first, last, etc.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "selection"
  - "filtering"
  - "Y-axis"
  - "extremes"

related:
  - "g2-transform-select"
  - "g2-transform-selectx"

use_cases:
  - "Filtering extremes in horizontal bar charts"
  - "Data selection under transposed coordinate systems"
  - "Filtering data points by Y category"

anti_patterns:
  - "Should not be used when all data needs to be retained"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

The SelectY Transform groups data by the Y channel and then selects specific data points from each group. Supported selectors include:
- `max`: The point with the maximum X value
- `min`: The point with the minimum X value
- `first`: The first data point
- `last`: The last data point
- Custom selection function

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
    { value: 25, category: 'A' },
    { value: 15, category: 'A' },
    { value: 20, category: 'B' },
    { value: 35, category: 'B' },
    { value: 30, category: 'B' },
  ],
  encode: {
    x: 'value',
    y: 'category',
  },
  transform: [
    {
      type: 'selectY',
      selector: 'max',  // Retain only the maximum value point for each Y category
    },
  ],
});

chart.render();
```

## Common Variants

### Select Minimum Value

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    { type: 'selectY', selector: 'min' },
  ],
});
```

### Select First/Last

```javascript
// Select the first data point for each Y category
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    { type: 'selectY', selector: 'first' },
  ],
});

// Select the last data point for each Y category
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    { type: 'selectY', selector: 'last' },
  ],
});
```

### Custom Selector

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'value', y: 'category' },
  transform: [
    {
      type: 'selectY',
      selector: (I, X) => {
        // I: Array of indices within the group
        // X: Array of values in the X channel
        // Return the selected index
        return I.reduce((maxIdx, i) => X[i] > X[maxIdx] ? i : maxIdx, I[0]);
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface SelectYTransform {
  type: 'selectY';
  selector: 'max' | 'min' | 'first' | 'last' | ((I: number[], X: any[]) => number);
}
```

## Comparison with Select/SelectX

| Transform | Grouping Dimension | Common Use Cases |
|-----------|--------------------|------------------|
| select    | By specified channel | General selection |
| selectX   | By X channel        | X-axis categorical filtering |
| selectY   | By Y channel        | Y-axis categorical filtering |

## Common Errors and Fixes

### Error 1: Incorrect Spelling of `selector`

```javascript
// ❌ Incorrect
transform: [{ type: 'selectY', selector: 'minimum' }]

// ✅ Correct
transform: [{ type: 'selectY', selector: 'min' }]
```

### Error 2: Custom Selector Returns Incorrect Value

```javascript
// ❌ Incorrect: Returns a value instead of an index
selector: (I, X) => Math.max(...I.map(i => X[i]))

// ✅ Correct: Returns an index
selector: (I, X) => I.reduce((maxIdx, i) => X[i] > X[maxIdx] ? i : maxIdx, I[0])
```