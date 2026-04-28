---
id: "g2-mark-funnel"
title: "G2 Funnel Chart (funnel)"
description: |
  The funnel chart uses the interval mark with shape: 'funnel' or 'pyramid' to
  display the flow and conversion rate of data at different stages in a business process.
  It must be used in conjunction with the symmetryY transform and transpose coordinate.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "funnel chart"
  - "funnel"
  - "pyramid"
  - "conversion rate"
  - "process"
  - "symmetryY"

related:
  - "g2-mark-interval-basic"
  - "g2-transform-symmetryy"
  - "g2-coord-transpose"

use_cases:
  - "Sales process conversion rate analysis"
  - "User registration/purchase funnel"
  - "Pyramid hierarchical structure display"
  - "Dual funnel comparison (comparison of two channels)"

anti_patterns:
  - "Unordered data is not suitable for funnel charts"
  - "Processes with increasing and decreasing values are not suitable"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/funnel"
---

## Core Concepts

**Funnel Chart = interval mark + shape: 'funnel' + symmetryY transform + transpose coordinate**

- `encode.shape: 'funnel'`：Enable funnel shape
- `transform: [{ type: 'symmetryY' }]`：Make the funnel symmetric ( **required** )
- `coordinate: { transform: [{ type: 'transpose' }] }`：Display horizontally (recommended)
- `axis: false`：Funnel charts typically hide axes

**Pyramid Variant**：`shape: 'pyramid'` + `style: { reverse: true }`

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'interval',
  data: [
    { stage: 'Visit', value: 8043 },
    { stage: 'Inquiry', value: 2136 },
    { stage: 'Quotation', value: 908 },
    { stage: 'Negotiation', value: 691 },
    { stage: 'Deal', value: 527 },
  ],
  encode: {
    x: 'stage',
    y: 'value',
    color: 'stage',
    shape: 'funnel',
  },
  coordinate: { transform: [{ type: 'transpose' }] },
  transform: [{ type: 'symmetryY' }],
  scale: {
    color: { palette: 'spectral' },
  },
  animate: { enter: { type: 'fadeIn' } },
  axis: false,
  labels: [
    {
      text: (d) => `${d.stage}\n${d.value}`,
      position: 'inside',
      transform: [{ type: 'contrastReverse' }],
    },
  ],
  legend: false,
});

chart.render();
```

## Pyramid Chart

```javascript
chart.options({
  type: 'interval',
  data: [
    { text: 'Top', value: 5 },
    { text: 'Upper Middle', value: 10 },
    { text: 'Middle', value: 20 },
    { text: 'Lower Middle', value: 25 },
    { text: 'Bottom', value: 40 },
  ],
  encode: {
    x: 'text',
    y: 'value',
    color: 'text',
    shape: 'pyramid',   // Pyramid shape
  },
  coordinate: { transform: [{ type: 'transpose' }] },
  transform: [{ type: 'symmetryY' }],
  style: {
    reverse: true,    // Reverse, placing smaller values at the top (pyramid shape)
  },
  scale: {
    x: { paddingOuter: 0, paddingInner: 0 },
    color: { type: 'ordinal' },
  },
  axis: false,
  labels: [
    { text: (d) => d.text, position: 'inside' },
    { text: (d) => `${d.value}%`, position: 'inside', style: { dy: 15 } },
  ],
});
```

## Comparative Funnel Chart (Dual Funnel)

Two funnels are mirrored for comparison, with the lower funnel displayed in reverse using negative y-axis values:

```javascript
chart.options({
  type: 'view',
  autoFit: true,
  data: [
    { action: 'Visit', visitor: 500, site: 'Site1' },
    { action: 'Browse', visitor: 400, site: 'Site1' },
    { action: 'Interact', visitor: 300, site: 'Site1' },
    { action: 'Order', visitor: 200, site: 'Site1' },
    { action: 'Complete', visitor: 100, site: 'Site1' },
    { action: 'Visit', visitor: 550, site: 'Site2' },
    { action: 'Browse', visitor: 420, site: 'Site2' },
    { action: 'Interact', visitor: 280, site: 'Site2' },
    { action: 'Order', visitor: 150, site: 'Site2' },
    { action: 'Complete', visitor: 80, site: 'Site2' },
  ],
  scale: {
    x: { padding: 0 },
    color: { range: ['#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#BAE7FF'] },
  },
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: false,
  children: [
    {
      type: 'interval',
      data: {
        transform: [{ type: 'filter', callback: (d) => d.site === 'Site1' }],
      },
      encode: { x: 'action', y: 'visitor', color: 'action', shape: 'funnel' },
      style: { stroke: '#FFF' },
      animate: { enter: { type: 'fadeIn' } },
      labels: [
        {
          text: 'visitor',
          position: 'inside',
          transform: [{ type: 'contrastReverse' }],
        },
        { text: 'action', position: 'right' },
      ],
    },
    {
      type: 'interval',
      data: {
        transform: [{ type: 'filter', callback: (d) => d.site === 'Site2' }],
      },
      encode: {
        x: 'action',
        y: (d) => -d.visitor,  // Negative value for mirrored symmetry
        color: 'action',
        shape: 'funnel',
      },
      style: { stroke: '#FFF' },
      animate: { enter: { type: 'fadeIn' } },
      labels: [
        {
          text: 'visitor',
          position: 'inside',
          transform: [{ type: 'contrastReverse' }],
        },
      ],
    },
  ],
  legend: false,
});
```

## Percentage Funnel + Conversion Rate Annotation

`normalizeY` makes the height of each stage proportional, and `symmetryY` makes it symmetrical——**the order cannot be reversed**:

```javascript
const data = [
  { stage: 'Visit', count: 10000 },
  { stage: 'Register', count: 6200 },
  { stage: 'Activate', count: 3800 },
  { stage: 'Pay', count: 1500 },
];

const dataWithRate = data.map((d, i) => ({
  ...d,
  rate: i === 0 ? '100%' : `${((d.count / data[i - 1].count) * 100).toFixed(1)}%`,
}));

chart.options({
  type: 'interval',
  data: dataWithRate,
  encode: {
    x: 'stage',
    y: 'count',
    color: 'stage',
    shape: 'funnel',
  },
  transform: [
    { type: 'normalizeY' },   // ① Normalize first (unify height proportions)
    { type: 'symmetryY' },    // ② Symmetrize next (form funnel shape)
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: false,
  legend: false,
  labels: [
    {
      text: (d) => d.stage,
      position: 'inside',
      style: { fill: 'white', fontSize: 13, fontWeight: 'bold' },
    },
    {
      text: (d) => `Conversion Rate ${d.rate}`,
      position: 'right',
      style: { fill: '#666', fontSize: 11 },
      dx: 8,
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Missing symmetryY transform

```javascript
// ❌ Error: Without symmetryY, the funnel shape becomes asymmetrical and turns into a regular bar chart
chart.options({
  type: 'interval',
  data,
  encode: { x: 'stage', y: 'value', shape: 'funnel' },
  coordinate: { transform: [{ type: 'transpose' }] },
  // ❌ Missing transform: [{ type: 'symmetryY' }]
});

// ✅ Correct: Must add symmetryY
chart.options({
  type: 'interval',
  data,
  encode: { x: 'stage', y: 'value', shape: 'funnel' },
  coordinate: { transform: [{ type: 'transpose' }] },
  transform: [{ type: 'symmetryY' }],  // ✅ Required
});
```

### Error 2: Incorrect `shape` Value

```javascript
// ❌ Incorrect: `shape` should be in `encode`, not `style`
chart.options({
  type: 'interval',
  encode: { x: 'stage', y: 'value' },
  style: { shape: 'funnel' },  // ❌ `shape` does not belong in `style`
});

// ✅ Correct: `shape` is an encode channel
chart.options({
  type: 'interval',
  encode: { x: 'stage', y: 'value', shape: 'funnel' },  // ✅
});
```

### Error 3: Incorrect `coordinate` Syntax

```javascript
// ❌ Incorrect: `coordinate` is not an array
chart.options({
  coordinate: [{ type: 'transpose' }],  // ❌ Incorrect syntax
});

// ✅ Correct: `coordinate` is an object, `transpose` is placed in the `transform` array
chart.options({
  coordinate: { transform: [{ type: 'transpose' }] },  // ✅
});
```

### Error 4: Pyramid Not Inverted

```javascript
// ❌ Incorrect: Pyramid defaults to wide end at the top (not a pyramid shape)
chart.options({
  encode: { shape: 'pyramid' },
  // ❌ Missing style.reverse: true
});

// ✅ Correct: Add reverse: true to place smaller values at the top
chart.options({
  encode: { shape: 'pyramid' },
  style: { reverse: true },  // ✅ Places the smallest value at the top (pyramid shape)
});
```

## encode.shape Optional Values

| shape Value | Effect                     |
|-------------|----------------------------|
| `'funnel'`  | Standard funnel shape (default trapezoid) |
| `'pyramid'` | Isosceles triangle (pyramid) |