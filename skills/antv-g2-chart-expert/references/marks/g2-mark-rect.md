---
id: "g2-mark-rect"
title: "G2 Rectangle Mark (rect)"
description: |
  The rect mark draws rectangles of arbitrary position and size in a chart,
  using x/x1 to specify the left and right boundaries, and y/y1 to specify the top and bottom boundaries (consistent with the coordinate axis units).
  Commonly used for highlighting specific data ranges, background partitioning, and annotating regions.
  Similar to rangeX but more versatile (supports specifying boundaries in both x and y directions simultaneously).

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "rect"
  - "rectangle"
  - "region annotation"
  - "background partitioning"
  - "annotation"

related:
  - "g2-mark-rangex"
  - "g2-comp-annotation"
  - "g2-mark-linex-liney"

use_cases:
  - "Highlighting specific x/y ranges in a chart"
  - "Annotating a rectangular region in a scatter plot for a specific value range"
  - "Partitioning background coloring"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/annotation/range/"
---

## Minimum Viable Example (2D Interval Annotation)

```javascript
import { Chart } from '@antv/g2';

const scatterData = Array.from({ length: 100 }, () => ({
  x: Math.random() * 100,
  y: Math.random() * 100,
}));

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'view',
  children: [
    // Main scatter plot
    {
      type: 'point',
      data: scatterData,
      encode: { x: 'x', y: 'y' },
      style: { r: 3, fillOpacity: 0.6 },
    },
    // Rectangle annotation: Highlight the interval x: 30~70, y: 30~70
    {
      type: 'rect',
      data: [{ x: 30, x1: 70, y: 30, y1: 70, label: 'Target Interval' }],
      encode: { x: 'x', x1: 'x1', y: 'y', y1: 'y1' },
      style: {
        fill: '#52c41a',
        fillOpacity: 0.1,
        stroke: '#52c41a',
        lineWidth: 1.5,
        lineDash: [4, 4],
      },
      labels: [
        { text: 'label', position: 'top-left', style: { fill: '#52c41a', fontSize: 11 } },
      ],
    },
  ],
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'rect',
  data: [{ x: 20, x1: 60, y: 0, y1: 100, label: 'Range A' }],
  encode: {
    x: 'x',     // Left boundary of the rectangle (same unit as the x-axis)
    x1: 'x1',   // Right boundary of the rectangle
    y: 'y',     // Bottom boundary of the rectangle (same unit as the y-axis)
    y1: 'y1',   // Top boundary of the rectangle
  },
  style: {
    fill: '#5B8FF9',
    fillOpacity: 0.1,
    stroke: '#5B8FF9',
    lineWidth: 1,
  },
});
```

## Common Errors and Fixes

### Error: Confusion between rect and rangeX/rangeY - rect requires specifying both x and y directions
```javascript
// rangeX: Only specifies the x-direction boundary, y-direction fills the entire chart height
chart.options({ type: 'rangeX', encode: { x: 'start', x1: 'end' } });

// rangeY: Only specifies the y-direction boundary, x-direction fills the entire chart width
chart.options({ type: 'rangeY', encode: { y: 'min', y1: 'max' } });

// rect: Specifies both x and y directions simultaneously (complete rectangular range)
chart.options({ type: 'rect', encode: { x: 'x', x1: 'x1', y: 'y', y1: 'y1' } });
```