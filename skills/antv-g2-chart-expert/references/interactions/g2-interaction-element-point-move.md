---
id: "g2-interaction-element-point-move"
title: "G2 ElementPointMove Data Point Drag-and-Drop Editing"
description: |
  elementPointMove is an interaction in G2 v5 that allows users to modify data values by dragging data points on the chart using the mouse.
  It supports line charts, bar charts, pie charts, area charts, etc., and triggers the 'element-point:moved' event callback with new data after dragging.
  It is suitable for scenarios such as data visualization editing, interactive budget adjustments, and manual correction of predicted values.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "elementPointMove"
  - "data editing"
  - "drag-and-drop"
  - "interactive"
  - "data modification"
  - "interaction"

related:
  - "g2-mark-line-basic"
  - "g2-mark-interval-basic"
  - "g2-interaction-element-select"

use_cases:
  - "Visual budget allocation editing (drag bars to adjust values)"
  - "Manual adjustment of predicted trends in line charts"
  - "Interactive adjustment of category proportions in pie charts"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/element-point-move"
---

## Core Concepts

`elementPointMove` renders draggable control points on chart elements, updating data and redrawing the chart in real-time as the mouse is pressed and dragged.
After the drag ends, the `element-point:moved` event is triggered, with the callback parameter containing the modified data.

Supported Mark Types:
- `line` (Line Chart): Each data point is draggable
- `area` (Area Chart): Each vertex is draggable
- `interval` (Bar Chart/Column Chart/Pie Chart): Bar vertices are draggable

## Line Chart Data Point Dragging

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', value: 83 },
  { month: 'Feb', value: 60 },
  { month: 'Mar', value: 95 },
  { month: 'Apr', value: 72 },
  { month: 'May', value: 110 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },
  interaction: {
    elementPointMove: true,   // Enable data point dragging
  },
});

// Listen for data change events
chart.on('element-point:moved', (event) => {
  const { changeData, data } = event.data;
  console.log('Modified single data:', changeData);
  console.log('Complete new data:', data);
});

chart.render();
```

## Bar Chart Data Point Dragging

```javascript
chart.options({
  type: 'interval',
  data: budgetData,
  encode: { x: 'department', y: 'budget', color: 'department' },
  interaction: {
    elementPointMove: {
      precision: 0,   // Dragging tooltip precision (decimal places), default is 2
    },
  },
});
```

## Configuration Options

```javascript
chart.options({
  interaction: {
    elementPointMove: {
      precision: 2,             // Decimal places for real-time tooltip, default 2
      selection: [],            // Initial selected data point indices [elementIndex, pointIndex]
      // Control point style
      pointR: 6,                // Control point radius, default 6
      pointStroke: '#888',      // Control point stroke color
      pointActiveStroke: '#f5f5f5',  // Active stroke color
      // Auxiliary line style
      pathStroke: '#888',
      pathLineDash: [3, 4],
      // Tooltip label style
      labelFontSize: 12,
      labelFill: '#888',
    },
  },
});
```

## Event Listening

```javascript
// Drag-end event (data has been updated)
chart.on('element-point:moved', ({ changeData, data }) => {
  // changeData: The modified single record { month: 'Feb', value: 75 }
  // data: The complete updated data array
  syncToServer(changeData);
});

// Control point selection event
chart.on('element-point:select', ({ selection }) => {
  // selection: [elementIndex, pointIndex]
  console.log('Selected point index:', selection);
});
```

## Common Errors and Fixes

### Error: Using (Unsupported) on Scatter Plot
```javascript
// ❌ point mark does not support elementPointMove
chart.options({
  type: 'point',
  interaction: { elementPointMove: true },  // Invalid
});

// ✅ Supported types: line, area, interval
chart.options({
  type: 'line',
  interaction: { elementPointMove: true },  // ✅
});
```