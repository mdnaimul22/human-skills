---
id: "g2-mark-path"
title: "G2 Path Mark"
description: |
  The path mark renders arbitrary shapes using SVG path strings (d attribute),
  suitable for custom graphics, map contours, flowchart arrows, and other shapes that cannot be expressed using standard marks.
  Difference from line mark: line connects data point coordinates, while path directly uses SVG d path strings.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "path"
  - "path"
  - "SVG"
  - "custom shapes"
  - "annotation"

related:
  - "g2-mark-polygon"
  - "g2-mark-link"
  - "g2-mark-connector"

use_cases:
  - "Rendering custom SVG path shapes"
  - "Map contour (non-GeoJSON) annotations"
  - "Custom arrows and flowchart elements"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/path"
---
## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

// path mark provides SVG path string through the 'd' field
const pathData = [
  {
    d: 'M 100 200 C 100 100 400 100 400 200 S 700 300 700 200',
    color: '#5B8FF9',
    label: 'Curved Path',
  },
  {
    d: 'M 100 350 L 250 300 L 400 350 L 550 300 L 700 350',
    color: '#FF6B6B',
    label: 'Broken Path',
  },
];

chart.options({
  type: 'view',
  width: 640,
  height: 480,
  children: [
    {
      type: 'path',
      data: pathData,
      encode: {
        d: 'd',          // SVG path string field
        color: 'color',
      },
      style: {
        lineWidth: 2,
        fillOpacity: 0,  // Paths typically only display strokes
      },
    },
  ],
});

chart.render();
```

## Closed Paths with Fill

```javascript
// Closed paths (Z command) can be filled with color
const shapes = [
  {
    d: 'M 200 100 L 300 300 L 100 300 Z',  // Triangle
    category: 'triangle',
  },
  {
    d: 'M 450 100 L 550 150 L 550 250 L 450 300 L 350 250 L 350 150 Z',  // Hexagon
    category: 'hexagon',
  },
];

chart.options({
  type: 'path',
  data: shapes,
  encode: {
    d: 'd',
    color: 'category',
  },
  style: {
    fillOpacity: 0.3,
    lineWidth: 2,
  },
});
```

## Common Errors and Fixes

### Error: Path Mark Uses x/y Encode - Path Does Not Support Coordinate Encoding
```javascript
// ❌ Path mark does not use x/y, but uses d (SVG path string)
chart.options({
  type: 'path',
  encode: { x: 'x', y: 'y' },  // ❌ Path mark does not support coordinate encoding
});

// ✅ Path mark uses the d field to provide a complete SVG path
chart.options({
  type: 'path',
  encode: { d: 'd' },           // ✅ d field is the SVG path string
  style: { lineWidth: 2 },
});
```

### Error: Confusing path with line - Connecting data points using line
```javascript
// Connect multiple data coordinate points → use line mark
chart.options({ type: 'line', encode: { x: 'date', y: 'value' } });

// Customize SVG path shape → use path mark
chart.options({ type: 'path', encode: { d: 'pathString' } });
```