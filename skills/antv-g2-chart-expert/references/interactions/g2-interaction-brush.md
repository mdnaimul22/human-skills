---
id: "g2-interaction-brush"
title: "G2 Brush Interaction"
description: |
  G2 v5 comes with built-in brush interaction, which can be implemented using interaction: [{ type: 'brushHighlight' }] or brushFilter. It allows users to drag and select, highlight, or filter data points using the mouse. This feature is commonly used in scatter plots, line charts, and other scenarios that require local focus.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "box selection"
  - "interaction"
  - "brushHighlight"
  - "brushFilter"
  - "interact"
  - "spec"

related:
  - "g2-mark-point-scatter"
  - "g2-interaction-element-highlight"
  - "g2-core-view-composition"

use_cases:
  - "Select a region of interest in a scatter plot"
  - "Select a time range in a time series chart and filter"
  - "Local focus analysis on large datasets"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/brush-highlight"
---

## Basic Usage (brushHighlight: Box Selection Highlight)

Drag the mouse to select data points, the selected area is highlighted, and the unselected area is dimmed:

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
    { x: 1, y: 4.8, category: 'A' },
    { x: 2, y: 3.2, category: 'B' },
    { x: 3, y: 6.1, category: 'A' },
    { x: 4, y: 2.5, category: 'C' },
    { x: 5, y: 7.3, category: 'B' },
    { x: 6, y: 5.0, category: 'A' },
    { x: 7, y: 1.8, category: 'C' },
  ],
  encode: { x: 'x', y: 'y', color: 'category', size: 8 },
  interaction: [
    { type: 'brushHighlight' },   // Box selection highlight
  ],
});

chart.render();
```

## brushFilter: Box Selection Filtering

After box selection, only the data points within the selected area are retained (the rest are removed):

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'category' },
  interaction: [
    { type: 'brushFilter' },   // Box selection filtering (only display points in the selected area)
  ],
});
```

## Scatter Plot + Box Selection + Detail Linkage

```javascript
chart.options({
  type: 'point',
  data,
  encode: {
    x: 'income',
    y: 'happiness',
    color: 'region',
    size: 'population',
  },
  scale: {
    size: { range: [4, 20] },
  },
  interaction: [
    { type: 'brushHighlight' },
    { type: 'tooltip' },         // Also retain tooltip interaction
  ],
  legend: { color: { position: 'top' } },
});
```

## Single-Axis Brush Selection (Horizontal/Vertical Only)

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'date', y: 'price' },
  interaction: [
    {
      type: 'brushXHighlight',   // Allows horizontal brush selection only (by time range)
    },
  ],
});

// Vertical brush selection: brushYHighlight
chart.options({
  interaction: [{ type: 'brushYHighlight' }],
});
```

## Brush Selection + Linkage with Other Charts

By listening to events, achieve multi-chart linkage:

```javascript
const chart = new Chart({ container: 'container', width: 700, height: 400 });

chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'type' },
  interaction: [{ type: 'brushFilter' }],
});

chart.render();

// Listen for brush selection events
chart.on('brush:filter', (event) => {
  const filteredData = event.data.items;   // Remaining data after brush selection
  console.log('Selected data:', filteredData);
  // Update other charts based on this...
});
```

## Common Errors and Fixes

### Error: `interaction` is written as an object instead of an array
```javascript
// ❌ Error: `interaction` must be an array
chart.options({
  interaction: { type: 'brushHighlight' },
});

// ✅ Correct: Array format
chart.options({
  interaction: [{ type: 'brushHighlight' }],
});
```

### Error: Enabling both brushHighlight and brushFilter simultaneously
```javascript
// ❌ Not recommended: The two functions conflict, and using them together will result in unexpected behavior
chart.options({
  interaction: [
    { type: 'brushHighlight' },
    { type: 'brushFilter' },
  ],
});

// ✅ Correct: Choose one based on requirements
chart.options({
  interaction: [{ type: 'brushHighlight' }],  // Highlight but retain all points
  // or
  // interaction: [{ type: 'brushFilter' }],  // Filter to show only selected points
});
```