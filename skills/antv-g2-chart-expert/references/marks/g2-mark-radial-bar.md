---
id: "g2-mark-radial-bar"
title: "G2 Radial Bar Chart Mark"
description: |
  Radial Bar Chart Mark. Uses the interval mark with a radial coordinate system to display categorical data comparisons in a circular manner.
  Suitable for data visualization scenarios with high aesthetic requirements.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Radial Bar Chart"
  - "Radial Bar"
  - "Circular Bar Chart"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-rose"

use_cases:
  - "Categorical data comparison"
  - "Aesthetic display"
  - "Large screen visualization"

anti_patterns:
  - "Precise numerical comparisons should use bar charts"
  - "Data must be sorted"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/radial-bar"
---

## Core Concepts

The Jade Ring Chart (Radial Bar Chart) is a transformation of the bar chart in a polar coordinate system:
- Uses the `interval` mark
- Combined with the `radial` coordinate system
- Represents numerical values with arc length

**Notes:**
- There is a radius feedback effect, making the outer circle appear larger
- Data must be sorted
- More suitable for aesthetic display rather than precise comparison

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'interval',
  data: [
    { question: 'Cross-Strait Relations', percent: 0.21 },
    { question: 'Military Power', percent: 0.47 },
    { question: 'Environmental Impact', percent: 0.49 },
  ],
  coordinate: { type: 'radial', innerRadius: 0.2 },
  encode: {
    x: 'question',
    y: 'percent',
    color: 'question',
  },
  style: {
    radiusTopLeft: 4,
    radiusTopRight: 4,
  },
});

chart.render();
```

## Common Variants

### Specify Angle Range

```javascript
chart.options({
  type: 'interval',
  coordinate: {
    type: 'radial',
    innerRadius: 0.3,
    startAngle: -Math.PI,
    endAngle: -0.25 * Math.PI,
  },
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
});
```

### With Labels

```javascript
chart.options({
  type: 'interval',
  coordinate: { type: 'radial', innerRadius: 0.2 },
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  labels: [
    {
      text: 'value',
      position: 'inside',
      style: { fontWeight: 'bold', fill: 'white' },
    },
  ],
});
```

### Interaction Integration

```javascript
chart.options({
  type: 'interval',
  coordinate: { type: 'radial', innerRadius: 0.2 },
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  interaction: [
    { type: 'elementHighlight', background: true },
  ],
});
```

## Complete Type Reference

```typescript
interface RadialBarOptions {
  type: 'interval';
  coordinate: {
    type: 'radial';
    innerRadius?: number;    // Inner radius
    startAngle?: number;     // Start angle
    endAngle?: number;       // End angle
  };
  encode: {
    x: string;    // Category field (mapped to angle)
    y: string;    // Numerical field (mapped to radius)
    color?: string;
  };
}
```

## Radial Bar Chart vs. Column Chart

| Feature | Radial Bar Chart | Column Chart |
|---------|---------------|---------------|
| Coordinate System | Polar | Cartesian |
| Visual Effect | More Aesthetic | More Precise |
| Data Comparison | Radial Effect | Accurate Comparison |

## Common Errors and Fixes

### Error 1: Unsorted Data

```javascript
// ❌ Issue: Unsorted data can lead to visual misinterpretation
data: [{ category: 'A', value: 100 }, { category: 'B', value: 50 }]

// ✅ Correct: Data sorted by value
data: [{ category: 'B', value: 50 }, { category: 'A', value: 100 }]
```

### Error 2: Using `polar` Coordinate System

```javascript
// ❌ Issue: `polar` is the coordinate system for rose charts
coordinate: { type: 'polar' }

// ✅ Correct: Use `radial` coordinate system
coordinate: { type: 'radial' }
```

### Error 3: Excessive Categories

```javascript
// ⚠️ Note: It is recommended to have no more than 15 categories
// Excessive categories can result in an overly narrow ring
```

### Error 4: Incorrect Encoding Channel Mapping

```javascript
// ❌ Issue: x maps to a numerical field, y maps to a categorical field, which is incorrect in a radial coordinate system
encode: {
  x: 'value',       // x should map to a categorical field
  y: 'category',    // y should map to a numerical field
}

// ✅ Correct: x maps to a categorical field, y maps to a numerical field
encode: {
  x: 'category',    // x maps to a categorical field (corresponds to angle)
  y: 'value',       // y maps to a numerical field (corresponds to radius)
}
```

### Error 5: Incorrect Sorting Method in transform

```javascript
// ❌ Issue: Used transform sorting but with incorrect direction
transform: [
  {
    type: 'sortX',
    by: 'value',
    reverse: false,   // Should be true to achieve increment from inside to outside
  },
],

// ✅ Correct: Use the correct sorting direction
transform: [
  {
    type: 'sortX',
    by: 'value',
    reverse: true,   // Increment from inside to outside
  },
],
// Or a more recommended approach is to pre-sort at the data level
data: rawData.sort((a, b) => b.value - a.value)
```