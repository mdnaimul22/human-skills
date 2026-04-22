---
id: "g2-mark-rose"
title: "G2 Rose Chart Mark"
description: |
  Nightingale's Rose Chart Mark. Uses interval marks with a polar coordinate system, where the radius of the sector represents the numerical value.
  Suitable for scenarios such as categorical data comparison and periodic data display.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "rose chart"
  - "rose"
  - "nightingale chart"
  - "polar coordinates"

related:
  - "g2-mark-arc-pie"
  - "g2-coord-polar"

use_cases:
  - "Categorical data comparison"
  - "Periodic data display"
  - "Multi-dimensional comparison"

anti_patterns:
  - "Use pie charts for too few categories"
  - "Not suitable for significant numerical differences"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/rose"
---

## Core Concepts

The Nightingale Rose Chart is a bar chart plotted in a polar coordinate system:
- Uses the `interval` mark
- Combined with the `polar` coordinate system
- Sector radius represents the numerical value

**Difference from Pie Chart:**
- Pie Chart: Arc length represents the numerical value
- Rose Chart: Radius represents the numerical value

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'interval',
  autoFit: true,
  coordinate: { type: 'polar' },
  data: [
    { country: 'China', cost: 96 },
    { country: 'Germany', cost: 121 },
    { country: 'United States', cost: 100 },
    { country: 'Japan', cost: 111 },
  ],
  encode: {
    x: 'country',
    y: 'cost',
    color: 'country',
  },
  style: {
    stroke: 'white',
    lineWidth: 1,
  },
});

chart.render();
```

## Common Variants

### Stacked Rose Chart

```javascript
chart.options({
  type: 'interval',
  coordinate: { type: 'polar', innerRadius: 0.1 },
  data,
  encode: { x: 'year', y: 'count', color: 'type' },
  transform: [{ type: 'stackY' }],
});
```

### Sector Rose Chart

```javascript
chart.options({
  type: 'interval',
  coordinate: {
    type: 'polar',
    startAngle: Math.PI,
    endAngle: Math.PI * (3 / 2),
  },
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
});
```

### With Labels

```javascript
chart.options({
  type: 'interval',
  coordinate: { type: 'polar' },
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  labels: [
    {
      text: 'value',
      style: { textAlign: 'center', fontSize: 10 },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface RoseOptions {
  type: 'interval';
  coordinate: {
    type: 'polar';
    innerRadius?: number;    // Inner radius
    startAngle?: number;     // Start angle
    endAngle?: number;       // End angle
  };
  encode: {
    x: string;    // Category field
    y: string;    // Numerical field
    color?: string;
  };
  transform?: [{ type: 'stackY' }];  // Stack
}
```

## Rose Chart vs Pie Chart

| Feature | Rose Chart | Pie Chart |
|---------|-----------|-----------|
| Value Mapping | Radius | Arc |
| Number of Categories | More | Fewer |
| Comparison Method | Radius Comparison | Area Comparison |

## Common Errors and Fixes

### Error 1: Using theta coordinate system

```javascript
// ❌ Problem: theta is a pie chart coordinate system
coordinate: { type: 'theta' }

// ✅ Correct: Use polar coordinate system
coordinate: { type: 'polar' }
```

### Error 2: Data is not sorted

```javascript
// ⚠️ Note: It is recommended to sort the data before using the rose chart
// You can use the sortX transform
transform: [{ type: 'sortX', by: 'y' }]
```

### Error 3: Too Many Categories

```javascript
// ⚠️ Note: It is recommended to have no more than 30 categories
// Excessive categories can result in overly narrow sectors that are difficult to read
```