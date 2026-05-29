---
id: "g2-transform-select"
title: "G2 Select / SelectX / SelectY Filter Transform"
description: |
  The select series of transforms filters specific data rows from grouped data for annotation.
  selectX filters after grouping by the x channel (commonly used for end labels in line charts),
  selectY filters after grouping by the y channel.
  The selector supports preset values such as 'first', 'last', 'min', 'max', or custom functions.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "select"
  - "selectX"
  - "selectY"
  - "filter"
  - "end label"
  - "extreme value annotation"
  - "transform"

related:
  - "g2-mark-line-basic"
  - "g2-mark-text"
  - "g2-comp-annotation"

use_cases:
  - "Display the latest data label at the end of a line chart"
  - "Annotate the maximum or minimum value of each line"
  - "Place annotation labels at specific x positions"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/select"
---

## Minimum Viable Example (Line Chart End Label)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', type: 'A', value: 83 },
  { month: 'Feb', type: 'A', value: 90 },
  { month: 'Mar', type: 'A', value: 76 },
  { month: 'Jan', type: 'B', value: 50 },
  { month: 'Feb', type: 'B', value: 65 },
  { month: 'Mar', type: 'B', value: 72 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

// Main line chart
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data,
      encode: { x: 'month', y: 'value', color: 'type' },
    },
    // End label: text mark + selectX (select the last point of each line)
    {
      type: 'text',
      data,
      encode: { x: 'month', y: 'value', color: 'type', text: 'type' },
      transform: [
        {
          type: 'selectX',
          selector: 'last',   // Select the point with the largest x value in each group (each line)
        },
      ],
      style: { textAnchor: 'start', dx: 6 },
    },
  ],
});

chart.render();
```

## Annotate Maximum Value

```javascript
// Add annotation at the highest point of the line chart
{
  type: 'point',
  data,
  encode: { x: 'date', y: 'value', color: 'type' },
  transform: [
    {
      type: 'selectY',
      selector: 'max',   // Select the point with the maximum y value in each group
    },
  ],
  style: { r: 6, lineWidth: 2 },
  labels: [{ text: (d) => `Max: ${d.value}`, position: 'top' }],
}
```

## selector Quick Reference

```javascript
// Select the last point (commonly used for end labels)
transform: [{ type: 'selectX', selector: 'last' }]

// Select the first point
transform: [{ type: 'selectX', selector: 'first' }]

// Select the point with the maximum y value
transform: [{ type: 'selectY', selector: 'max' }]

// Select the point with the minimum y value
transform: [{ type: 'selectY', selector: 'min' }]

// Custom: Select the Nth point
transform: [{ type: 'selectX', selector: (data) => data[Math.floor(data.length / 2)] }]
```

## Common Errors and Fixes

### Error: select used on the line mark itself—applied to an independent text/point mark
```javascript
// ❌ Using selectX on a line mark, the entire line is reduced to a single point
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },
  transform: [{ type: 'selectX', selector: 'last' }],  // ❌ Turns the line into a single point
});

// ✅ select applied to an additional text or point mark, parallel to the line
chart.options({
  type: 'view',
  children: [
    { type: 'line', data, encode: { x: 'month', y: 'value' } },
    {
      type: 'text',
      data,
      encode: { x: 'month', y: 'value', text: 'value' },
      transform: [{ type: 'selectX', selector: 'last' }],  // ✅ Independent mark
    },
  ],
});
```