---
id: "g2-transform-sort-color"
title: "G2 SortColor Transformation for Grouping and Sorting by Color"
description: |
  sortColor is a sorting Transform in G2 v5 that sorts the domain of the color channel scale.
  Similar to sortX (sorting by the x-axis), but the sorting applies to the categorical order of the color channel.
  Commonly used in scenarios such as legend sorting and adjusting the order of stacked layers.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "sortColor"
  - "color sorting"
  - "legend order"
  - "transform"
  - "sort"
  - "color"

related:
  - "g2-transform-sortx"
  - "g2-transform-sorty"
  - "g2-mark-interval-stacked"

use_cases:
  - "Sorting legend order by numerical value"
  - "Adjusting color layering order in stacked bar charts"
  - "Controlling color assignment order in line chart series"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/sort-color"
---

## Core Concepts

`sortColor` reorders the domain of the color scale by calculating the aggregated value (default: mean of the y channel) for each color group, affecting:
- The display order of the legend
- The stacking order of layers in stacked charts
- The color assignment order

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', type: 'A', value: 50 },
    { month: 'Jan', type: 'B', value: 80 },
    { month: 'Jan', type: 'C', value: 30 },
    { month: 'Feb', type: 'A', value: 60 },
    { month: 'Feb', type: 'B', value: 70 },
    { month: 'Feb', type: 'C', value: 40 },
  ],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    { type: 'stackY' },
    { type: 'sortColor', channel: 'y', order: 'descending' },  // Sort colors by y-axis mean in descending order
  ],
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  transform: [
    {
      type: 'sortColor',
      channel: 'y',           // Channel used for sorting calculation, default 'y'
      order: 'ascending',     // 'ascending' (ascending order) | 'descending' (descending order), default 'ascending'
      reducer: 'mean',        // Aggregation method: 'mean' | 'sum' | 'max' | 'min' | function, default 'mean'
      reverse: false,         // Whether to reverse the sorting result
    },
  ],
});
```

## Comparison with sortX

```javascript
// sortX: Sorts the order of categories on the x-axis (affects the x-axis position order of bars/points)
transform: [{ type: 'sortX', channel: 'y', order: 'descending' }]

// sortColor: Sorts color groups (legend/stacking layers) (does not affect x-axis order)
transform: [{ type: 'sortColor', channel: 'y', order: 'descending' }]
```

## Common Errors and Fixes

### Error: Expected to change column position but used sortColor
```javascript
// ❌ Error: sortColor only changes the color/legend order, not the x-axis column position
chart.options({
  encode: { x: 'type', y: 'value' },
  transform: [{ type: 'sortColor', channel: 'y', order: 'descending' }],
  // The x-axis column order remains unchanged!
});

// ✅ To change the x-axis column position, use sortX
chart.options({
  encode: { x: 'type', y: 'value' },
  transform: [{ type: 'sortX', channel: 'y', order: 'descending' }],  // ✅
});
```