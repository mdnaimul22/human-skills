---
id: "g2-coord-cartesian"
title: "G2 Cartesian Coordinate System"
description: |
  The cartesian coordinate system is the default coordinate system in G2 v5, where the x and y channels are mapped to horizontal and vertical positions, respectively.
  Most common charts (bar charts, line charts, scatter plots) use the cartesian coordinate system.
  Transformations such as transpose can be added to the cartesian coordinate system via coordinate.transform.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "cartesian"
  - "Cartesian Coordinate System"
  - "Default Coordinate System"
  - "coordinate"
  - "Cartesian"

related:
  - "g2-coord-transpose"
  - "g2-coord-polar"
  - "g2-mark-interval-basic"
  - "g2-mark-line-basic"

use_cases:
  - "Bar Chart (Default Cartesian Coordinate)"
  - "Line Chart (Default Cartesian Coordinate)"
  - "Horizontal Bar Chart (Cartesian Coordinate + Transpose)"
  - "Scatter Plot (Cartesian Coordinate)"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/cartesian"
---

## Core Concepts

The Cartesian coordinate system is the **default coordinate system** in G2, and does not require explicit configuration of the `coordinate` field.

- x channel → horizontal position (from left to right)
- y channel → vertical position (from bottom to top)
- Supports adding transformations such as transposition via `coordinate.transform`

## Default Usage (No Configuration Required)

```javascript
import { Chart } from '@antv/g2';

// Cartesian coordinate system is the default, no need to write coordinate configuration
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
  ],
  encode: { x: 'genre', y: 'sold' },
  // No need for coordinate configuration, default is Cartesian coordinate system
});

chart.render();
```

## Explicit Specification (Equivalent to Default)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  coordinate: { type: 'cartesian' },  // Explicit specification (equivalent to omitting)
});
```

## Cartesian Coordinate System + Transpose (Bar Chart)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  coordinate: {
    type: 'cartesian',
    transform: [{ type: 'transpose' }],  // Transpose: Swap x/y axes, converting column chart to bar chart
  },
});
```

## Coordinate System Configuration

```javascript
chart.options({
  coordinate: {
    type: 'cartesian',
    transform: [
      { type: 'transpose' },         // Transpose (swap x↔y)
      { type: 'reflect', x: true },  // Reflect across the X-axis
      { type: 'reflect', y: true },  // Reflect across the Y-axis
      { type: 'scale', sx: 1, sy: -1 },  // Custom scaling
    ],
  },
});
```

## Common Errors and Fixes

### Error: Cartesian Coordinate System Configured but Expecting a Pie/Donut Chart
```javascript
// ❌ Error: Pie/Donut charts require a theta coordinate system, not cartesian
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'cartesian' },  // ❌ This will render a regular bar chart
});

// ✅ Pie/Donut charts use a theta coordinate system
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8, innerRadius: 0.5 },  // ✅
});
```