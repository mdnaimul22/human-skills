---
id: "g2-transform-selectx"
title: "G2 SelectX Transform"
description: |
  Select a subset of data by the X channel. Used to filter specific data points for each X category,
  such as maximum, minimum, first, last, etc.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "select"
  - "filter"
  - "X-axis"
  - "extremes"

related:
  - "g2-transform-select"
  - "g2-transform-selecty"

use_cases:
  - "Display only the maximum value for each category"
  - "Filter the first/last data point for each X group"
  - "Highlight extreme points"

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

SelectX Transform groups data by the X channel and then selects specific data points from each group. The supported selectors are:
- `max`: The point with the maximum Y value
- `min`: The point with the minimum Y value
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
    { category: 'A', value: 10 },
    { category: 'A', value: 25 },
    { category: 'A', value: 15 },
    { category: 'B', value: 20 },
    { category: 'B', value: 35 },
    { category: 'B', value: 30 },
  ],
  encode: {
    x: 'category',
    y: 'value',
  },
  transform: [
    {
      type: 'selectX',
      selector: 'max',  // Only keep the maximum value point for each category
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
  encode: { x: 'category', y: 'value' },
  transform: [
    { type: 'selectX', selector: 'min' },
  ],
});
```

### Select First/Last

```javascript
// Select the first data point of each category
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    { type: 'selectX', selector: 'first' },
  ],
});

// Select the last data point of each category
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    { type: 'selectX', selector: 'last' },
  ],
});
```

### Custom Selector

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'selectX',
      selector: (I, Y) => {
        // I: Array of indices within the group
        // Y: Array of values in the Y channel
        // Return the selected index
        return I.reduce((maxIdx, i) => Y[i] > Y[maxIdx] ? i : maxIdx, I[0]);
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface SelectXTransform {
  type: 'selectX';
  selector: 'max' | 'min' | 'first' | 'last' | ((I: number[], Y: any[]) => number);
}
```

## Comparison with Select/SelectY

| Transform | Grouping Dimension | Common Use Cases |
|-----------|--------------------|------------------|
| select    | By specified channel | General selection |
| selectX   | By X channel        | X-axis categorical filtering |
| selectY   | By Y channel        | Y-axis categorical filtering |

## Common Errors and Fixes

### Error 1: Incorrect Spelling of `selector`

```javascript
// ❌ Incorrect
transform: [{ type: 'selectX', selector: 'maximum' }]

// ✅ Correct
transform: [{ type: 'selectX', selector: 'max' }]
```

### Error 2: Custom Selector Returns Incorrect Value

```javascript
// ❌ Incorrect: Returns a value instead of an index
selector: (I, Y) => Math.max(...I.map(i => Y[i]))

// ✅ Correct: Returns an index
selector: (I, Y) => I.reduce((maxIdx, i) => Y[i] > Y[maxIdx] ? i : maxIdx, I[0])
```