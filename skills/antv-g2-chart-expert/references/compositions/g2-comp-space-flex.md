---
id: "g2-comp-space-flex"
title: "G2 Flexible Layout (spaceFlex)"
description: |
  spaceFlex arranges multiple sub-charts in a row (row) or column (col) direction according to a flexible ratio.
  Similar to CSS flexbox, the size of each sub-chart is allocated proportionally based on the ratio array.
  It is suitable for creating layouts with multiple charts of unequal widths side by side, offering more flexibility than repeatMatrix.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "spaceFlex"
  - "flexible layout"
  - "multiple charts"
  - "flex"
  - "side by side"
  - "composition"

related:
  - "g2-comp-space-layer"
  - "g2-comp-facet-rect"
  - "g2-comp-repeat-matrix"

use_cases:
  - "Dual-chart layout with a wider left chart and narrower right chart (e.g., 2:1 ratio)"
  - "Equal division of multiple charts (e.g., 3 equally wide charts)"
  - "Side-by-side display of multiple charts with unequal widths"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/space-flex"
---

## Minimum Viable Example (Left-Right 2:1 Layout)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 900, height: 400 });

chart.options({
  type: 'spaceFlex',
  width: 900,
  height: 400,
  direction: 'row',      // 'row' (horizontal) or 'col' (vertical)
  ratio: [2, 1],         // Left chart takes 2/3, right chart takes 1/3
  padding: 20,           // Spacing between sub-charts
  children: [
    // Left chart: Line chart (takes 2/3 width)
    {
      type: 'line',
      data: salesData,
      encode: { x: 'month', y: 'value', color: 'city' },
      title: 'Monthly Sales Trend',
    },
    // Right chart: Pie chart (takes 1/3 width)
    {
      type: 'interval',
      data: categoryData,
      encode: { y: 'value', color: 'type' },
      transform: [{ type: 'stackY' }],
      coordinate: { type: 'theta', outerRadius: 0.85 },
      title: 'Category Proportion',
    },
  ],
});

chart.render();
```

## Vertical Layout (Top Large, Bottom Small)

```javascript
chart.options({
  type: 'spaceFlex',
  width: 640,
  height: 700,
  direction: 'col',      // Vertical arrangement
  ratio: [3, 1],         // Top chart occupies 3/4 height, bottom chart occupies 1/4
  children: [
    {
      type: 'line',
      data: timeData,
      encode: { x: 'date', y: 'value', color: 'type' },
    },
    // Thumbnail axis chart (bottom small chart)
    {
      type: 'line',
      data: timeData,
      encode: { x: 'date', y: 'value', color: 'type' },
      style: { lineWidth: 1 },
      axis: { y: false },
    },
  ],
});
```

## Equal-width Three Charts Side by Side

```javascript
chart.options({
  type: 'spaceFlex',
  direction: 'row',
  ratio: [1, 1, 1],   // Equal width for three charts
  children: [chart1Config, chart2Config, chart3Config],
});
```

## Common Errors and Fixes

### Error: Inconsistent Length of `ratio` Array with `children`
```javascript
// ❌ Error: 3 child charts but `ratio` only has 2 values
chart.options({
  type: 'spaceFlex',
  ratio: [2, 1],       // ❌ Only 2 ratio values
  children: [c1, c2, c3],  // 3 child charts
});

// ✅ The length of the `ratio` array must match the length of the `children` array
chart.options({
  ratio: [2, 1, 1],   // ✅ 3 ratio values corresponding to 3 child charts
  children: [c1, c2, c3],
});
```

### Error: Subplot width and height not set - spaceFlex automatically calculates, no need to set for subplots individually
```javascript
// ⚠️  Setting width/height for subplots individually will override spaceFlex's automatic layout
children: [
  { type: 'line', width: 400, height: 300, ... },  // ⚠️  Do not set individually
]

// ✅ Subplots only set content, width and height are automatically allocated by parent spaceFlex based on ratio
children: [
  { type: 'line', data: ..., encode: { ... } },  // ✅ Do not set width and height
]
```