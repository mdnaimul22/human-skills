---
id: "g2-transform-diffy"
title: "G2 DiffY Difference Area Transform"
description: |
  diffY calculates the difference interval (y0 to y1) between two line charts, used for drawing difference area charts.
  It keeps the y values of the upper line unchanged and calculates the difference of the lower line relative to the upper line as y1,
  visually displaying the positive/negative difference areas between the two series.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "diffY"
  - "difference"
  - "difference area"
  - "comparison"
  - "transform"
  - "interval area"

related:
  - "g2-mark-area-stacked"
  - "g2-transform-stacky"
  - "g2-mark-line-basic"

use_cases:
  - "Displaying positive/negative difference areas between two line charts"
  - "Visualization of deviations between actual and predicted values"
  - "Displaying differences in price ranges"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/diff-y"
---

## Minimum Viable Example (Actual vs Forecast Difference)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', actual: 83,  forecast: 75 },
  { month: 'Feb', actual: 60,  forecast: 70 },
  { month: 'Mar', actual: 95,  forecast: 85 },
  { month: 'Apr', actual: 72,  forecast: 80 },
  { month: 'May', actual: 110, forecast: 100 },
  { month: 'Jun', actual: 88,  forecast: 95 },
];

// Convert to long table format
const longData = data.flatMap(d => [
  { month: d.month, value: d.actual,   type: 'Actual' },
  { month: d.month, value: d.forecast, type: 'Forecast' },
]);

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'view',
  children: [
    // Difference area (Positive difference: Actual > Forecast shows green, Negative difference: Actual < Forecast shows red)
    {
      type: 'area',
      data: longData,
      encode: { x: 'month', y: 'value', color: 'type', series: 'type' },
      transform: [{ type: 'diffY' }],   // Calculate the difference range between the two series
      style: {
        fillOpacity: 0.3,
      },
    },
    // Main line
    {
      type: 'line',
      data: longData,
      encode: { x: 'month', y: 'value', color: 'type' },
      style: { lineWidth: 2 },
    },
  ],
});

chart.render();
```

## Configuration Options

```javascript
transform: [
  {
    type: 'diffY',
    groupBy: 'x',   // Group and align by the 'x' channel, default is 'x'
  },
]
```

## Common Errors and Fixes

### Error: Data does not have two series - diffY requires at least two series to calculate the difference
```javascript
// ❌ Only one series, diffY has no comparison baseline, difference is 0
chart.options({
  type: 'area',
  data: singleSeriesData,
  encode: { x: 'date', y: 'value' },  // ❌ No series/color to distinguish between two groups
  transform: [{ type: 'diffY' }],
});

// ✅ Must have two series (distinguished by color/series)
chart.options({
  type: 'area',
  data: twoSeriesData,
  encode: {
    x: 'date',
    y: 'value',
    color: 'type',   // ✅ Distinguish between two series
    series: 'type',
  },
  transform: [{ type: 'diffY' }],
});
```

### Error: Confusion between diffY and stackY — stackY is cumulative, diffY is the difference
```javascript
// stackY: Accumulates the y values of multiple series (suitable for stacked charts)
transform: [{ type: 'stackY' }]

// diffY: Calculates the difference range between two series (suitable for difference area charts)
transform: [{ type: 'diffY' }]
```