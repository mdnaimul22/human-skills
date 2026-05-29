---
id: "g2-transform-pack"
title: "G2 Pack Transform"
description: |
  Pack layout Transform, which evenly arranges multiple graphic elements to avoid overlapping.
  Commonly used in scenarios such as Treemap and Bubble Chart that require automatic layout.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "pack"
  - "layout"
  - "anti-overlap"
  - "grid"

related:
  - "g2-mark-pack"
  - "g2-mark-treemap"

use_cases:
  - "Automatic arrangement of multiple graphic elements"
  - "Small multiple grid layout"
  - "Avoiding graphic overlap"

anti_patterns:
  - "Single graphic does not require packing"
  - "Data with explicit position information"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform"
---

## Core Concepts

Pack Transform arranges multiple graphic elements evenly through transformations (translate + scale) to avoid overlapping. It automatically calculates the position and scaling ratio for each element.

**How It Works:**
1. Calculate the bounding box for each element
2. Compute the grid layout based on container dimensions
3. Apply translate and scale transformations to each element

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'pack',
  data: {
    nodes: [
      { name: 'A', value: 100 },
      { name: 'B', value: 80 },
      { name: 'C', value: 60 },
    ],
  },
  encode: {
    value: 'value',
    color: 'value',
  },
});

chart.render();
```

## Common Variants

### Use as Transform

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'pack',
      padding: 5,        // Element spacing
      direction: 'col',  // Arrangement direction: 'col' | 'row'
    },
  ],
});
```

### Custom Spacing

```javascript
chart.options({
  type: 'pack',
  data,
  encode: { value: 'value', color: 'value' },
  transform: [
    {
      type: 'pack',
      padding: 10,  // Spacing between elements
    },
  ],
});
```

### Arrange by Row

```javascript
chart.options({
  type: 'pack',
  data,
  encode: { value: 'value', color: 'value' },
  transform: [
    {
      type: 'pack',
      direction: 'row',  // Arrange by row
    },
  ],
});
```

## Complete Type Reference

```typescript
interface PackTransform {
  type: 'pack';
  padding?: number;       // Spacing between elements, default 0
  direction?: 'col' | 'row';  // Arrangement direction, default 'col'
}
```

## Relationship with Pack Mark

Pack Mark internally uses Pack Transform for layout:
- **Pack Mark**: Used for creating circle packing charts (Circle Packing)
- **Pack Transform**: Used for grid arrangement of arbitrary graphical elements

## Common Errors and Fixes

### Error 1: Excessive Padding Value

```javascript
// ❌ Incorrect: Excessive padding causes elements to be overly compressed
transform: [{ type: 'pack', padding: 50 }]

// ✅ Correct: Appropriate padding value
transform: [{ type: 'pack', padding: 5 }]
```

### Error 2: Incorrect `direction` Parameter

```javascript
// ❌ Incorrect
transform: [{ type: 'pack', direction: 'horizontal' }]

// ✅ Correct
transform: [{ type: 'pack', direction: 'row' }]
```