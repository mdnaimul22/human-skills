---
id: "g2-mark-arc-pie"
title: "G2 Pie Chart (Interval + theta Coordinate System)"
description: |
  Create a pie chart using Interval Mark with the theta coordinate system and stackY transform,
  to display the proportion of each part in the whole. This article uses the Spec mode (chart.options({})).

library: "g2"
version: "5.x"
category: "marks"
subcategory: "arc"
tags:
  - "pie chart"
  - "proportion"
  - "theta coordinate system"
  - "stackY"
  - "spec"

related:
  - "g2-mark-arc-donut"
  - "g2-core-chart-init"
  - "g2-transform-stacky"
  - "g2-interaction-tooltip"

use_cases:
  - "Display the proportion of each category to the total"
  - "Show market share distribution"
  - "Visualize resource allocation proportions"

anti_patterns:
  - "Pie charts are difficult to read when there are more than 6-7 categories, use bar charts instead"
  - "Not suitable for precise numerical comparisons (human eyes are inaccurate at judging angles)"
  - "Pie charts are meaningless when there are zero or negative values"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/pie"
---
## Core Concepts

Spec structure for G2 v5 pie chart:
- `coordinate: { type: 'theta' }` — Transforms Cartesian coordinates into circular angle coordinates
- `transform: [{ type: 'stackY' }]` — Accumulates categorical values into angle ranges (**required**)
- `encode.y` — Maps numerical fields (angle size)
- `encode.color` — Maps categorical fields (sector color)

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { type: 'Category One', value: 27 },
    { type: 'Category Two', value: 25 },
    { type: 'Category Three', value: 18 },
    { type: 'Category Four', value: 15 },
    { type: 'Category Five', value: 10 },
    { type: 'Others', value: 5 },
  ],
  encode: {
    y: 'value',       // Maps numerical field (determines sector angle size)
    color: 'type',    // Maps categorical field (determines sector color)
  },
  transform: [{ type: 'stackY' }],   // Required: Converts y values to angle ranges
  coordinate: { type: 'theta', outerRadius: 0.8 },
  legend: {
    color: { position: 'bottom', layout: { justifyContent: 'center' } },
  },
  labels: [
    {
      text: (d) => `${d.type}\n${d.value}`,
      position: 'outside',
      connector: true,
    },
  ],
});

chart.render();
```

## Pie Chart with Percentage Labels

```javascript
import { Chart } from '@antv/g2';

const data = [
  { type: 'Category One', value: 27 },
  { type: 'Category Two', value: 25 },
  { type: 'Category Three', value: 18 },
  { type: 'Category Four', value: 15 },
  { type: 'Other', value: 15 },
];
const total = data.reduce((sum, d) => sum + d.value, 0);

const chart = new Chart({ container: 'container', width: 600, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
  labels: [
    {
      text: (d) => `${((d.value / total) * 100).toFixed(1)}%`,
      position: 'inside',
      style: { fill: 'white', fontSize: 12, fontWeight: 'bold' },
    },
  ],
});

chart.render();
```

## Donut Chart (Donut)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: {
    type: 'theta',
    outerRadius: 0.8,
    innerRadius: 0.5,    // Setting the inner radius creates a donut chart
  },
});
```

## Rose Chart (Polar Coordinate Bar Chart)

```javascript
// In polar coordinates, each sector has the same angle, and the radius is determined by the value
chart.options({
  type: 'interval',
  data,
  encode: { x: 'type', y: 'value', color: 'type' },
  coordinate: { type: 'polar' },   // Note: Use polar for rose charts, not theta
});
```

## Common Errors and Fixes

### Error 1: Forgetting to transform stackY
```javascript
// ❌ Incorrect: Without stackY, all sectors start from angle 0, completely overlapping
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  coordinate: { type: 'theta' },
  // Missing transform!
});

// ✅ Correct: Must declare stackY
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],   // Mandatory!
  coordinate: { type: 'theta' },
});
```

### Error 2: Misuse of x Channel in Pie Charts
```javascript
// ❌ Incorrect: x channel is invalid in theta coordinate system, do not use encode.x in pie charts
chart.options({
  type: 'interval',
  encode: { x: 'type', y: 'value' },    // x has no meaning under theta
  coordinate: { type: 'theta' },
});

// ✅ Correct: Pie charts only require encode.y (numerical) and encode.color (categorical)
chart.options({
  type: 'interval',
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta' },
});
```

### Error 3: Pie Chart Syntax in G2 v4
```javascript
// ❌ Incorrect (G2 v4 Syntax)
chart.coord('theta', { radius: 0.75 });
chart.interval().position('value').color('type');

// ✅ Correct (G2 v5 Spec Syntax)
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
});
```