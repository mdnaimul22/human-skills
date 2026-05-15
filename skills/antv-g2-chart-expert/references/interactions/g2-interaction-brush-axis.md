---
id: "g2-interaction-brush-axis"
title: "G2 Axis Brush Highlight (brushAxisHighlight)"
description: |
  brushAxisHighlight allows for interval brushing on a single axis in parallel coordinates,
  highlighting the lines that meet the selection criteria on all axes. It is the most common multi-dimensional filtering interaction in parallel coordinate plots,
  enabling simultaneous setting of intervals on multiple axes to achieve multi-dimensional joint filtering.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brushAxisHighlight"
  - "axis brushing"
  - "parallel coordinates"
  - "multi-dimensional filtering"
  - "interaction"

related:
  - "g2-coord-parallel"
  - "g2-interaction-brush-filter"

use_cases:
  - "Multi-dimensional joint data filtering in parallel coordinate plots"
  - "Setting filtering intervals on multiple axes separately"
  - "Interactive exploration of high-dimensional data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/brush-axis-highlight"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { name: 'Product A', price: 120, sales: 300, rating: 4.5, stock: 80 },
  { name: 'Product B', price: 85,  sales: 450, rating: 3.8, stock: 120 },
  { name: 'Product C', price: 200, sales: 180, rating: 4.9, stock: 40 },
  { name: 'Product D', price: 60,  sales: 600, rating: 3.2, stock: 200 },
  { name: 'Product E', price: 150, sales: 220, rating: 4.2, stock: 65 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: {
    position: ['price', 'sales', 'rating', 'stock'],
    color: 'name',
  },
  coordinate: { type: 'parallel' },
  style: { lineWidth: 1.5, strokeOpacity: 0.7 },
  interaction: {
    brushAxisHighlight: true,   // Draggable filter ranges on each axis
  },
});

chart.render();
```

## Standard Combination with Parallel Coordinate System

```javascript
chart.options({
  type: 'line',
  data: carData,
  encode: {
    position: ['mpg', 'cylinders', 'displacement', 'horsepower', 'weight', 'acceleration'],
    color: 'origin',
  },
  coordinate: { type: 'parallel' },
  style: { lineWidth: 1, strokeOpacity: 0.5 },
  interaction: {
    brushAxisHighlight: {
      // Style of unselected lines
      unhighlightedOpacity: 0.1,
    },
  },
  legend: { color: { position: 'top' } },
});
```

## Common Errors and Fixes

### Error: Using brushAxisHighlight on a Non-Parallel Coordinate Chart
```javascript
// ❌ brushAxisHighlight is specifically designed for parallel coordinate charts
chart.options({
  type: 'line',
  encode: { x: 'date', y: 'value' },   // Regular line chart
  coordinate: { type: 'cartesian' },
  interaction: { brushAxisHighlight: true },  // ❌ Regular charts do not have "axes" to brush
});

// ✅ Use regular brushHighlight or brushFilter instead
chart.options({
  interaction: { brushHighlight: true },  // ✅ Regular rectangular brush
});

// ✅ Use brushAxisHighlight only with parallel coordinate charts
chart.options({
  coordinate: { type: 'parallel' },
  interaction: { brushAxisHighlight: true },  // ✅
});
```