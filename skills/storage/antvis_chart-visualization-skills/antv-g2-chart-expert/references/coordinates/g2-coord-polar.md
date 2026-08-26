---
id: "g2-coord-polar"
title: "G2 Polar Coordinate System (polar)"
description: |
  The polar coordinate system maps the Cartesian coordinate system to a circular area, where the x channel is mapped to the angle and the y channel is mapped to the radius.
  It is commonly used in rose charts (polar bar charts), polar area charts, and radial charts.
  The angle range is controlled by startAngle / endAngle, and the size of the inner hole is controlled by innerRadius.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "polar"
  - "polar coordinate"
  - "rose chart"
  - "nightingale"
  - "coxcomb"
  - "radial"
  - "coordinate"

related:
  - "g2-coord-transpose"
  - "g2-mark-arc-pie"
  - "g2-mark-interval-stacked"

use_cases:
  - "Rose Chart / Nightingale Rose Chart (categories encoded by both angle and radius)"
  - "Polar Area Chart (circular display of periodic data)"
  - "Radial Progress Bar"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/polar"
---

## Minimum Viable Example (Rose Chart)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 500, height: 500 });

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', value: 83 },
    { month: 'Feb', value: 60 },
    { month: 'Mar', value: 95 },
    { month: 'Apr', value: 72 },
    { month: 'May', value: 110 },
    { month: 'Jun', value: 88 },
  ],
  encode: {
    x: 'month',   // Maps to angle (direction)
    y: 'value',   // Maps to radius (length)
    color: 'month',
  },
  coordinate: { type: 'polar' },  // Key: Polar coordinate
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'month' },
  coordinate: {
    type: 'polar',
    startAngle: -Math.PI / 2,    // Start angle, default -π/2 (12 o'clock direction)
    endAngle: (Math.PI * 3) / 2, // End angle, default 3π/2 (clockwise full circle)
    innerRadius: 0,              // Inner radius, 0 = no hole, 0.5 = 50% of radius as hole
    outerRadius: 1,              // Outer radius ratio, default 1
  },
});
```

## Semi-Circular Rose Chart

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'month' },
  coordinate: {
    type: 'polar',
    startAngle: -Math.PI / 2,   // Start from the top
    endAngle: Math.PI / 2,      // Only to the bottom, semi-circle
  },
});
```

## Polar Coordinate Stacked Area Chart

```javascript
chart.options({
  type: 'area',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'polar', innerRadius: 0.2 },
  style: { fillOpacity: 0.65 },
});
```

## Common Errors and Fixes

### Error 1: Uneven Angles in Rose Chart — x Channel Data Type is Not Categorical
```javascript
// ❌ Error: x channel is numerical, resulting in uneven angles in polar coordinates
chart.options({
  encode: { x: 'timestamp', y: 'value' },  // ❌ Timestamp is numerical
  coordinate: { type: 'polar' },
});

// ✅ Correct: x channel should be a categorical field (string)
chart.options({
  encode: { x: 'month', y: 'value' },  // ✅ String category
  coordinate: { type: 'polar' },
});
```

### Error 2: Confusion with the theta coordinate system
```javascript
// ❌ Polar is invalid for pie charts — the y channel will not automatically convert to sector angles
chart.options({
  type: 'interval',
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'polar' },  // ❌ Pie charts should use theta, not polar
});

// ✅ Pie charts must use the theta coordinate system
chart.options({
  coordinate: { type: 'theta' },  // ✅
});
```