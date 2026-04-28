---
id: "g2-mark-box-boxplot"
title: "G2 Box Plot (Box Mark)"
description: |
  Create a box plot (also known as a box-and-whisker plot) using the Box Mark to display the quantile distribution of data:
  minimum, Q1 (25th percentile), median, Q3 (75th percentile), maximum, and outliers.
  This article uses the Spec mode.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "box"
tags:
  - "box plot"
  - "box-and-whisker plot"
  - "Box"
  - "boxplot"
  - "distribution"
  - "quantile"
  - "outliers"
  - "spec"

related:
  - "g2-mark-point-scatter"
  - "g2-core-encode-channel"

use_cases:
  - "Display the distribution and dispersion of numerical data"
  - "Compare distribution differences across multiple categories"
  - "Identify outliers"

anti_patterns:
  - "Box plots have no statistical significance with very small datasets (< 5 points)"
  - "Use a violin plot or scatter plot instead when needing to display the distribution of specific data points"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/statistics/boxplot"
---

## Core Concepts

Box Mark requires 5 numerical channels:
- `y`: Median (Q2)
- `y1`: Q1 (25th percentile)
- `y2`: Q3 (75th percentile)
- `y3`: Lower whisker (minimum non-outlier value)
- `y4`: Upper whisker (maximum non-outlier value)

**Data Format**: Data must be pre-calculated with percentiles or use raw data with the `boxplot` transform for automatic calculation.

## Use boxplot transform for automatic calculation (recommended)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

// Raw data, each category has multiple observations
const rawData = [
  { category: 'A', value: 10 },
  { category: 'A', value: 25 },
  { category: 'A', value: 30 },
  { category: 'A', value: 45 },
  { category: 'A', value: 50 },
  { category: 'A', value: 55 },
  { category: 'A', value: 80 },   // Outlier
  { category: 'B', value: 20 },
  { category: 'B', value: 35 },
  { category: 'B', value: 40 },
  { category: 'B', value: 48 },
  { category: 'B', value: 52 },
  { category: 'B', value: 65 },
];

chart.options({
  type: 'boxplot',          // boxplot is a shortcut combination of box mark + boxplot transform
  data: rawData,
  encode: {
    x: 'category',
    y: 'value',
  },
  style: {
    fill: '#1890ff',
    fillOpacity: 0.3,
    stroke: '#1890ff',
  },
});

chart.render();
```

## Pre-calculated Quantile Data

```javascript
// Data already includes quantile fields
chart.options({
  type: 'box',
  data: [
    { category: 'A', min: 10, q1: 25, median: 45, q3: 55, max: 75 },
    { category: 'B', min: 20, q1: 35, median: 48, q3: 58, max: 80 },
    { category: 'C', min: 5,  q1: 20, median: 35, q3: 50, max: 65 },
  ],
  encode: {
    x: 'category',
    y: 'median',     // Median
    y1: 'q1',        // Lower quartile
    y2: 'q3',        // Upper quartile
    y3: 'min',       // Lower whisker
    y4: 'max',       // Upper whisker
  },
  style: {
    fill: '#1890ff',
    fillOpacity: 0.3,
    stroke: '#1890ff',
    lineWidth: 1.5,
  },
});
```

## Boxplot + Scatter (Displaying Raw Data Points)

```javascript
chart.options({
  type: 'view',
  data: rawData,
  children: [
    {
      type: 'boxplot',
      encode: { x: 'category', y: 'value' },
      style: { fill: '#1890ff', fillOpacity: 0.2, stroke: '#1890ff' },
    },
    {
      // Overlay raw data points
      type: 'point',
      encode: { x: 'category', y: 'value' },
      transform: [{ type: 'jitter' }],   // jitter to avoid point overlap
      style: { fill: '#1890ff', fillOpacity: 0.5, r: 3 },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Box Mark Missing y1/y2/y3/y4 Channels
```javascript
// ❌ Error: Box mark requires 5 y channels, missing channels will cause rendering anomalies
chart.options({
  type: 'box',
  encode: { x: 'category', y: 'median' },  // Missing y1-y4!
});

// ✅ Correct: Use boxplot (auto-calculation) or complete all channels
chart.options({ type: 'boxplot', encode: { x: 'category', y: 'value' } });
```