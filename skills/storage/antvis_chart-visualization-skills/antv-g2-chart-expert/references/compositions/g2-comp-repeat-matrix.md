---
id: "g2-comp-repeat-matrix"
title: "G2 Repeat Matrix (repeatMatrix)"
description: |
  The G2 v5 repeatMatrix composition type arranges the same chart in a matrix according to two dimensional fields,
  with each cell sharing the same Mark configuration. The x-axis and y-axis correspond to a categorical field each,
  suitable for displaying pairwise relationships between multiple variables (scatter plot matrix).

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "repeat matrix"
  - "repeatMatrix"
  - "scatter plot matrix"
  - "multi-variable"
  - "facet"
  - "spec"

related:
  - "g2-comp-facet-rect"
  - "g2-mark-point-scatter"
  - "g2-core-view-composition"

use_cases:
  - "Pairwise scatter plot matrix for multiple variables"
  - "Exploring correlations in multi-dimensional data"
  - "Diagonal display of distribution histograms"

difficulty: "advanced"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/matrix"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 800,
  height: 800,
});

// Multi-dimensional data (each row is a sample with multiple numerical fields)
const data = [
  { sepalLength: 5.1, sepalWidth: 3.5, petalLength: 1.4, petalWidth: 0.2, species: 'setosa' },
  { sepalLength: 4.9, sepalWidth: 3.0, petalLength: 1.4, petalWidth: 0.2, species: 'setosa' },
  { sepalLength: 7.0, sepalWidth: 3.2, petalLength: 4.7, petalWidth: 1.4, species: 'versicolor' },
  { sepalLength: 6.4, sepalWidth: 3.2, petalLength: 4.5, petalWidth: 1.5, species: 'versicolor' },
  { sepalLength: 6.3, sepalWidth: 3.3, petalLength: 6.0, petalWidth: 2.5, species: 'virginica' },
  // ...more data
];

chart.options({
  type: 'repeatMatrix',
  data,
  encode: {
    x: ['sepalLength', 'sepalWidth', 'petalLength'],   // Column variables
    y: ['sepalLength', 'sepalWidth', 'petalLength'],   // Row variables
  },
  children: [
    {
      type: 'point',
      encode: { color: 'species' },
      style: { r: 3, fillOpacity: 0.7 },
    },
  ],
});

chart.render();
```

## Complete Scatter Plot Matrix (Including Diagonal)

```javascript
chart.options({
  type: 'repeatMatrix',
  data,
  encode: {
    x: ['sepalLength', 'sepalWidth', 'petalLength', 'petalWidth'],
    y: ['sepalLength', 'sepalWidth', 'petalLength', 'petalWidth'],
  },
  // Grid spacing
  padding: 10,
  children: [
    {
      type: 'point',
      encode: { color: 'species' },
      style: { r: 2.5, fillOpacity: 0.6 },
      legend: { color: { position: 'top' } },
    },
  ],
});
```

## Comparison with facetRect

```javascript
// repeatMatrix: Both x/y encode are variable arrays, automatically arranged into an n×n matrix
chart.options({
  type: 'repeatMatrix',
  encode: {
    x: ['var1', 'var2', 'var3'],
    y: ['var1', 'var2', 'var3'],
  },
  children: [{ type: 'point', encode: { color: 'category' } }],
});

// facetRect: Facet by different values of a single categorical field (one panel per value, arranged in a row or column)
chart.options({
  type: 'facetRect',
  encode: { x: 'region' },   // Split into multiple columns by different values of region
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'sales' },
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: encode.x/y Written as a Single Field Instead of an Array

```javascript
// ❌ Incorrect: encode.x/y in repeatMatrix must be an array of field names
chart.options({
  type: 'repeatMatrix',
  encode: {
    x: 'sepalLength',   // ❌ Single field name
    y: 'sepalWidth',
  },
});

// ✅ Correct: Both x and y must be arrays
chart.options({
  type: 'repeatMatrix',
  encode: {
    x: ['sepalLength', 'sepalWidth', 'petalLength'],   // ✅ Array
    y: ['sepalLength', 'sepalWidth', 'petalLength'],
  },
});
```

### Error 2: Confusing Scatterplot Matrix with Regular Faceting

```javascript
// ❌ Incorrect: Attempting to create a scatterplot matrix using facetRect
chart.options({
  type: 'facetRect',
  encode: {
    x: ['sepalLength', 'sepalWidth'],   // ❌ encode.x in facetRect only accepts a single field
  },
});

// ✅ Correct: Use repeatMatrix for pairwise comparisons of multiple variables
chart.options({
  type: 'repeatMatrix',
  encode: {
    x: ['sepalLength', 'sepalWidth'],   // ✅
    y: ['sepalLength', 'sepalWidth'],
  },
  children: [{ type: 'point', encode: { color: 'species' } }],
});
```