---
id: "g2-mark-mosaic"
title: "G2 Mosaic Plot (mosaic)"
description: |
  Mosaic Plot (Mosaic Plot / Marimekko Chart) has three forms:
  1. Uniform Mosaic Plot: type: 'cell', uses color and size to display the distribution of two-dimensional categorical data;
  2. Non-uniform Mosaic Plot: type: 'interval' + flexX/stackY/normalizeY transform,
     rectangle width represents category scale, height represents internal distribution ratio;
  3. Density Mosaic Plot: type: 'rect' + bin transform, displays the distribution density of two-dimensional continuous data.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "mosaic plot"
  - "mosaic"
  - "marimekko"
  - "cell"
  - "flexX"
  - "bin"
  - "heatmap"

related:
  - "g2-mark-cell-heatmap"
  - "g2-mark-interval-stacked"

use_cases:
  - "Two-dimensional categorical data distribution (Uniform Mosaic Plot)"
  - "Market segmentation analysis (Non-uniform Mosaic Plot)"
  - "Two-dimensional continuous data density analysis (Density Mosaic Plot)"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/mosaic"
---

## Core Concepts

There are three implementation methods for mosaic plots:

| Type | Mark | Characteristics |
|------|------|------|
| Uniform Mosaic Plot | `cell` | Axes are uniformly distributed, using color/size to encode the third dimension |
| Non-Uniform Mosaic Plot | `interval` + flexX | X-axis width is allocated according to data proportions |
| Density Mosaic Plot | `rect` + bin | Displays density after binning continuous data |

## Uniform Mosaic Plot (Cell)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
  height: 400,
});

chart.options({
  type: 'cell',
  data: [
    { product: 'Phone', region: 'North China', sales: 120, category: 'High-end' },
    { product: 'Phone', region: 'East China', sales: 180, category: 'High-end' },
    { product: 'Phone', region: 'South China', sales: 150, category: 'High-end' },
    { product: 'Computer', region: 'North China', sales: 80, category: 'Mid-range' },
    { product: 'Computer', region: 'East China', sales: 110, category: 'Mid-range' },
    { product: 'Computer', region: 'South China', sales: 95, category: 'Mid-range' },
    { product: 'Tablet', region: 'North China', sales: 60, category: 'Mid-range' },
    { product: 'Tablet', region: 'East China', sales: 85, category: 'Mid-range' },
    { product: 'Tablet', region: 'South China', sales: 70, category: 'Low-end' },
    { product: 'Headphones', region: 'North China', sales: 40, category: 'Low-end' },
    { product: 'Headphones', region: 'East China', sales: 55, category: 'Low-end' },
    { product: 'Headphones', region: 'South China', sales: 45, category: 'Low-end' },
  ],
  encode: {
    x: 'product',
    y: 'region',
    color: 'category',
    size: 'sales',      // Encode numerical values using cell size
  },
  scale: {
    color: { palette: 'category10', type: 'ordinal' },
    size: { type: 'linear', range: [0.3, 1] },
  },
  style: {
    stroke: '#fff',
    lineWidth: 2,
    inset: 2,
  },
});

chart.render();
```

## Non-Uniform Marimekko Chart

The width of the rectangles is allocated according to the proportion of the total amount of the X-axis field, displaying market share-like data:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 900,
  height: 600,
  paddingLeft: 0,
  paddingRight: 0,
});

chart.options({
  type: 'interval',
  data: {
    type: 'fetch',
    value: 'https://gw.alipayobjects.com/os/bmw-prod/3041da62-1bf4-4849-aac3-01a387544bf4.csv',
  },
  transform: [
    { type: 'flexX', reducer: 'sum' },  // X-axis width allocated by sum proportion
    { type: 'stackY' },                  // Y-axis stacking
    { type: 'normalizeY' },              // Y-axis normalization to 0-1
  ],
  encode: {
    x: 'market',
    y: 'value',
    color: 'segment',
  },
  axis: {
    y: false,
  },
  scale: {
    x: { paddingOuter: 0, paddingInner: 0.01 },
  },
  tooltip: 'value',
  labels: [
    {
      text: 'segment',
      x: 5,
      y: 5,
      textAlign: 'start',
      textBaseline: 'top',
      fontSize: 10,
      fill: '#fff',
    },
  ],
});

chart.render();
```

## Density Mosaic Plot (Bin Transform)

Suitable for displaying the distribution density relationship between two continuous fields:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'rect',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/movies.json',
  },
  encode: {
    x: 'IMDB Rating',
    y: 'Rotten Tomatoes Rating',
  },
  transform: [
    { type: 'bin', color: 'count', thresholdsX: 30, thresholdsY: 20 },
  ],
  scale: {
    color: { palette: 'ylGnBu' },
  },
});

chart.render();
```

## Common Errors and Fixes

### Error 1: Non-Uniform Mosaic Chart Missing flexX Transform

```javascript
// ❌ Error: Without flexX, X-axis widths are equal, not a true mosaic chart
chart.options({
  type: 'interval',
  data,
  transform: [
    { type: 'stackY' },
    { type: 'normalizeY' },
    // ❌ Missing flexX
  ],
  encode: { x: 'market', y: 'value', color: 'segment' },
});

// ✅ Correct: Three transforms must be used together
chart.options({
  type: 'interval',
  data,
  transform: [
    { type: 'flexX', reducer: 'sum' },  // ✅ X-axis widths proportional
    { type: 'stackY' },
    { type: 'normalizeY' },
  ],
  encode: { x: 'market', y: 'value', color: 'segment' },
});
```

### Error 2: Uniform Mosaic Charts Use `interval` Instead of `cell`

```javascript
// ❌ Issue: `interval` is less intuitive than `cell` in uniform grid scenarios
chart.options({
  type: 'interval',   // ❌ Use `cell` for uniform grids
  data,
  encode: { x: 'product', y: 'region', color: 'category' },
});

// ✅ Correct: Use `cell` for uniform two-dimensional categorizations
chart.options({
  type: 'cell',  // ✅
  data,
  encode: { x: 'product', y: 'region', color: 'category' },
});
```

### Error 3: Using cell/interval instead of rect for density mosaic plots

```javascript
// ❌ Incorrect: Continuous data binning applied with rect + bin transform
chart.options({
  type: 'cell',   // ❌ cell is suitable for discrete data
  data,
  encode: { x: 'IMDB Rating', y: 'Rotten Tomatoes Rating' },
});

// ✅ Correct: Continuous data binning should use rect
chart.options({
  type: 'rect',  // ✅
  data,
  encode: { x: 'IMDB Rating', y: 'Rotten Tomatoes Rating' },
  transform: [{ type: 'bin', color: 'count' }],
});
```

## Comparison of Three Types of Mosaic Plots

| Type | Data Type | Mark | Core Transform |
|------|---------|------|---------------|
| Uniform Mosaic Plot | Two-dimensional Discrete | `cell` | None |
| Non-uniform Mosaic Plot | Multi-dimensional Categorical + Numerical | `interval` | `flexX + stackY + normalizeY` |
| Density Mosaic Plot | Two-dimensional Continuous | `rect` | `bin` |