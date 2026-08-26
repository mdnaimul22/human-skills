---
id: "g2-mark-heatmap"
title: "G2 Gradient Heatmap (heatmap mark)"
description: |
  The heatmap mark (distinct from the cell mark color block heatmap) uses Gaussian kernel density gradients to render heat distribution,
  with each point generating an outward-diffusing heat halo effect. It is suitable for displaying geospatial density or two-dimensional density distributions.
  The intensity is specified through the color channel, and the size controls the heat halo radius.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "heatmap"
  - "heatmap"
  - "density heatmap"
  - "gradient heatmap"
  - "Gaussian kernel"
  - "spatial density"

related:
  - "g2-mark-cell-heatmap"
  - "g2-mark-density"
  - "g2-mark-point-scatter"

use_cases:
  - "User click/visit heatmap on maps"
  - "Density distribution visualization in two-dimensional space"
  - "Density display of a large number of overlapping points (clearer than scatter plots)"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/heatmap/"
---
## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Two-dimensional data with density weights
const data = Array.from({ length: 500 }, () => ({
  x: Math.random() * 100 + (Math.random() > 0.5 ? 20 : 60),
  y: Math.random() * 100 + (Math.random() > 0.5 ? 20 : 70),
  weight: Math.random(),
}));

const chart = new Chart({ container: 'container', width: 600, height: 500 });

chart.options({
  type: 'heatmap',   // Gradient heatmap (not cell heatmap)
  data,
  encode: {
    x: 'x',
    y: 'y',
    color: 'weight',  // Heat intensity (0~1)
    size: 30,         // Heat radius (px), fixed value or field name
  },
  style: {
    opacity: 0.8,
  },
  scale: {
    color: {
      type: 'sequential',
      palette: ['blue', 'cyan', 'lime', 'yellow', 'red'],  // Cold to warm colors
    },
  },
  axis: false,
  legend: false,
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'heatmap',
  data,
  encode: {
    x: 'lng',
    y: 'lat',
    color: 'intensity',    // Intensity field (default 0~1)
    size: 'radius',        // Heat radius, can be a field name or a fixed number
                           // Default 40 (px)
  },
  style: {
    opacity: 1,            // Overall opacity
  },
});
```

## heatmap vs cell Heatmap

```javascript
// heatmap mark: Gaussian gradient, continuous heat halo effect, suitable for point data density
chart.options({ type: 'heatmap', ... });

// cell mark: Discrete color blocks, suitable for matrix data (e.g., time × category two-dimensional tables)
chart.options({ type: 'cell', ... });
```

## Common Errors and Fixes

### Error 1: Color Channel Value Range Not in 0~1—Heatmap Color Mapping Anomaly
```javascript
// ❌ If the color value is a raw count (e.g., 500, 1000), the color mapping may be inaccurate
chart.options({
  encode: { color: 'rawCount' },  // ⚠️ rawCount values may range from 0~10000
});

// ✅ Normalize to 0~1, or set scale.color.domain
chart.options({
  encode: { color: 'intensity' },  // intensity is already normalized to 0~1
  // or configure domain
  scale: { color: { domain: [0, 1000] } },  // Explicitly specify the range
});
```

### Error 2: Confusion with Cell Mark—Cell is a Matrix Grid, Heatmap is Continuous Gradient
```javascript
// ❌ Using cell to display spatial density—grid-like, lacks continuous gradient effect
chart.options({ type: 'cell', encode: { x: 'lng', y: 'lat', color: 'density' } });

// ✅ Spatial density using heatmap (continuous gradient heat halo effect)
chart.options({ type: 'heatmap', encode: { x: 'lng', y: 'lat', color: 'density', size: 30 } });
```