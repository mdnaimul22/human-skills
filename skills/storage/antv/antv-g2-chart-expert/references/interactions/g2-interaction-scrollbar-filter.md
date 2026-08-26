---
id: "g2-interaction-scrollbar-filter"
title: "G2 ScrollbarFilter Interaction"
description: |
  scrollbarFilter is an interaction in G2 v5 that filters the visible data range using an embedded scrollbar within the chart.
  Similar to sliderFilter, but uses a more compact scrollbar control (instead of a slider),
  suitable for scenarios with large datasets that require pagination (e.g., bar charts with numerous categories).
  Must be used in conjunction with the scrollbar component (scrollbar: { x: true }).

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "scrollbarFilter"
  - "scrollbar"
  - "data filtering"
  - "pagination"
  - "interaction"

related:
  - "g2-interaction-slider-filter"
  - "g2-comp-scrollbar"
  - "g2-mark-interval-basic"

use_cases:
  - "Horizontal scrolling for bar charts with excessive categories"
  - "Pagination for long time-series data"
  - "Partial display of large categorized datasets"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/scrollbar"
---

## Core Concepts

The `scrollbarFilter` interaction needs to work in conjunction with the `scrollbar` component:
- `scrollbar` field: Controls the display position of the scrollbar (x-axis / y-axis)
- `scrollbarFilter` interaction: Responds to scrollbar drag events, filtering the data range

Difference from `sliderFilter`:
- `sliderFilter`: Dual-ended slider, supports arbitrary range selection
- `scrollbarFilter`: Fixed-size scrollbar, can only pan and cannot zoom the range

## Basic Usage (X-axis Scrollbar)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 600, height: 400 });

chart.options({
  type: 'interval',
  manyCategories,   // Large number of category data
  encode: { x: 'category', y: 'value' },
  scrollbar: {
    x: true,   // Enable X-axis scrollbar
  },
  interaction: {
    scrollbarFilter: true,   // Enable scrollbar filtering
  },
});

chart.render();
```

## Y-Axis Scrollbar

```javascript
chart.options({
  type: 'interval',
  data: manyCategories,
  encode: { x: 'value', y: 'category' },  // Bar chart
  coordinate: { transform: [{ type: 'transpose' }] },
  scrollbar: {
    y: true,   // Enable Y-axis scrollbar (vertical scrolling for bar chart)
  },
  interaction: {
    scrollbarFilter: true,
  },
});
```

## Configuration Options

```javascript
chart.options({
  scrollbar: {
    x: {
      ratio: 0.3,    // Initial scrollbar window ratio (displaying 30% of all data), default is calculated based on data volume
    },
  },
  interaction: {
    scrollbarFilter: {
      // Currently, scrollbarFilter has fewer options, primarily configured through the scrollbar component
    },
  },
});
```

## Common Errors and Fixes

### Error: Forgot to configure the scrollbar component
```javascript
// ❌ Only added interaction but no scrollbar component, the scrollbar will not be displayed
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  interaction: { scrollbarFilter: true },  // ❌ No scrollbar component
});

// ✅ Must configure the scrollbar component simultaneously
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  scrollbar: { x: true },              // ✅ Enable the scrollbar component
  interaction: { scrollbarFilter: true },  // ✅ Enable filter interaction
});
```

### Error: Mixed Use with sliderFilter
```javascript
// ❌ Enabling scrollbar and slider simultaneously will cause conflicts
chart.options({
  scrollbar: { x: true },
  slider: { x: true },
  interaction: {
    scrollbarFilter: true,
    sliderFilter: true,   // ❌ Do not enable both at the same time
  },
});

// ✅ Choose one of them
chart.options({
  scrollbar: { x: true },
  interaction: { scrollbarFilter: true },
});
```