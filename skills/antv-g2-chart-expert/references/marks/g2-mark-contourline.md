---
id: "g2-mark-contourline"
title: "G2 Contour Line Chart"
description: |
  Contour line charts are implemented using `type: 'cell'` or `type: 'line'`,
  displaying continuous data distribution on a two-dimensional plane (e.g., terrain elevation, temperature distribution) through color gradient grids or lines.
  G2 does not have a built-in contour line algorithm; typically, `cell + sequential` color scales are used to simulate contour line effects.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "contour line chart"
  - "contour"
  - "terrain map"
  - "heatmap"
  - "continuous data"
  - "2D distribution"

related:
  - "g2-mark-cell-heatmap"
  - "g2-mark-point-scatter"

use_cases:
  - "Terrain elevation visualization"
  - "Meteorological data distribution (temperature, pressure)"
  - "Spatial distribution of 2D continuous data"

anti_patterns:
  - "Discrete categorical data is not suitable for contour line charts"
  - "Time series data is not suitable"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/contourline"
---

## Core Concepts

There are two implementation methods for contour plots in G2:

1. **Grid color blocks simulating contour lines**: `type: 'cell'` + `sequential` color gradient, where color depth represents numerical value height
2. **Contour line outlines**: `type: 'line'` + grouping by numerical value levels, drawing closed isovalues

**The higher the grid density, the more refined the contour line effect** (requires evenly distributed grid points in the data)

## Grid Color Blocks Simulating Contour Lines (Most Commonly Used)

```javascript
import { Chart } from '@antv/g2';

// Generate terrain data
const terrainData = [];
for (let x = 0; x <= 50; x += 2) {
  for (let y = 0; y <= 50; y += 2) {
    const elevation1 = 100 * Math.exp(-((x - 15) ** 2 + (y - 15) ** 2) / 200);
    const elevation2 = 80 * Math.exp(-((x - 35) ** 2 + (y - 35) ** 2) / 150);
    const elevation = elevation1 + elevation2 + 10;
    terrainData.push({ x, y, elevation });
  }
}

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'cell',
  data: terrainData,
  encode: {
    x: 'x',
    y: 'y',
    color: 'elevation',
  },
  style: {
    stroke: '#333',
    lineWidth: 0.5,
    inset: 0.5,
  },
  scale: {
    color: {
      palette: 'viridis',
      type: 'sequential',
    },
  },
  legend: {
    color: {
      length: 300,
      layout: { justifyContent: 'center' },
      labelFormatter: (value) => `${Math.round(value)}m`,
    },
  },
  tooltip: {
    title: 'Elevation Information',
    items: [
      { field: 'x', name: 'Longitude' },
      { field: 'y', name: 'Latitude' },
      {
        field: 'elevation',
        name: 'Elevation',
        valueFormatter: (value) => `${Math.round(value)}m`,
      },
    ],
  },
});

chart.render();
```

## Contour Lines (Implemented with Line Charts)

Preprocess data by value levels, drawing one isopleth for each level:

```javascript
import { Chart } from '@antv/g2';

// Pre-calculate points for each contour line level
const generateContourLines = () => {
  const lines = [];
  const levels = [20, 40, 60, 80, 100];

  levels.forEach((level, index) => {
    for (let angle = 0; angle <= 360; angle += 5) {
      const radian = (angle * Math.PI) / 180;
      const baseRadius = 5 + index * 4;
      const radius = baseRadius + Math.sin((angle * Math.PI) / 45) * 2;
      lines.push({
        x: 25 + radius * Math.cos(radian),
        y: 25 + radius * Math.sin(radian),
        level,
        lineId: `line_${level}`,
      });
    }
  });
  return lines;
};

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'line',
  data: generateContourLines(),
  encode: {
    x: 'x',
    y: 'y',
    color: 'level',
    series: 'lineId',   // Each contour line is an independent series
  },
  style: {
    lineWidth: 2,
    strokeOpacity: 0.8,
  },
  scale: {
    color: {
      type: 'sequential',
      palette: 'oranges',
    },
  },
  axis: {
    x: { title: 'Distance (km)' },
    y: { title: 'Distance (km)' },
  },
  legend: {
    color: { title: 'Elevation (m)' },
  },
});

chart.render();
```

## Common Errors and Fixes

### Error 1: Missing `data` Keyword

```javascript
// ❌ Incorrect: The `data` keyword must be explicitly written
chart.options({
  type: 'cell',
  terrainData,   // ❌ Isolated object literal, missing `data:` key
  encode: { x: 'x', y: 'y', color: 'elevation' },
});

// ✅ Correct
chart.options({
  type: 'cell',
  data: terrainData,
  encode: { x: 'x', y: 'y', color: 'elevation' },
});
```

### Error 2: Contour Lines Missing Series Grouping

```javascript
// ❌ Incorrect: Without series, all contour points are connected into a single line
chart.options({
  type: 'line',
  data,
  encode: {
    x: 'x',
    y: 'y',
    color: 'level',
    // ❌ Missing series: 'lineId'
  },
});

// ✅ Correct: Each contour line is grouped independently using series
chart.options({
  type: 'line',
  data,
  encode: {
    x: 'x',
    y: 'y',
    color: 'level',
    series: 'lineId',  // ✅ Ensures each line is drawn independently
  },
});
```

### Error 3: Mismatched Color Scale Type

```javascript
// ❌ Error: Using ordinal color scale for continuous data, insufficient colors
scale: { color: { type: 'ordinal' } }  // ❌ Suitable for discrete categories

// ✅ Correct: Using sequential color scale for continuous data
scale: { color: { type: 'sequential', palette: 'viridis' } }  // ✅
```

## Contour Cell vs. Heatmap

| Feature | Contour Cell | Heatmap |
|------|------------|--------------|
| Coordinates | Uniform 2D grid (discrete x, y) | Uniform 2D grid |
| Color | Sequential gradient | Typically sequential |
| Use Case | Terrain, continuous field distribution | Frequency, density visualization |
| Data | 3D (x, y, z) | Typically frequency aggregation |