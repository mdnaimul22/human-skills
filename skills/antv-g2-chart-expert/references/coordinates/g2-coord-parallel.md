---
id: "g2-coord-parallel"
title: "G2 Parallel Coordinates (parallel)"
description: |
  Parallel coordinates arrange multiple dimensions as parallel vertical axes, with each line representing a data record.
  It is used to discover patterns, clusters, and outliers in multidimensional data.
  It should be used in conjunction with the line mark, binding multiple fields using the position channel in encode.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "parallel"
  - "平行坐标"
  - "parallel coordinates"
  - "multidimensional"
  - "high-dimensional data"
  - "coordinate"

related:
  - "g2-mark-line-basic"
  - "g2-coord-transpose"

use_cases:
  - "Multidimensional data comparison analysis (e.g., multiple metrics of car performance)"
  - "Discovering clusters and associations in high-dimensional data"
  - "Outlier detection"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/parallel"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { name: 'Product A', price: 120, sales: 300, rating: 4.5, stock: 80 },
  { name: 'Product B', price: 85,  sales: 450, rating: 3.8, stock: 120 },
  { name: 'Product C', price: 200, sales: 180, rating: 4.9, stock: 40 },
  { name: 'Product D', price: 60,  sales: 600, rating: 3.2, stock: 200 },
];

const chart = new Chart({ container: 'container', width: 600, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: {
    position: ['price', 'sales', 'rating', 'stock'],  // Multi-dimensional field list
  },
  coordinate: { type: 'parallel' },  // Parallel coordinate system
  style: {
    lineWidth: 1.5,
    strokeOpacity: 0.7,
  },
  legend: { color: { position: 'right' } },
});

chart.render();
```

## Parallel Coordinates with Interactive Highlighting

```javascript
chart.options({
  type: 'line',
  data,
  encode: {
    position: ['cylinders', 'displacement', 'horsepower', 'weight', 'acceleration', 'miles_per_gallon'],
    color: 'origin',
  },
  coordinate: { type: 'parallel' },
  style: { lineWidth: 1, strokeOpacity: 0.5 },
  interaction: {
    elementHighlight: { background: true },  // Hover highlight
  },
  axis: {
    // Configure titles for each dimension individually
    position0: { title: 'Cylinders' },
    position1: { title: 'Displacement' },
    position2: { title: 'Horsepower' },
  },
});
```

## Common Errors and Fixes

### Error 1: Using x/y encode instead of position
```javascript
// ❌ Incorrect: Parallel coordinates do not use x/y, must use the position channel
chart.options({
  type: 'line',
  encode: {
    x: 'price',      // ❌
    y: 'sales',      // ❌ Only two dimensions, not parallel coordinates
  },
  coordinate: { type: 'parallel' },
});

// ✅ Correct: Position channel passes in a field array
chart.options({
  type: 'line',
  encode: {
    position: ['price', 'sales', 'rating'],  // ✅ Array form
  },
  coordinate: { type: 'parallel' },
});
```

### Error 2: Using interval or point mark in parallel coordinates
```javascript
// ❌ Incorrect: Parallel coordinates are only suitable for line mark
chart.options({
  type: 'interval',  // ❌ Meaningless in parallel coordinates
  coordinate: { type: 'parallel' },
});

// ✅ Correct: Use with line mark
chart.options({
  type: 'line',      // ✅
  coordinate: { type: 'parallel' },
});
```