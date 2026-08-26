---
id: "g2-mark-point-scatter"
title: "G2 Scatter Plot (Point Mark)"
description: |
  Create a scatter plot using Point Mark to display the correlation between two numerical variables through x/y positions.
  This article uses the Spec mode (chart.options({})), supporting variants such as bubble charts (size channel), categorical coloring, and custom shapes.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "point"
tags:
  - "scatter plot"
  - "bubble chart"
  - "Point"
  - "scatter"
  - "bubble"
  - "correlation"
  - "distribution"
  - "spec"

related:
  - "g2-core-encode-channel"
  - "g2-scale-linear"
  - "g2-interaction-tooltip"

use_cases:
  - "Display the correlation between two continuous variables"
  - "Identify data distribution and outliers"
  - "Use bubble charts to display three-dimensional data (x/y/size)"

anti_patterns:
  - "Performance is poor when there are more than 10,000 data points; consider using a density plot"
  - "Scatter plots are less meaningful when both axes are categorical variables"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/point/scatter"
---

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
    { x: 10, y: 30, category: 'A' },
    { x: 20, y: 50, category: 'B' },
    { x: 30, y: 20, category: 'A' },
    { x: 40, y: 80, category: 'B' },
    { x: 50, y: 40, category: 'A' },
    { x: 60, y: 65, category: 'B' },
  ],
  encode: {
    x: 'x',
    y: 'y',
    color: 'category',
  },
});

chart.render();
```

## Bubble Chart (Three-Dimensional Data)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 500 });

chart.options({
  type: 'point',
  data: [
    { income: 30000, lifeExpect: 72, population: 1400, country: 'China'  },
    { income: 60000, lifeExpect: 79, population: 330,  country: 'USA'    },
    { income: 45000, lifeExpect: 84, population: 125,  country: 'Japan'  },
    { income: 20000, lifeExpect: 68, population: 1380, country: 'India'  },
    { income: 35000, lifeExpect: 80, population: 210,  country: 'Brazil' },
  ],
  encode: {
    x: 'income',
    y: 'lifeExpect',
    size: 'population',    // Bubble size = Third dimension
    color: 'country',
  },
  scale: {
    size: { range: [10, 60] },    // Control bubble size range
  },
  tooltip: {
    title: 'country',
    items: [
      { field: 'income',     name: 'Income per capita' },
      { field: 'lifeExpect', name: 'Life expectancy' },
      { field: 'population', name: 'Population (millions)' },
    ],
  },
});

chart.render();
```

## Custom Point Shapes

```javascript
chart.options({
  type: 'point',
  data: [...],
  encode: {
    x: 'x',
    y: 'y',
    color: 'type',
    shape: 'type',    // Map the type field to the shape channel
  },
  scale: {
    shape: {
      range: ['circle', 'square', 'triangle', 'diamond'],
    },
  },
});
```

## Scatter Plot + Trend Line

```javascript
// Use type: 'view' + children to overlay scatter plot and regression trend line
chart.options({
  type: 'view',
  data: [...],
  children: [
    {
      type: 'point',
      encode: { x: 'x', y: 'y' },
    },
    {
      type: 'line',
      encode: { x: 'x', y: 'y' },
      transform: [{ type: 'regression' }],
      style: { stroke: '#f00', lineWidth: 1.5 },
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Performance Issues with Large Datasets
```javascript
// ❌ Note: 100,000 points will cause slow rendering
chart.options({ type: 'point', data: hugeDataWith100000Points, encode: { x: 'x', y: 'y' } });

// ✅ Optimization 1: Sample the data first
chart.options({ type: 'point', data: sampledData, encode: { x: 'x', y: 'y' } });

// ✅ Optimization 2: Use a density chart to display distribution
chart.options({ type: 'density', data: [...], encode: { x: 'x', y: 'y' } });
```

### Error 2: Using String Literals in the `size` Channel
```javascript
// ❌ Misunderstanding: String in `size` is treated as a field name
chart.options({ type: 'point', encode: { size: '10' } });  // Looks for a field named '10'

// ✅ Correct: Use numbers for fixed sizes, field name strings for data mapping
chart.options({ type: 'point', encode: { size: 10 } });           // Fixed size 10
chart.options({ type: 'point', encode: { size: 'population' } }); // Maps to the 'population' field
```