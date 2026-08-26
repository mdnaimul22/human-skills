---
id: "g2-transform-symmetryy"
title: "G2 SymmetryY Transform (Butterfly Chart / Population Pyramid)"
description: |
  symmetryY applies an offset to the y channel, making the data symmetric about the y=0 axis.
  Typical applications include population pyramids (symmetric bar charts in two directions) and butterfly charts.
  It is often used in conjunction with the transpose coordinate system to achieve horizontal symmetric bar charts.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "symmetryY"
  - "symmetry"
  - "population pyramid"
  - "butterfly chart"
  - "transform"

related:
  - "g2-transform-stacky"
  - "g2-coord-transpose"
  - "g2-mark-interval-stacked"

use_cases:
  - "Population pyramid (symmetric display of male and female age distribution)"
  - "A/B comparison butterfly chart"
  - "Charts with positive and negative values symmetric about the center"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/symmetry-y"
---

## Minimum Viable Example (Population Pyramid)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { age: '0-9',   gender: 'Male', value: 8500 },
  { age: '10-19', gender: 'Male', value: 9200 },
  { age: '20-29', gender: 'Male', value: 10300 },
  { age: '30-39', gender: 'Male', value: 9800 },
  { age: '40-49', gender: 'Male', value: 8900 },
  { age: '0-9',   gender: 'Female', value: 8100 },
  { age: '10-19', gender: 'Female', value: 8800 },
  { age: '20-29', gender: 'Female', value: 9900 },
  { age: '30-39', gender: 'Female', value: 9500 },
  { age: '40-49', gender: 'Female', value: 8700 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: {
    x: 'age',
    y: 'value',
    color: 'gender',
  },
  transform: [
    { type: 'stackY' },     // Stack first
    { type: 'symmetryY' },  // Then symmetrize (with y=0 as the axis)
  ],
  coordinate: { transform: [{ type: 'transpose' }] },  // Transpose to horizontal bars
  axis: {
    y: {
      labelFormatter: (v) => Math.abs(v).toLocaleString(),  // Display negative values as positive
    },
  },
});

chart.render();
```

## Configuration Options

```javascript
transform: [
  {
    type: 'symmetryY',
    groupBy: 'x',   // Group by which channel, default is 'x'
  },
]
```

## Butterfly Chart (Symmetrical for Two Categories)

```javascript
chart.options({
  type: 'interval',
  data: abTestData,
  encode: { x: 'metric', y: 'value', color: 'group' },
  transform: [
    { type: 'stackY' },
    { type: 'symmetryY' },
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
  style: { fillOpacity: 0.85 },
});
```

## Common Errors and Fixes

### Error: Missing `stackY` before `symmetryY`—Grouped data will not be symmetric
```javascript
// ❌ Without stackY, bars for both genders overlap on the same side, symmetry fails
transform: [
  { type: 'symmetryY' },  // ❌ Missing preceding stackY
]

// ✅ Must apply stackY before symmetryY
transform: [
  { type: 'stackY' },     // ✅ Stack first (group data together)
  { type: 'symmetryY' },  // ✅ Then symmetrize (shift each group to opposite sides)
]
```