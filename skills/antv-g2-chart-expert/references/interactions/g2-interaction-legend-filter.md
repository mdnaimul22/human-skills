---
id: "g2-interaction-legend-filter"
title: "G2 Legend Filter Interaction (legendFilter)"
description: |
  legendFilter allows users to show/hide corresponding data series by clicking on legend items.
  In G2 v5, it is enabled by default, and clicking a legend item toggles the visibility of the corresponding series.
  It can be disabled or customized through configuration. legendHighlight highlights the corresponding series when the mouse hovers over a legend item.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "legendFilter"
  - "legend filtering"
  - "legend highlighting"
  - "legendHighlight"
  - "interaction"

related:
  - "g2-comp-legend-config"
  - "g2-interaction-element-highlight"

use_cases:
  - "Show/hide specific series on demand in multi-series line charts"
  - "Temporarily hide a category in stacked charts"
  - "Selective viewing when there are a large number of series"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/legend-filter"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', city: 'Beijing', temp: -3 },
  { month: 'Feb', city: 'Beijing', temp: 0 },
  { month: 'Jan', city: 'Shanghai', temp: 5 },
  { month: 'Feb', city: 'Shanghai', temp: 7 },
  { month: 'Jan', city: 'Guangzhou', temp: 15 },
  { month: 'Feb', city: 'Guangzhou', temp: 16 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'temp', color: 'city' },
  // legendFilter is enabled by default, no explicit configuration needed
  // Click on the city name in the legend to toggle visibility
});

chart.render();
```

## Explicitly Enable legendFilter

```javascript
// If disabled, it can be explicitly re-enabled
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  interaction: {
    legendFilter: true,   // Click legend to toggle show/hide
  },
});
```

## Enable legendHighlight (Hover Highlight) Simultaneously

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  interaction: {
    legendFilter: true,    // Click: Filter data
    legendHighlight: true, // Hover: Highlight series
  },
});
```

## Disable Legend Interaction

```javascript
// Disable legend filtering (legend is for display only, not clickable)
chart.options({
  interaction: {
    legendFilter: false,  // Disable click filtering
  },
});
```

## Common Errors and Fixes

### Error: Mistakenly believed that legendFilter requires manual configuration - actually, it is enabled by default in G2 v5
```javascript
// ℹ️  legendFilter is enabled by default in G2 v5, no additional configuration is needed
// Explicit configuration is only required in the following cases:

// 1. When you want to disable it
chart.options({ interaction: { legendFilter: false } });

// 2. When you want to customize the style or behavior
chart.options({ interaction: { legendFilter: { /* custom options */ } } });
```

### Error: Still Wanting legendFilter When legend: false - Unable to Interact After Hiding Legend
```javascript
// ❌ Hiding the legend but still wanting legend filtering - cannot click when legend is invisible
chart.options({
  legend: false,
  interaction: { legendFilter: true },  // ❌ No legend, filtering cannot be triggered
});

// ✅ legendFilter requires a visible legend to work
chart.options({
  legend: { color: { position: 'top' } },  // ✅ Retain the legend
  interaction: { legendFilter: true },
});
```