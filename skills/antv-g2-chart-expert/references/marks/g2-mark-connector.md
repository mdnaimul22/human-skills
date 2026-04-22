---
id: "g2-mark-connector"
title: "G2 Connector Mark"
description: |
  The connector mark draws a cornered connecting line between two points, used to annotate the association or difference between two data points in a chart.
  It is commonly used to annotate the difference between two bars, the change between two data points, and is often paired with text or labels to display difference annotations.
  Similar to the link mark but more oriented towards annotation purposes, it defaults to a right-angled polyline.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "connector"
  - "annotation"
  - "difference annotation"
  - "polyline connection"

related:
  - "g2-mark-link"
  - "g2-mark-linex-liney"
  - "g2-comp-annotation"

use_cases:
  - "Annotating the difference between two bar chart values"
  - "Connecting two data points and displaying the difference"
  - "Annotating the change amount between start and end points in a line chart"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/annotation/connector/"
---
## Minimum Viable Example (Difference Annotation)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', value: 83 },
  { month: 'Feb', value: 60 },
  { month: 'Mar', value: 95 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'view',
  children: [
    // Main bar chart
    {
      type: 'interval',
      data,
      encode: { x: 'month', y: 'value', color: 'month' },
    },
    // connector: Connects the bars for Jan and Mar, annotating the difference
    {
      type: 'connector',
      data: [{ x: 'Jan', y: 83, x1: 'Mar', y1: 95 }],
      encode: {
        x: 'x',
        y: 'y',
        x1: 'x1',
        y1: 'y1',
      },
      labels: [
        {
          text: '+12',
          position: 'top',
          style: { fill: '#52c41a', fontWeight: 'bold' },
        },
      ],
      style: {
        stroke: '#52c41a',
        lineWidth: 1.5,
        offset: 16,   // Offset of the connector line relative to the data points
      },
    },
  ],
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'connector',
  data: [{ x: 'A', y: 100, x1: 'B', y1: 150 }],
  encode: {
    x: 'x',    // Start point x (corresponds to the main chart's x-axis)
    y: 'y',    // Start point y
    x1: 'x1',  // End point x
    y1: 'y1',  // End point y
  },
  style: {
    stroke: '#999',
    lineWidth: 1,
    offset: 16,         // Pixel offset of the connector line from the data point, default is 16
    endMarker: true,    // Whether to display the end marker
    startMarker: false, // Whether to display the start marker
  },
});
```

## Common Errors and Fixes

### Error: Only x/y are specified in encode, missing x1/y1—connector line has no endpoint
```javascript
// ❌ Error: connector requires both start and end points
chart.options({
  type: 'connector',
  encode: { x: 'x', y: 'y' },   // ❌ Missing x1/y1
});

// ✅ Correct: Both start and end points must be specified
chart.options({
  type: 'connector',
  encode: { x: 'x', y: 'y', x1: 'x1', y1: 'y1' },  // ✅
});
```