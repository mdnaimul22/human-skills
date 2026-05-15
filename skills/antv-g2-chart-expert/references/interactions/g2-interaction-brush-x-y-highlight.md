---
id: "g2-interaction-brush-x-highlight"
title: "G2 BrushXHighlight / BrushYHighlight Single-Axis Box Selection Highlight"
description: |
  brushXHighlight and brushYHighlight are interactions in G2 v5,
  restricting the box selection range to the X-axis (or Y-axis) direction, highlighting elements within the selected area, and fading out non-selected areas with semi-transparency.
  Suitable for scenarios such as time series comparison and local trend focus.
  If data filtering rather than highlighting is needed, use brushXFilter / brushYFilter.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brushXHighlight"
  - "brushYHighlight"
  - "box selection highlight"
  - "X-axis box selection"
  - "Y-axis box selection"
  - "interaction"
  - "highlight"

related:
  - "g2-interaction-brush"
  - "g2-interaction-brush-filter"
  - "g2-interaction-brush-xy"

use_cases:
  - "Select a time period on the timeline and highlight corresponding data points"
  - "Select and highlight specific categories in horizontal comparison charts"
  - "Highlight outlier regions in scatter plots based on Y-axis range"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/brush-x-highlight"
---

## Core Concepts

- `brushXHighlight`: Brush selection only in the X-axis direction, highlighting selected elements while fading out the rest.
- `brushYHighlight`: Brush selection only in the Y-axis direction, highlighting selected elements while fading out the rest.
- Highlighting does not filter data; all data remains visible (unlike `brushXFilter`).

## BrushXHighlight Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  interaction: {
    brushXHighlight: true,   // Enable X-axis brush highlighting
  },
});

chart.render();
```

## Basic Usage of BrushYHighlight

```javascript
chart.options({
  type: 'point',
  data: scatterData,
  encode: { x: 'x', y: 'y', color: 'category' },
  interaction: {
    brushYHighlight: true,   // Enable Y-axis brush highlighting
  },
});
```

## Configuration Options

```javascript
chart.options({
  interaction: {
    brushXHighlight: {
      series: true,      // Highlight all points in the same series (e.g., selecting a point in a line chart highlights the entire line), default true
      state: {
        // Custom styles for highlighted/unhighlighted states
        selected: {
          lineWidth: 2,
          opacity: 1,
        },
        unselected: {
          opacity: 0.2,
        },
      },
    },
  },
});
```

## X/Y Simultaneous Box Selection (Freehand Selection)

```javascript
// For freehand selection (simultaneously restricting X and Y), use brushHighlight
chart.options({
  interaction: {
    brushHighlight: true,    // Freehand rectangle selection highlight
  },
});
```

## Common Errors and Fixes

### Error: Confusing Highlighting with Filtering
```javascript
// ❌ Mistakenly thinking brushXHighlight will filter out unselected data
// brushXHighlight only changes opacity, all data remains visible

// ✅ If you need to filter data (unselected regions removed from the chart), use:
chart.options({
  interaction: { brushXFilter: true },   // Filter mode, unselected data disappears
});

// ✅ If you only need to highlight without filtering, use:
chart.options({
  interaction: { brushXHighlight: true },   // Highlight mode, unselected data fades out
});
```