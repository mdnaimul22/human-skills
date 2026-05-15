---
id: "g2-coord-theta"
title: "G2 Theta Coordinate System (Pie Chart / Donut Chart)"
description: |
  The Theta coordinate system is a dedicated coordinate system in G2 v5 for creating pie charts and donut charts.
  Essentially, it is a combination of Transpose + Polar: mapping the y channel (numeric value) to the angle.
  It must be used in conjunction with the stackY transform, otherwise all sector angles will start from 0 and completely overlap.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "theta"
  - "pie chart"
  - "donut chart"
  - "pie"
  - "donut"
  - "coordinate"

related:
  - "g2-transform-stacky"
  - "g2-mark-arc-pie"
  - "g2-mark-arc-donut"
  - "g2-coord-polar"

use_cases:
  - "Pie Chart (displaying the proportion of each part to the whole)"
  - "Donut Chart (leaving the center empty to display aggregated values)"
  - "Rose Pie Chart"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/theta"
---

## Minimum Viable Example (Pie Chart)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 480, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { type: 'Electronics', value: 40 },
    { type: 'Clothing',    value: 25 },
    { type: 'Food',        value: 20 },
    { type: 'Others',      value: 15 },
  ],
  encode: {
    y: 'value',      // Value maps to sector angle size
    color: 'type',   // Color distinguishes categories
  },
  transform: [{ type: 'stackY' }],       // Required! Accumulates values into angle ranges
  coordinate: { type: 'theta' },         // Required! Theta coordinate system
});

chart.render();
```

## Ring Chart (Setting innerRadius)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: {
    type: 'theta',
    innerRadius: 0.6,   // Inner radius ratio (0.5~0.7 are common values)
    outerRadius: 0.9,
  },
  labels: [
    {
      position: 'outside',
      text: (d) => `${d.type}: ${d.value}`,
    },
  ],
});
```

## Configuration Options

```javascript
coordinate: {
  type: 'theta',
  startAngle: -Math.PI / 2,    // Start angle, default -π/2 (12 o'clock direction)
  endAngle: (Math.PI * 3) / 2, // End angle, default clockwise full circle
  innerRadius: 0,              // Inner radius, 0 = solid pie chart, > 0 = donut chart
  outerRadius: 1,              // Outer radius ratio
}
```

## Pie Chart with Percentage Labels

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
  labels: [
    {
      position: 'outside',
      text: (d, i, arr) => {
        const total = arr.reduce((sum, item) => sum + item.value, 0);
        return `${((d.value / total) * 100).toFixed(1)}%`;
      },
    },
  ],
  legend: { color: { position: 'right' } },
});
```

## Common Errors and Fixes

### Error 1: Forgetting stackY —— All sectors start from 0 and completely overlap
```javascript
// ❌ Error: Without stackY, all sector angles start from 0, causing the chart to completely overlap
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  coordinate: { type: 'theta' },   // ❌ Missing transform!
});

// ✅ Correct: Must add stackY
chart.options({
  transform: [{ type: 'stackY' }],  // ✅ Accumulate angles first
  coordinate: { type: 'theta' },
});
```

### Error 2: Using polar instead of theta for pie charts
```javascript
// ❌ Incorrect: The polar coordinate system maps the y channel to the radius, which does not generate sector angles
chart.options({
  coordinate: { type: 'polar' },  // ❌ Results in a rose chart, not a pie chart
});

// ✅ Pie charts must use theta
chart.options({
  coordinate: { type: 'theta' },  // ✅
});
```

### Error 3: Setting the x Channel in encode
```javascript
// ❌ Incorrect: Pie charts in theta coordinates do not require the x channel
chart.options({
  encode: {
    x: 'type',    // ❌ Redundant, the x channel is meaningless in theta coordinates
    y: 'value',
    color: 'type',
  },
});

// ✅ Correct: Theta pie charts only require y and color
chart.options({
  encode: {
    y: 'value',    // ✅ Value → Angle
    color: 'type', // ✅ Category → Color
  },
});
```