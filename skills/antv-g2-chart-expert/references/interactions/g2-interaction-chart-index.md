---
id: "g2-interaction-chart-index"
title: "G2 ChartIndex Linked Crosshair"
description: |
  chartIndex renders a vertical crosshair (reference line) on the chart that moves with the mouse,
  and can link the crosshairs of multiple charts, enabling horizontal comparison of data at the same time point across multiple charts.
  It is suitable for scenarios involving multi-chart linkage of time-series data and synchronized viewing of multiple metrics in a Dashboard.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "chartIndex"
  - "crosshair"
  - "linkage"
  - "reference line"
  - "multi-chart linkage"
  - "interaction"
  - "crosshair"

related:
  - "g2-interaction-tooltip"
  - "g2-mark-linex-liney"
  - "g2-recipe-dashboard"

use_cases:
  - "Linking multiple line charts to view values of various metrics at the same time point"
  - "Crosshair in a time-series data Dashboard"
  - "Comparing concurrent data of two time series"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/chart-index"
---

## Core Concepts

`chartIndex` renders a vertical reference line in the plotting area, moving with the mouse's X-axis position.
When used with a Tooltip that has `shared: true`, it enables synchronized highlighting of data from multiple series at the same time.

## Single Chart Cursor Line

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  interaction: {
    chartIndex: true,          // Enable cursor line
    tooltip: { shared: true }, // Combine with shared Tooltip
  },
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  interaction: {
    chartIndex: {
      // Cursor line style
      ruleStroke: '#aaa',          // Cursor line color, default '#aaa'
      ruleLineWidth: 1,            // Cursor line width, default 1
      ruleLineDash: [4, 4],        // Cursor line dash style
      // Label configuration
      labelDy: -8,                 // Label vertical offset
      labelBackground: true,       // Whether to display label background
      labelBackgroundFill: '#fff', // Label background color
      // Performance control
      wait: 50,                    // Debounce time (milliseconds), default 50
      leading: true,               // Debounce leading trigger
      trailing: false,             // Debounce trailing trigger
    },
  },
});
```

## Multi-Chart Linkage (Same Container Parent Element)

```javascript
// Achieve multi-chart cursor linkage by sharing emit events
// Two charts use the same emitter (need to manually implement or use G2's on/emit API)
const chart1 = new Chart({ container: 'container1', width: 800, height: 200 });
const chart2 = new Chart({ container: 'container2', width: 800, height: 200 });

[chart1, chart2].forEach((chart) => {
  chart.options({
    type: 'line',
    data: timeSeriesData,
    encode: { x: 'date', y: 'value' },
    interaction: {
      chartIndex: true,
    },
  });
  chart.render();
});
```

## Common Errors and Fixes

### Error: Cursor Line Appears but Tooltip Does Not Display Data at the Same Time
```javascript
// ❌ Multi-series chart, Tooltip only shows the element closest to the current mouse position
chart.options({
  interaction: {
    chartIndex: true,
    // Missing tooltip shared configuration
  },
});

// ✅ Enable shared Tooltip, data from all series at the same time is displayed together
chart.options({
  interaction: {
    chartIndex: true,
    tooltip: { shared: true },   // Must be used together
  },
});
```