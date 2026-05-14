---
id: "g2-mark-polygon"
title: "G2 Polygon Mark"
description: |
  The polygon mark renders arbitrary polygons based on multiple x/y channel coordinates.
  Each record corresponds to one polygon, with coordinates passed through x, x1, x2... and y, y1, y2... channels.
  Commonly used in scenarios such as map area coloring, Voronoi diagrams, and custom shapes.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "polygon"
  - "polygon"
  - "Voronoi"
  - "map"
  - "custom shape"

related:
  - "g2-mark-image"
  - "g2-mark-path"

use_cases:
  - "Voronoi Diagram (Natural Neighbor Partitioning)"
  - "Custom Shape Area Coloring"
  - "Geographic Area Polygon Coloring (Non-Standard Maps)"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/other/#polygon"
---
## Minimum Viable Example (Voronoi Diagram)

```javascript
import { Chart } from '@antv/g2';
import { Delaunay } from 'd3-delaunay';

// Randomly generate points and calculate Voronoi diagram
const points = Array.from({ length: 30 }, () => [
  Math.random() * 600,
  Math.random() * 400,
]);

const delaunay = Delaunay.from(points);
const voronoi = delaunay.voronoi([0, 0, 600, 400]);

// Convert Voronoi polygons to G2 data format
const polygonData = Array.from({ length: points.length }, (_, i) => {
  const cell = voronoi.cellPolygon(i);
  if (!cell) return null;
  return {
    x: cell.map(([px]) => px),
    y: cell.map(([, py]) => py),
    index: i,
  };
}).filter(Boolean);

const chart = new Chart({ container: 'container', width: 600, height: 400 });

chart.options({
  type: 'polygon',
  data: polygonData,
  encode: {
    x: 'x',    // Array of x-coordinates for polygon vertices
    y: 'y',    // Array of y-coordinates for polygon vertices
    color: 'index',
  },
  scale: {
    x: { domain: [0, 600] },   // Specify coordinate range (type defaults to linear)
    y: { domain: [0, 400] },
    color: { type: 'ordinal' },
  },
  style: {
    fillOpacity: 0.6,
    stroke: '#fff',
    lineWidth: 1,
  },
  axis: false,
  legend: false,
});

chart.render();
```

## Data Format Description

```javascript
// Data format for polygon mark: Each record's x/y field is an array (sequence of polygon vertices)
const data = [
  {
    x: [10, 50, 90, 10],   // Polygon vertex x-coordinates (in order, automatically closed)
    y: [10, 80, 10, 10],   // Polygon vertex y-coordinates
    category: 'A',
  },
  {
    x: [100, 150, 200],    // Triangle
    y: [20, 100, 20],
    category: 'B',
  },
];

chart.options({
  type: 'polygon',
  data,
  encode: { x: 'x', y: 'y', color: 'category' },
});
```

## Common Errors and Fixes

### Error: x/y passed as a single value instead of an array
```javascript
// ❌ Error: x/y for polygon must be an array of coordinates, not a single value
chart.options({
  type: 'polygon',
  data: [{ x: 100, y: 200, ... }],  // ❌ x/y are single values, only one point
  encode: { x: 'x', y: 'y' },
});

// ✅ Correct: x/y are arrays of coordinates
chart.options({
  type: 'polygon',
  data: [{ x: [10, 50, 90], y: [10, 80, 10], ... }],  // ✅ Arrays
  encode: { x: 'x', y: 'y' },
});
```