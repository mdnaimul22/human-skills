---
id: "g2-interaction-brush-xy"
title: "G2 Single-Axis Brush Selection (brushXHighlight / brushYHighlight / brushXFilter / brushYFilter)"
description: |
  Single-axis brush selection interaction restricts brushing to only one direction:
  - brushXHighlight/brushYHighlight: Brush to highlight, without filtering data
  - brushXFilter/brushYFilter: Brush and filter data (hide elements outside the brushed range)
  X-axis brushing is suitable for time series interval selection, while Y-axis brushing is suitable for numerical range filtering.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brushXHighlight"
  - "brushYHighlight"
  - "brushXFilter"
  - "brushYFilter"
  - "单轴框选"
  - "刷选"
  - "interaction"

related:
  - "g2-interaction-brush-filter"
  - "g2-interaction-brush-axis"
  - "g2-comp-slider"

use_cases:
  - "Time series charts: X-axis brush selection for time interval highlighting"
  - "Scatter plots: Y-axis brush selection for numerical range filtering"
  - "Line chart interval comparison annotations"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/brush-highlight"
---

## brushXHighlight (X-axis Box Selection Highlight)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'series' },
  interaction: {
    brushXHighlight: true,  // Horizontal box selection, highlights the selected range of the line chart
  },
});

chart.render();
```

## brushXFilter (X-axis Brush Filtering)

```javascript
// After brushing, only display data within the brushed range
chart.options({
  type: 'point',
  data: scatterData,
  encode: { x: 'date', y: 'value', color: 'category' },
  interaction: {
    brushXFilter: true,   // Brush X-axis range, filter out points outside the range
  },
});
```

## brushYFilter (Y-axis Box Selection Filter)

```javascript
// Box select value range, only display data with Y values within the selected interval
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'category', size: 'value' },
  interaction: {
    brushYFilter: true,   // Vertical box selection, filter out points outside the Y range
  },
});
```

## Comparison of Four Types of Box Selection Interactions

```javascript
// brushHighlight   → 2D box selection, highlight (no filter)
// brushFilter      → 2D box selection, filter data
// brushXHighlight  → X-axis box selection, highlight
// brushXFilter     → X-axis box selection, filter
// brushYHighlight  → Y-axis box selection, highlight
// brushYFilter     → Y-axis box selection, filter

// Supports highlighting on scatter plots (single X-axis box selection)
chart.options({
  interaction: {
    brushXHighlight: {
      series: true,        // Whether to highlight other points in the same series
    },
  },
});
```

## Common Errors and Fixes

### Error: Misunderstanding that brushXFilter and brushFilter have the same effect
```javascript
// brushFilter can select a rectangular area in both X and Y directions simultaneously
chart.options({ interaction: { brushFilter: true } });  // 2D rectangular selection

// brushXFilter can only be dragged in the X direction, forming a vertical strip
chart.options({ interaction: { brushXFilter: true } }); // X-axis direction only

// Different use cases: brushXFilter is more intuitive for time series
```