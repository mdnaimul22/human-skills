---
id: "g2-comp-facet-rect"
title: "G2 Rectangular Facet (facetRect)"
description: |
  facetRect splits data by categorical fields and renders a separate sub-chart for each category in a grid layout.
  It is suitable for comparing data distributions and trends across different groups. Specify facet dimensions using type: 'facetRect' + encode.x/y.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "facetRect"
  - "facet"
  - "small multiples"
  - "trellis"
  - "grid layout"
  - "spec"

related:
  - "g2-core-view-composition"
  - "g2-mark-interval-basic"
  - "g2-mark-point-scatter"

use_cases:
  - "Compare data distributions across different categories"
  - "Multi-dimensional time series comparison"
  - "Facet display by region/product/department"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/facet-rect"
---

## Basic Concepts

```
chart.options({
  type: 'facetRect',
  encode: {
    x: 'Facet Column Field',      // Split data into multiple columns by this field
    y: 'Facet Row Field',         // Split data into multiple rows by this field (optional)
  },
  children: [
    { type: 'Child Mark', ... },  // Configuration for each subplot (shared, data automatically filtered)
  ],
});
```

**Key Rules**:
- `encode.x` → Split into multiple columns by unique values of this field (column faceting)
- `encode.y` → Split into multiple rows by unique values of this field (row faceting)
- Marks in `children` automatically receive filtered data

## Single-Dimensional Column Facet (Categorized by Region)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 800,
  height: 300,
});

const data = [
  { month: 'Jan', value: 33, region: 'East China' },
  { month: 'Feb', value: 78, region: 'East China' },
  { month: 'Mar', value: 56, region: 'East China' },
  { month: 'Jan', value: 45, region: 'South China' },
  { month: 'Feb', value: 62, region: 'South China' },
  { month: 'Mar', value: 71, region: 'South China' },
  { month: 'Jan', value: 28, region: 'North China' },
  { month: 'Feb', value: 39, region: 'North China' },
  { month: 'Mar', value: 53, region: 'North China' },
];

chart.options({
  type: 'facetRect',
  data,
  encode: { x: 'region' },     // Facet by region column (3 columns)
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'value' },
      style: { fill: '#1890ff' },
    },
  ],
});

chart.render();
```

## Two-Dimensional Faceting (Row + Column)

```javascript
const data = [
  { quarter: 'Q1', value: 100, region: 'East China', type: 'Online' },
  { quarter: 'Q2', value: 130, region: 'East China', type: 'Online' },
  { quarter: 'Q1', value: 80,  region: 'South China', type: 'Online' },
  { quarter: 'Q2', value: 95,  region: 'South China', type: 'Online' },
  { quarter: 'Q1', value: 60,  region: 'East China', type: 'Offline' },
  { quarter: 'Q2', value: 85,  region: 'East China', type: 'Offline' },
  { quarter: 'Q1', value: 40,  region: 'South China', type: 'Offline' },
  { quarter: 'Q2', value: 55,  region: 'South China', type: 'Offline' },
];

chart.options({
  type: 'facetRect',
  data,
  encode: {
    x: 'region',   // Column: East China/South China
    y: 'type',     // Row: Online/Offline
  },
  children: [
    {
      type: 'interval',
      encode: { x: 'quarter', y: 'value' },
    },
  ],
});
```

## Facet Line Chart (Multi-Series Trend Comparison)

```javascript
chart.options({
  type: 'facetRect',
  data,
  encode: { x: 'product' },          // Facet by product
  children: [
    {
      type: 'view',
      children: [
        {
          type: 'area',
          encode: { x: 'month', y: 'sales' },
          style: { fill: '#1890ff', fillOpacity: 0.15 },
        },
        {
          type: 'line',
          encode: { x: 'month', y: 'sales' },
          style: { stroke: '#1890ff', lineWidth: 2 },
        },
      ],
    },
  ],
});
```

## Configure Facet Title Style

```javascript
chart.options({
  type: 'facetRect',
  data,
  encode: { x: 'region' },
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'value' },
    },
  ],
  // Facet title configuration (via the frame field)
  frame: false,                        // Whether to display the border
  // Title configured through facetRect's title
  title: {
    position: 'top',                   // Title at the top
    style: { fontSize: 13, fill: '#333', fontWeight: 'bold' },
  },
});
```

## Shared Coordinate Axis (shareData)

```javascript
chart.options({
  type: 'facetRect',
  data,
  encode: { x: 'category' },
  shareData: true,          // Shared data range (consistent axis scales)
  children: [
    {
      type: 'point',
      encode: { x: 'x', y: 'y', color: 'category' },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Data is written in the children of facetRect
```javascript
// ❌ Error: Data should not be specified again in the child Mark, otherwise facet filtering will not take effect
chart.options({
  type: 'facetRect',
  data: allData,
  encode: { x: 'region' },
  children: [
    {
      type: 'interval',
      data: allData,            // ❌ Causes each facet to display all data
      encode: { x: 'month', y: 'value' },
    },
  ],
});

// ✅ Correct: Child Mark does not specify data, automatically receives filtered data from the facet
chart.options({
  type: 'facetRect',
  data: allData,
  encode: { x: 'region' },
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'value' },   // No data specified, inherits and automatically filters
    },
  ],
});
```

### Error: Mismatch between encode field and data field name
```javascript
// ❌ Error: The facet field specified by encode.x does not exist in the data
chart.options({
  type: 'facetRect',
  data: [{ month: 'Jan', value: 33, area: '华东' }],
  encode: { x: 'region' },   // ❌ Data contains 'area', not 'region'
});

// ✅ Correct: Field name matches the data
chart.options({
  type: 'facetRect',
  data,
  encode: { x: 'area' },     // ✅ Matches the data field name
});
```