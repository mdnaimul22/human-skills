---
id: "g2-mark-radar"
title: "G2 Radar Chart (Polar Coordinate + Area/Line)"
description: |
  G2 v5 radar chart is implemented using coordinate: { type: 'polar' } + area + line Mark combination,
  Data uses long table format, encode.x maps dimension fields, encode.y maps numerical fields,
  encode.color distinguishes multiple series.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "radar chart"
  - "radar"
  - "polar"
  - "polar coordinate"
  - "spider chart"
  - "multi-dimensional"
  - "spec"

related:
  - "g2-core-view-composition"
  - "g2-mark-area-basic"
  - "g2-mark-line-basic"

use_cases:
  - "Multi-dimensional capability/indicator comparison (e.g., KPI radar chart)"
  - "Comprehensive score comparison of multiple objects"
  - "Multi-dimensional evaluation of athletes/products"

anti_patterns:
  - "When dimensions exceed 8, labels will overlap, switch to parallel coordinate chart"
  - "When dimension scales differ significantly, normalization is required first"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/radar"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 480,
  height: 480,
});

const data = [
  { item: 'Design', type: 'Product A', score: 70 },
  { item: 'Development', type: 'Product A', score: 60 },
  { item: 'Marketing', type: 'Product A', score: 50 },
  { item: 'Operations', type: 'Product A', score: 80 },
  { item: 'Service', type: 'Product A', score: 90 },
  { item: 'Design', type: 'Product B', score: 40 },
  { item: 'Development', type: 'Product B', score: 75 },
  { item: 'Marketing', type: 'Product B', score: 85 },
  { item: 'Operations', type: 'Product B', score: 55 },
  { item: 'Service', type: 'Product B', score: 65 },
];

chart.options({
  type: 'view',
  data,
  coordinate: { type: 'polar' },   // Key: Polar coordinate
  scale: {
    x: { padding: 0.5, align: 0 },
    y: { tickCount: 5, domainMin: 0, domainMax: 100 },
  },
  axis: {
    x: { grid: true },
    y: { zIndex: 1, title: false },
  },
  children: [
    {
      type: 'area',
      encode: { x: 'item', y: 'score', color: 'type' },
      style: { fillOpacity: 0.2 },
    },
    {
      type: 'line',
      encode: { x: 'item', y: 'score', color: 'type' },
      style: { lineWidth: 2 },
    },
  ],
});

chart.render();
```

## Radar Chart with Data Points

```javascript
chart.options({
  type: 'view',
  data,
  coordinate: { type: 'polar' },
  scale: {
    x: { padding: 0.5, align: 0 },
    y: { tickCount: 5, domainMin: 0 },
  },
  axis: {
    x: { grid: true, labelFontSize: 13 },
    y: { zIndex: 1, title: false, label: false },  // Hide y-axis labels (show grid only)
  },
  children: [
    {
      type: 'area',
      encode: { x: 'item', y: 'score', color: 'type' },
      style: { fillOpacity: 0.15 },
    },
    {
      type: 'line',
      encode: { x: 'item', y: 'score', color: 'type' },
      style: { lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { x: 'item', y: 'score', color: 'type' },
      style: { r: 4, fill: 'white', lineWidth: 2 },
    },
  ],
  legend: { color: { position: 'top' } },
  interaction: [{ type: 'tooltip' }],
});
```

## Single Series Radar Chart (Solid Color Fill)

```javascript
const singleData = [
  { item: 'Attack', score: 85 },
  { item: 'Defense', score: 72 },
  { item: 'Speed', score: 90 },
  { item: 'Magic', score: 60 },
  { item: 'Stamina', score: 78 },
  { item: 'Luck', score: 66 },
];

chart.options({
  type: 'view',
  data: singleData,
  coordinate: { type: 'polar' },
  scale: {
    x: { padding: 0.5, align: 0 },
    y: { tickCount: 4, domainMin: 0, domainMax: 100 },
  },
  axis: {
    x: { grid: true, labelFontSize: 14 },
    y: { zIndex: 1, title: false },
  },
  children: [
    {
      type: 'area',
      encode: { x: 'item', y: 'score' },
      style: { fill: '#1890ff', fillOpacity: 0.25 },
    },
    {
      type: 'line',
      encode: { x: 'item', y: 'score' },
      style: { stroke: '#1890ff', lineWidth: 2 },
    },
    {
      type: 'point',
      encode: { x: 'item', y: 'score' },
      style: { r: 5, fill: '#1890ff' },
      labels: [{ text: (d) => d.score, position: 'top', style: { fontSize: 11 } }],
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Forgetting to Set Polar Coordinates, Resulting in a Regular Area Line Chart
```javascript
// ❌ Missing coordinate, renders a regular line chart instead of a radar chart
chart.options({
  type: 'view',
  data,
  // Forgot coordinate: { type: 'polar' }
  children: [{ type: 'area', ... }],
});

// ✅ Correct: Must declare polar coordinates
chart.options({
  type: 'view',
  data,
  coordinate: { type: 'polar' },   // ✅ Key
  children: [{ type: 'area', ... }],
});
```

### Error 2: Using Wide Table Data Format

```javascript
// ❌ Wide table format cannot directly use color to distinguish series
const wrongData = [
  { item: 'Design', A: 70, B: 40 },
  { item: 'Development', A: 60, B: 75 },
];

// ✅ Correct: Use long table format (one data point per row + series field)
const correctData = [
  { item: 'Design', type: 'A', score: 70 },
  { item: 'Design', type: 'B', score: 40 },
  { item: 'Development', type: 'A', score: 60 },
  { item: 'Development', type: 'B', score: 75 },
];
```

### Error 3: Inconsistent Measurement Scales Across Dimensions Leading to Visual Distortion

```javascript
// ❌ Large differences in measurement scales across dimensions (0-100 vs 0-10000), causing severe visual distortion
const data = [
  { item: 'Sales', score: 8500 },   // Ten thousand yuan
  { item: 'Rating', score: 85 },    // Percentage
];

// ✅ Normalize to 0-100 before rendering
const normalized = data.map(d => ({
  ...d,
  score: (d.score / maxScores[d.item]) * 100,
}));
```