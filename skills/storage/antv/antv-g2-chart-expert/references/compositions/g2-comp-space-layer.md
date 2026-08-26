---
id: "g2-comp-space-layer"
title: "G2 Layer Overlay (spaceLayer / Multiple Marks in a View)"
description: |
  spaceLayer stacks multiple views in the same area (sharing axes),
  enabling combinations like line chart + bar chart, line chart + scatter plot, and other composite charts.
  A more common approach is to configure multiple marks using the children array within a single view.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "spaceLayer"
  - "layer"
  - "overlay"
  - "composite chart"
  - "dual-axis chart"
  - "view"
  - "children"

related:
  - "g2-core-view-composition"
  - "g2-comp-facet-rect"

use_cases:
  - "Bar Chart + Line Chart Overlay (Dual Metric Comparison)"
  - "Scatter Plot + Trend Line Overlay"
  - "Line Chart + Confidence Interval Area Overlay"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/space-layer"
---

## Minimum Viable Example (Bar Chart + Line Chart)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', sales: 200, growth: 15 },
  { month: 'Feb', sales: 280, growth: 22 },
  { month: 'Mar', sales: 320, growth: 8 },
  { month: 'Apr', sales: 250, growth: -5 },
  { month: 'May', sales: 410, growth: 18 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

// Method 1: type: 'view' + children (Recommended, most concise)
chart.options({
  type: 'view',
  data,
  children: [
    // Bar Chart: Display sales
    {
      type: 'interval',
      encode: { x: 'month', y: 'sales', color: '#5B8FF9' },
      style: { fillOpacity: 0.8 },
      axis: { y: { title: 'Sales' } },
    },
    // Line Chart: Display growth rate (shared x-axis)
    {
      type: 'line',
      encode: { x: 'month', y: 'growth' },
      scale: { y: { independent: true } },  // Independent y-axis (dual Y-axis)
      style: { lineWidth: 2.5, stroke: '#F4664A' },
      axis: { y: { position: 'right', title: 'Growth Rate (%)' } },
    },
  ],
});

chart.render();
```

## Line Chart + Scatter (Mark Composite)

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'date', y: 'value', color: 'type' },
      style: { lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { x: 'date', y: 'value', color: 'type' },
      style: { r: 4, lineWidth: 1, fill: '#fff' },
    },
  ],
});
```

## Area Chart + Line (Confidence Interval)

```javascript
chart.options({
  type: 'view',
  data: confidenceData,
  children: [
    // Confidence Interval (Area)
    {
      type: 'area',
      encode: { x: 'date', y: 'upper', y1: 'lower', color: '#5B8FF9' },
      style: { fillOpacity: 0.2 },
    },
    // Mean Line (Line)
    {
      type: 'line',
      encode: { x: 'date', y: 'mean' },
      style: { lineWidth: 2, stroke: '#5B8FF9' },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Dual Y-axis without setting independent: true—Both datasets are mapped to the same y-axis range
```javascript
// ❌ sales (0~400) and growth (-10~25) share a single y-axis, growth curve appears nearly horizontal
chart.options({
  type: 'view',
  children: [
    { type: 'interval', encode: { x: 'month', y: 'sales' } },
    { type: 'line',     encode: { x: 'month', y: 'growth' } },  // ❌ No independent y-axis
  ],
});

// ✅ Second y-axis set with independent: true
chart.options({
  type: 'view',
  children: [
    { type: 'interval', encode: { x: 'month', y: 'sales' } },
    {
      type: 'line',
      encode: { x: 'month', y: 'growth' },
      scale: { y: { independent: true } },  // ✅ Independent scale
      axis: { y: { position: 'right' } },    // ✅ Positioned on the right
    },
  ],
});
```