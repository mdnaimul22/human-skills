---
id: "g2-core-view-composition"
title: "G2 View Composition (view + children)"
description: |
  G2 v5 implements multi-Mark overlay, shared data, facets, and other composite charts through the `type: 'view'` container and the `children` array.
  This is the standard way to compose multiple graphic layers in the Spec mode.

library: "g2"
version: "5.x"
category: "core"
tags:
  - "view"
  - "children"
  - "view composition"
  - "multi-Mark overlay"
  - "layer"
  - "composite chart"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-comp-annotation"
  - "g2-comp-facet-rect"

use_cases:
  - "Overlaying multiple graphics in the same coordinate system (line + scatter, area + line)"
  - "Sharing a data source for multiple child Marks"
  - "Adding an annotation layer to a chart"

anti_patterns:
  - "When there is only a single Mark, a view container is not needed; use the corresponding type directly"
  - "Nesting `type: 'view'` in children—when a child Mark requires independent data, specify the `data` field directly on that Mark instead of adding another layer of view + children"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/view"
---

## Core Concepts

```
chart.options({
  type: 'view',      // Container type
   [...],       // Parent data (can be inherited by child Marks)
  encode: {...},     // Parent encoding (can be inherited by child Marks)
  children: [        // Child Mark list (rendered in order, later ones on top)
    { type: 'area', ... },
    { type: 'line', ... },
    { type: 'point', ... },
  ],
});
```

**Data Inheritance Rules**:
- If a child Mark does not specify `data`, it inherits the parent's `data`
- If a child Mark does not specify `encode`, it inherits the corresponding channel from the parent's `encode`

## Area + Line + Scatter Overlay

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

const data = [
  { month: 'Jan', value: 33 },
  { month: 'Feb', value: 78 },
  { month: 'Mar', value: 56 },
  { month: 'Apr', value: 91 },
  { month: 'May', value: 67 },
];

chart.options({
  type: 'view',
  data,                                    // Parent data, shared by three child Marks
  encode: { x: 'month', y: 'value' },     // Parent encoding, inherited by child Marks
  children: [
    {
      type: 'area',
      style: { fill: '#1890ff', fillOpacity: 0.15 },
    },
    {
      type: 'line',
      style: { stroke: '#1890ff', lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { shape: 'circle' },
      style: { fill: 'white', stroke: '#1890ff', r: 4, lineWidth: 2 },
    },
  ],
});

chart.render();
```

## Child Mark Independent Data (Does Not Inherit from Parent)

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
       salesData,       // Independent data
      encode: { x: 'month', y: 'revenue' },
    },
    {
      type: 'line',
       trendData,       // Independent data
      encode: { x: 'month', y: 'growth' },
      scale: { y: { key: 'right' } },   // Independent y-axis
    },
  ],
});
```

## Line + Reference Line Combination

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value' },
    },
    {
      type: 'lineY',                       // Horizontal reference line
      thresholds: [{ threshold: 60 }],
      encode: { y: 'threshold' },
      style: { stroke: 'red', lineDash: [4, 4] },
      labels: [{ text: 'Target Line', position: 'right', style: { fill: 'red' } }],
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Overriding Configuration with Multiple Calls to `options()`
```javascript
// ❌ Incorrect: Each call to `options()` overrides the previous one
chart.options({ type: 'area', ... });
chart.options({ type: 'line', ... });   // Overrides the area chart!

// ✅ Correct: Use `view` + `children`
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'area', ... },
    { type: 'line', ... },
  ],
});
```

### Error 2: Nesting view in children (Common Pitfall When Transforming Data for Child Marks Individually)

```javascript
// ❌ Incorrect: Nesting type:'view' + children within children
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'time', y: 'value' } },
    {
      type: 'view',                        // ❌ Unnecessary nested view
      data: data.map(d => ({              // Only intended to use derived data
        time: d.time,
        min: d.value - 0.1,
        max: d.value + 0.1,
      })),
      children: [
        { type: 'rangeY', encode: { x: 'time', y: 'min', y1: 'max' } },
      ],
    },
  ],
});

// ✅ Correct: Directly specify data on the child Mark without nesting view
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'time', y: 'value' } },
    {
      type: 'rangeY',
      data: data.map(d => ({             // ✅ Directly declare independent data on the Mark
        time: d.time,
        min: d.value - 0.1,
        max: d.value + 0.1,
      })),
      encode: { x: 'time', y: 'min', y1: 'max' },
      style: { fillOpacity: 0.1 },
    },
  ],
});
```

**Rule**: Each element in the `children` array must be a Mark (`line`/`point`/`interval`, etc.).  
When a Mark requires independent or derived data, directly specify `data` on that Mark node instead of wrapping it in an additional `view`.  
G2 does not support nesting `view` within `children`.

### Error 3: Sub-Mark's encode Field Names Do Not Match the Data
```javascript
// ❌ Error: Field names in parent and child encode should be consistent
chart.options({
  type: 'view',
  data: [{ month: 'Jan', value: 33 }],
  encode: { x: 'month', y: 'value' },
  children: [
    {
      type: 'point',
      encode: { x: 'date', y: 'amount' },  // Field names do not match the data!
    },
  ],
});
```