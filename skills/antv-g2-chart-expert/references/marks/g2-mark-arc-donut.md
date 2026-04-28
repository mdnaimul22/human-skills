---
id: "g2-mark-arc-donut"
title: "G2 Donut Chart"
description: |
  Based on the pie chart, a donut chart (ring chart) is created by setting coordinate.innerRadius,
  leaving a blank area in the center where summary numbers or explanatory text can be placed. This reduces visual weight while retaining proportional representation.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "arc"
tags:
  - "donut chart"
  - "donut"
  - "innerRadius"
  - "proportion"
  - "pie chart variant"
  - "spec"

related:
  - "g2-mark-arc-pie"
  - "g2-transform-stacky"

use_cases:
  - "Displaying category proportions with summary data in the center area"
  - "A more modern way to show proportions compared to pie charts"
  - "Proportional rings in KPI cards"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/donut"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 480,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { type: 'Category One', value: 27 },
    { type: 'Category Two', value: 25 },
    { type: 'Category Three', value: 18 },
    { type: 'Category Four', value: 15 },
    { type: 'Others', value: 15 },
  ],
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: {
    type: 'theta',
    outerRadius: 0.8,
    innerRadius: 0.5,    // Key: Set inner radius to create a hollow effect
  },
});

chart.render();
```

## Ring Chart with Center Text

```javascript
import { Chart } from '@antv/g2';

const data = [
  { type: 'Completed', value: 75 },
  { type: 'Uncompleted', value: 25 },
];
const total = data.reduce((s, d) => s + d.value, 0);

const chart = new Chart({ container: 'container', width: 400, height: 400 });

chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      data,
      encode: { y: 'value', color: 'type' },
      transform: [{ type: 'stackY' }],
      coordinate: { type: 'theta', outerRadius: 0.85, innerRadius: 0.6 },
      scale: {
        color: { range: ['#1890ff', '#f0f0f0'] },
      },
      legend: false,
    },
    {
      // Center text is drawn at the polar coordinate center using the text mark
      type: 'text',
      data: [{ value: data[0].value }],
      encode: { text: (d) => `${d.value}%` },
      style: {
        x: '50%', y: '50%',
        textAlign: 'center',
        fontSize: 32,
        fontWeight: 'bold',
        fill: '#1890ff',
      },
    },
  ],
});

chart.render();
```

## Donut Chart with External Labels

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8, innerRadius: 0.5 },
  labels: [
    {
      text: (d) => `${d.type}: ${d.value}`,
      position: 'outside',
      connector: true,
    },
  ],
});
```

## Common Errors and Fixes

### Error: innerRadius is greater than outerRadius
```javascript
// ❌ Error: Inner radius is greater than outer radius, causing the ring to disappear
chart.options({
  coordinate: { type: 'theta', outerRadius: 0.5, innerRadius: 0.8 },
});

// ✅ Correct: innerRadius < outerRadius, recommended ratio 0.5-0.7
chart.options({
  coordinate: { type: 'theta', outerRadius: 0.8, innerRadius: 0.5 },
});
```