---
id: "g2-coord-transpose"
title: "G2 Transpose Coordinate System (Convert Bar Chart to Horizontal Bar Chart)"
description: |
  Use `coordinate: { transform: [{ type: 'transpose' }]` to swap the x/y axes of the Cartesian coordinate system,
  most commonly used to convert a vertical bar chart to a horizontal bar chart.
  Suitable for scenarios with long category names or many categories.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "transpose"
  - "转置"
  - "bar chart"
  - "horizontal"
  - "水平"
  - "coordinate"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-interval-grouped"
  - "g2-mark-interval-stacked"

use_cases:
  - "Horizontal bar charts provide clearer labels when category names are long"
  - "Horizontal arrangement is more aesthetically pleasing when there are many categories (> 8)"
  - "Ranking charts (arranged horizontally from largest to smallest)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/transpose"
---

## Minimum Viable Example (Bar Chart to Column Chart)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { city: 'Beijing', gdp: 3.6 },
    { city: 'Shanghai', gdp: 4.3 },
    { city: 'Guangzhou', gdp: 2.8 },
    { city: 'Shenzhen', gdp: 3.2 },
    { city: 'Hangzhou', gdp: 1.8 },
  ],
  encode: {
    x: 'city',   // After transposition, city is on the y-axis (vertical direction)
    y: 'gdp',    // After transposition, gdp is on the x-axis (horizontal direction)
  },
  coordinate: { transform: [{ type: 'transpose' }] },   // Key: Transpose the coordinate system
});

chart.render();
```

## Ranking Bar Chart (Sorting + Transpose)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'city', y: 'gdp', color: 'city' },
  transform: [
    { type: 'sortX', by: 'y', reverse: true },   // Sort by value in descending order first
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: {
    x: { title: 'GDP (Trillion Yuan)' },
    y: { title: null },
  },
  labels: [
    {
      text: (d) => d.gdp.toFixed(1),
      position: 'outside',
      style: { fontSize: 12 },
    },
  ],
});
```

## Horizontal Stacked Bar Chart

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

## Horizontal Interval Chart (Gantt Chart Style)

```javascript
chart.options({
  type: 'interval',
  autoFit: true,
  data: [
    { stage: 'Phase 1', task: 'Prototype', start: 1, end: 3 },
    { stage: 'Phase 1', task: 'Validation', start: 3, end: 5 },
    { stage: 'Phase 2', task: 'Development', start: 4, end: 10 },
    { stage: 'Phase 2', task: 'Unit Testing', start: 8, end: 11 },
    { stage: 'Phase 3', task: 'Integration', start: 10, end: 13 },
    { stage: 'Phase 3', task: 'Stress Testing', start: 12, end: 15 }
  ],
  encode: {
    x: (d) => `${d.stage} - ${d.task}`,  // Combine label fields
    y: 'start',                          // Map start time to y-axis
    y1: 'end',                           // Map end time to y1 channel
    color: 'stage'                       // Map stage to color
  },
  coordinate: { transform: [{ type: 'transpose' }] },  // Transpose coordinate system
  axis: {
    x: {
      title: 'Stage and Task',
      labelTransform: 'rotate(30)'       // Rotate labels to prevent overlap
    },
    y: { title: 'Time (Weeks)' }         // Time axis title
  }
});

chart.render();
```

## Common Errors and Fixes

### Error: Axis Title Configuration Not Adjusted After Transposition
```javascript
// ❌ Note: After transposition, the original x configuration applies to the vertical axis, and the original y configuration applies to the horizontal axis
// If the horizontal axis needs to display the unit of measurement, configure axis.x (instead of axis.y)
chart.options({
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: {
    y: { title: 'GDP (Trillions)' },   // ❌ After transposition, the y-axis is a categorical axis, not a numerical axis
  },
});

// ✅ Correct: The "horizontal axis" after transposition corresponds to axis.x in the configuration
chart.options({
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: {
    x: { title: 'GDP (Trillions)' },   // ✅ Numerical axis
    y: { title: null },                 // ✅ Categorical axis (category names are already on the left, no title needed)
  },
});
```

### Error: Improper Handling of Labels in Horizontal Range Charts
```javascript
// ❌ Incorrect Example: Using labelFormatter for combined labels is prone to errors
chart.options({
  encode: {
    x: 'task',
    y: 'start',
    y1: 'end'
  },
  axis: {
    x: {
      labelFormatter: (task, item) => {
        const datum = item.data;
        return `${datum.stage}\n${task}`;
      }
    }
  }
});

// ✅ Correct Approach: Construct combined fields during data preprocessing
chart.options({
  encode: {
    x: (d) => `${d.stage} - ${d.task}`,  // Use a function to construct combined labels
    y: 'start',
    y1: 'end'
  },
  axis: {
    x: {
      title: 'Stage and Task',
      labelTransform: 'rotate(30)'        // Rotate labels appropriately to avoid overlap
    }
  }
});
```