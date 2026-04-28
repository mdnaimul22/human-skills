---
id: "g2-mark-range-rangey"
title: "G2 range / rangeX / rangeY Area Annotation"
description: |
  range, rangeX, and rangeY are Marks in G2 v5 used for drawing rectangular area annotations.
  rangeX annotates intervals along the X-axis (vertical rectangular bands), commonly used to highlight time periods;
  rangeY annotates intervals along the Y-axis (horizontal rectangular bands), commonly used to highlight numerical ranges;
  range annotates rectangular areas in both X and Y directions simultaneously.
  Often used in conjunction with other Marks as background area annotations.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "range"
  - "rangeX"
  - "rangeY"
  - "area annotation"
  - "highlight interval"
  - "background band"
  - "annotation"

related:
  - "g2-mark-linex-liney"
  - "g2-mark-connector"
  - "g2-comp-annotation"

use_cases:
  - "Highlighting specific time periods (e.g., promotional periods) on a line chart"
  - "Annotating upper and lower limit intervals of a normal range"
  - "Highlighting a reference area in a comparison chart"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/extra-topics/annotation#rangex"
---

## Comparison of Three Range Marks

| Mark | Data Format | Encode | Usage |
|------|-------------|--------|-------|
| `rangeX` | `[{ start: v1, end: v2 }]` | `x: 'start', x1: 'end'` | X-axis range (vertical band) **commonly used** |
| `rangeY` | `[{ min: v1, max: v2 }]` | `y: 'min', y1: 'max'` | Y-axis range (horizontal band) **commonly used** |
| `range` | `[{ x: [v1,v2], y: [v1,v2] }]` | `x: 'x', y: 'y'` | Two-dimensional rectangle, x/y fields as arrays **rarely used** |

> **Selection Principle**: Highlight only the time period in the X direction → `rangeX`; Highlight only the value range in the Y direction → `rangeY`; Need to define a rectangular area for both X and Y → `range`

## RangeX Highlight Time Period

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'view',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value' },
  children: [
    // Main line chart
    { type: 'line' },
    // X-axis range annotation (highlight promotion period)
    {
      type: 'rangeX',
      data: [
        { start: '2024-11-01', end: '2024-11-30', label: 'Double Eleven' },
      ],
      encode: {
        x: 'start',    // Range start
        x1: 'end',     // Range end
      },
      style: {
        fill: '#ff4d4f',
        fillOpacity: 0.1,
      },
    },
  ],
});

chart.render();
```

## RangeY Annotation for Value Range

```javascript
chart.options({
  type: 'view',
  data,
  encode: { x: 'date', y: 'value' },
  children: [
    { type: 'line' },
    // Y-axis range annotation (normal range)
    {
      type: 'rangeY',
      data: [{ min: 60, max: 100, label: 'Normal Range' }],
      encode: {
        y: 'min',    // Lower bound of the range
        y1: 'max',   // Upper bound of the range
      },
      style: {
        fill: '#52c41a',
        fillOpacity: 0.08,
        stroke: '#52c41a',
        strokeOpacity: 0.3,
        lineWidth: 1,
        lineDash: [4, 4],
      },
    },
  ],
});
```

## Range 2D Rectangular Area

> ⚠️ **`range` data format is completely different from `rangeX`/`rangeY`**: The `x` and `y` fields themselves are `[start, end]` arrays, and the encode only needs `x` and `y`, **no need** for `x1`/`y1`.

```javascript
// Scatter plot with four-quadrant background color (limiting both X and Y directions)
chart.options({
  type: 'view',
  children: [
    {
      type: 'point',
      data: scatterData,
      encode: { x: 'changeX', y: 'changeY' },
    },
    {
      type: 'range',
      // ✅ The values of the x and y fields are [start, end] arrays
      data: [
        { x: [-25, 0], y: [-30, 0], region: 'Q3' },
        { x: [-25, 0], y: [0, 20],  region: 'Q2' },
        { x: [0, 5],   y: [-30, 0], region: 'Q4' },
        { x: [0, 5],   y: [0, 20],  region: 'Q1' },
      ],
      encode: { x: 'x', y: 'y', color: 'region' },  // ✅ encode only needs x and y
      style: { fillOpacity: 0.15 },
    },
  ],
});
```

## Pairing with lineX/lineY for Threshold Annotation

```javascript
// rangeY annotation background area + lineY specific threshold line
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'date', y: 'value' } },
    // Danger zone background
    {
      type: 'rangeY',
      data: [{ min: 80, max: 100 }],
      encode: { y: 'min', y1: 'max' },
      style: { fill: '#ff4d4f', fillOpacity: 0.08 },
    },
    // Threshold line
    {
      type: 'lineY',
      data: [{ y: 80 }],
      encode: { y: 'y' },
      style: { stroke: '#ff4d4f', lineWidth: 1, lineDash: [4, 4] },
    },
  ],
});
```

## Common Errors and Fixes

### ❌ Error: Using Non-existent `regionX` / `regionY` Types
```javascript
// ❌ Error: `regionX` and `regionY` are concepts from other libraries and do not exist in G2
chart.options({ type: 'regionX', ... });
chart.options({ type: 'regionY', ... });

// ✅ Correct: In G2, use `rangeX` / `rangeY`
chart.options({ type: 'rangeX', encode: { x: 'start', x1: 'end' } });
chart.options({ type: 'rangeY', encode: { y: 'start', y1: 'end' } });
```

### ❌ Error: Using x1/y1 fields in range (confusing with rangeX/rangeY syntax)

```javascript
// ❌ Error: range does not use x1/y1; x and y fields are already [start, end] arrays
chart.options({
  type: 'range',
  data: [{ x0: 20, x1: 40, y0: 50, y1: 80 }],
  encode: { x: 'x0', x1: 'x1', y: 'y0', y1: 'y1' },  // ❌
});

// ✅ Correct: x/y field values are arrays
chart.options({
  type: 'range',
  data: [{ x: [20, 40], y: [50, 80] }],
  encode: { x: 'x', y: 'y' },  // ✅
});

// 💡 In most cases, use rangeX or rangeY instead of range:
// - Highlight only X direction → rangeX (encode: { x: 'start', x1: 'end' })
// - Highlight only Y direction → rangeY (encode: { y: 'min', y1: 'max' })
```

### ❌ Error: Omitting `encode` (Most Common, Causes Region Not to Render)

`rangeY` / `rangeX` must explicitly include `encode`. G2 cannot automatically infer the start and end of the range from the field names.

```javascript
// ❌ Error: Missing `encode`, region will not render
{
  type: 'rangeY',
  data: [{ y: 54, y1: 72 }],
  style: { fill: '#FF0000', fillOpacity: 0.1 },
  // ❌ No `encode`!
}

// ✅ Correct: Must include `encode` to explicitly map field names
{
  type: 'rangeY',
  data: [{ y: 54, y1: 72 }],
  encode: { y: 'y', y1: 'y1' },         // ✅ Tell G2 which fields are the start and end
  style: { fill: '#FF0000', fillOpacity: 0.1 },
}

// ✅ Field names can be arbitrary, key is to map them in `encode`
{
  type: 'rangeY',
  data: [{ lower: 54, upper: 72 }],
  encode: { y: 'lower', y1: 'upper' },   // ✅ Field names just need to match `data`
  style: { fill: '#FF0000', fillOpacity: 0.1 },
}
```

### ❌ Error: rangeX only specifies `x` without `x1`
```javascript
// ❌ Error: rangeX requires two encode fields: `x` (start) and `x1` (end)
chart.options({
  type: 'rangeX',
  data: [{ start: 10, end: 20 }],
  encode: { x: 'start' },   // ❌ Missing `x1`
});

// ✅ Correct
chart.options({
  type: 'rangeX',
  data: [{ start: 10, end: 20 }],
  encode: { x: 'start', x1: 'end' },  // ✅ Both `x` and `x1` are required
});
```