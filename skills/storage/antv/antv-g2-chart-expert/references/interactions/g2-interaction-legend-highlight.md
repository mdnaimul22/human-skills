---
id: "g2-interaction-legend-highlight"
title: "G2 Legend Highlight (legendHighlight)"
description: |
  The legendHighlight interaction allows users to hover over legend items, highlighting the corresponding group elements in the chart,
  while other group elements become semi-transparent (inactive state).
  Difference from legendFilter: legendHighlight only changes the visual state without filtering data;
  legendFilter actually hides data items upon clicking.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "legendHighlight"
  - "Legend Highlight"
  - "Interaction"
  - "highlight"
  - "interaction"

related:
  - "g2-interaction-legend-filter"
  - "g2-interaction-element-highlight-by"
  - "g2-comp-legend-config"

use_cases:
  - "Hovering over a legend in a multi-series line chart to highlight a specific series"
  - "Highlighting corresponding groups when hovering over a legend in a grouped bar chart"
  - "Hovering to highlight scatter plots categorized by color"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/legend-highlight"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', city: 'Beijing', value: 5 },
  { month: 'Jan', city: 'Shanghai', value: 12 },
  { month: 'Feb', city: 'Beijing', value: 8 },
  { month: 'Feb', city: 'Shanghai', value: 15 },
  { month: 'Mar', city: 'Beijing', value: 12 },
  { month: 'Mar', city: 'Shanghai', value: 18 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'city' },
  interaction: {
    legendHighlight: true,  // Highlight corresponding series when hovering over legend
  },
});

chart.render();
```

## legendHighlight vs legendFilter Comparison

```javascript
// legendHighlight: Hover over legend → Highlight corresponding elements, others become semi-transparent (data is not hidden)
chart.options({
  interaction: { legendHighlight: true },
});

// legendFilter: Click on legend → Toggle display/hide corresponding data items (data is removed from the chart)
chart.options({
  interaction: { legendFilter: true },
});

// Enable both interactions: Hover highlight + Click filter
chart.options({
  interaction: {
    legendHighlight: true,
    legendFilter: true,
  },
});
```

## Custom Highlight Style

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  state: {
    active: {
      // Active (highlight) state style
      lineWidth: 2,
      stroke: '#000',
    },
    inactive: {
      // Inactive (background) state style
      fillOpacity: 0.2,
      strokeOpacity: 0.2,
    },
  },
  interaction: {
    legendHighlight: true,
  },
});
```

## Common Errors and Fixes

### Error: Highlighting is ineffective when the legend does not have color encoding
```javascript
// ❌ Without color encoding, the legend will not be associated with the elements, and highlighting is ineffective
chart.options({
  type: 'interval',
  encode: { x: 'month', y: 'value' },   // ❌ Missing color encoding
  interaction: { legendHighlight: true },
});

// ✅ Color encoding is required to establish the association between the legend and the elements
chart.options({
  type: 'interval',
  encode: { x: 'month', y: 'value', color: 'city' },  // ✅ With color encoding
  interaction: { legendHighlight: true },
});
```