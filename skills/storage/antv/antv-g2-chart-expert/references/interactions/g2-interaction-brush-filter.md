---
id: "g2-interaction-brush-filter"
title: "G2 Brush Filter Interaction (brushFilter)"
description: |
  brushFilter allows users to drag and draw a rectangular area on the chart to filter data.
  Unlike brushHighlight, brushFilter directly filters out data points outside the selected area,
  retaining only the data within the selected region. It supports single-axis filtering in the x/y direction and two-dimensional rectangular filtering.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "brushFilter"
  - "刷选"
  - "过滤"
  - "交互"
  - "interaction"

related:
  - "g2-interaction-brush"
  - "g2-interaction-element-select"

use_cases:
  - "Select data points of interest in a scatter plot for in-depth analysis"
  - "Select a specific time period in a time series for zoomed viewing"
  - "Multi-dimensional data exploration: Rectangular selection of data subsets"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/brush-filter"
---
## Minimum Viable Example (Scatter Plot Brush Filtering)

```javascript
import { Chart } from '@antv/g2';

const data = Array.from({ length: 300 }, () => ({
  x: Math.random() * 100,
  y: Math.random() * 100,
  group: Math.floor(Math.random() * 4),
}));

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'group', shape: 'point' },
  scale: { color: { type: 'ordinal' } },
  interaction: {
    brushFilter: true,   // Enable brush filtering: Drag a rectangular area to filter data
  },
});

chart.render();
```

## Brush Selection Only in the X-Axis Direction (Time Range Filtering)

```javascript
chart.options({
  type: 'line',
  data: timeData,
  encode: { x: 'date', y: 'value', color: 'type' },
  interaction: {
    brushXFilter: true,   // Brush selection filtering only in the X-axis direction (commonly used for time filtering)
  },
});
```

## Custom Brush Filter Style

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: {
    brushFilter: {
      maskFill: '#1890ff',
      maskFillOpacity: 0.15,
      maskStroke: '#1890ff',
      maskLineWidth: 1.5,
    },
  },
});
```

## Brush Highlight vs Brush Filter

```javascript
// brushHighlight: Elements outside the selection area are dimmed (all data remains visible)
chart.options({ interaction: { brushHighlight: true } });

// brushFilter: Elements outside the selection area are filtered out (only selected data remains)
chart.options({ interaction: { brushFilter: true } });
```

## Common Errors and Fixes

### Error: brushFilter and brushHighlight Enabled Simultaneously—Behavior Conflict
```javascript
// ❌ Enabling both simultaneously causes a conflict
chart.options({
  interaction: {
    brushFilter: true,
    brushHighlight: true,  // ❌ Conflicts with brushFilter
  },
});

// ✅ Enable only one of them
chart.options({
  interaction: {
    brushFilter: true,  // ✅ Filter mode
  },
});
```