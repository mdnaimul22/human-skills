---
id: "g2-mark-link"
title: "G2 Link Chart (Line Between Two Points)"
description: |
  The link mark draws a line between two data points, with each record having independent start (x/y) and end (x1/y1) points.
  Unlike the line mark, each record in a link is an independent line segment and does not require grouping by color/series.
  It is suitable for scenarios such as migration, comparison, and ranking changes.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "link"
  - "line connection"
  - "slope chart"
  - "migration chart"
  - "line between two points"

related:
  - "g2-mark-line-basic"
  - "g2-mark-point-scatter"

use_cases:
  - "Slope chart (showing ranking/value changes between two periods)"
  - "Line connection between two categories (migration, association)"
  - "Path display of start and end point data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/link/"
---

## Minimum Viable Example (Slope Chart — Ranking Changes)

```javascript
import { Chart } from '@antv/g2';

// Each record represents the ranking change of a city from 2022 to 2023
const data = [
  { city: 'Beijing', rank2022: 1, rank2023: 2 },
  { city: 'Shanghai', rank2022: 2, rank2023: 1 },
  { city: 'Guangzhou', rank2022: 3, rank2023: 5 },
  { city: 'Shenzhen', rank2022: 4, rank2023: 3 },
  { city: 'Chengdu', rank2022: 5, rank2023: 4 },
];

const chart = new Chart({ container: 'container', width: 400, height: 480 });

chart.options({
  type: 'link',
  data,
  encode: {
    x: ['2022', '2023'],           // Two positions on the x-axis (start/end)
    y: ['rank2022', 'rank2023'],   // Y values at both ends (start/end)
    color: 'city',
  },
  scale: {
    y: { reverse: true },  // Ranking from top to bottom (1 at the top)
  },
  style: {
    lineWidth: 2,
    strokeOpacity: 0.8,
  },
  // Display scatter points at both ends
  labels: [
    { text: (d) => `${d.city} ${d.rank2022}`, position: 'left' },
    { text: (d) => `${d.rank2023}`, position: 'right' },
  ],
});

chart.render();
```

## Arrow Links

```javascript
chart.options({
  type: 'link',
  data,
  encode: {
    x: ['source_x', 'target_x'],
    y: ['source_y', 'target_y'],
    color: 'type',
  },
  style: {
    lineWidth: 1.5,
    // End arrow
    endArrow: true,
    endArrowSize: 8,
  },
});
```

## Common Errors and Fixes

### Error: encode.x/y written as a single field name - link requires an array of [start field, end field]
```javascript
// ❌ Error: x and y are single fields, only one end is bound
chart.options({
  type: 'link',
  encode: {
    x: 'x',    // ❌ Only one position
    y: 'y',    // ❌
  },
});

// ✅ Correct: x and y must be arrays containing two field names
chart.options({
  type: 'link',
  encode: {
    x: ['x0', 'x1'],  // ✅ [start field, end field]
    y: ['y0', 'y1'],  // ✅
  },
});
```

### Error: Using line mark instead of link—Different behavior with multiple data series
```javascript
// ❌ If each record is an independent line segment, using line requires series grouping, which is prone to errors
chart.options({
  type: 'line',
  encode: { x: 'x', y: 'y', color: 'id' },  // color is needed to separate lines
});

// ✅ For scenarios where each record is a single line segment, use link directly
chart.options({
  type: 'link',
  encode: { x: ['x0', 'x1'], y: ['y0', 'y1'] },  // ✅ More intuitive
});
```