---
id: "g2-coord-radial"
title: "G2 Radial Coordinate System (radial)"
description: |
  radial (radial coordinate system) is a variant of the polar coordinate system in G2 v5,
  which maps the transposed Cartesian coordinates to a circular layout: the x-axis is mapped to the radius, and the y-axis is mapped to the angle.
  Contrary to polar (where x→angle, y→radius),
  radial is suitable for rendering radial bar charts (centripetal bar charts), radial line charts, and more.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "radial"
  - "radial coordinate"
  - "centripetal bar chart"
  - "radial chart"
  - "coordinate"
  - "circular layout"

related:
  - "g2-coord-polar"
  - "g2-coord-theta"
  - "g2-mark-interval-basic"

use_cases:
  - "Radial bar chart (outward radiating bar chart)"
  - "Circular bar chart (categories extending outward from the center)"
  - "Circular layout display of time series"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/radial"
---

## Core Concepts

The mapping relationship between the radial coordinate system and the polar coordinate system is opposite:

| Coordinate System | x Channel | y Channel | Typical Chart |
|-------------------|-----------|-----------|---------------|
| `polar`           | → Angle (Circumferential Direction) | → Radius (Distance from Center) | Rose Chart |
| `radial`          | → Radius (Distance from Center) | → Angle (Circumferential Direction) | Radial Bar Chart |

## Minimum Viable Example (Radial Bar Chart)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 500, height: 500 });

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', value: 83 },
    { month: 'Feb', value: 60 },
    { month: 'Mar', value: 95 },
    { month: 'Apr', value: 72 },
    { month: 'May', value: 110 },
    { month: 'Jun', value: 85 },
  ],
  encode: {
    x: 'month',    // x channel → angle (circumferential position)
    y: 'value',    // y channel → radius (bar length)
    color: 'month',
  },
  coordinate: { type: 'radial', innerRadius: 0.1, outerRadius: 0.8 },
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  coordinate: {
    type: 'radial',
    innerRadius: 0.1,            // Inner radius (0 = from center), default 0
    outerRadius: 1,              // Outer radius ratio, default 1
    startAngle: -Math.PI / 2,    // Start angle, default -π/2 (12 o'clock direction)
    endAngle: (Math.PI * 3) / 2, // End angle, default 3π/2 (clockwise full circle)
  },
});
```

## Radial Column Chart with Inner Hole (Ring)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  coordinate: {
    type: 'radial',
    innerRadius: 0.3,   // Reserve space in the center
    outerRadius: 0.9,
  },
  style: { fillOpacity: 0.85 },
});
```

## Difference from Polar Coordinate System

```javascript
// polar: x→angle, y→radius (rose chart effect)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },  // x is categorical (angle), y is numerical (radius)
  coordinate: { type: 'polar' },
});

// radial: x→radius, y→angle (radial bar chart effect)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },  // x is categorical (radius), y is numerical (angle)
  coordinate: { type: 'radial' },
});
```

## Common Errors and Fixes

### Error: Encoding of x/y is opposite to the expected direction
```javascript
// ❌ Error: In radial coordinates, x should represent the angular direction (category), and y should represent the radial direction (value)
chart.options({
  type: 'interval',
  encode: { x: 'value', y: 'month' },  // ❌ Value as angle, month as radius
  coordinate: { type: 'radial' },
});

// ✅ Correct: Use the categorical field as x (mapped to angle) and the numerical field as y (mapped to radius)
chart.options({
  type: 'interval',
  encode: { x: 'month', y: 'value' },  // ✅ Month→angle, value→radius
  coordinate: { type: 'radial' },
});
```

### Error: Centered Image Not Displayed Correctly
```javascript
// ❌ Error: Using fixed coordinates (0,0) to display the image does not guarantee it will be centered
chart.options({
  type: 'image',
  data: [{ url: 'https://example.com/logo.png' }],
  encode: {
    x: () => 0,
    y: () => 0
  },
  style: {
    img: (d) => d.url,
    width: 80,
    height: 80
  }
});

// ✅ Correct: Use style.x and style.y to set relative positions, ensuring the image is centered
chart.options({
  type: 'image',
  data: [{ src: 'https://example.com/logo.png' }],
  style: {
    x: '50%',      // 50% relative to the container width
    y: '50%',      // 50% relative to the container height
    width: 80,
    height: 80
  }
});
```

### Error: Multiple View Overlays Causing Coordinate System Conflicts
```javascript
// ❌ Error: Redefining coordinate in view leads to rendering anomalies
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      coordinate: { type: 'radial' }  // Defining coordinate in child view may cause conflicts
    },
    {
      type: 'image',
      coordinate: { type: 'radial' }  // Image markers do not require a coordinate system
    }
  ]
});

// ✅ Correct: Define coordinate in the top-level view, and child elements inherit it
chart.options({
  type: 'view',
  coordinate: { type: 'radial', innerRadius: 0.3 },
  children: [
    {
      type: 'interval',
      data,
      encode: { x: 'type', y: 'value' }
    },
    {
      type: 'image',
      data: [{ src: 'https://example.com/logo.png' }],
      style: {
        x: '50%',
        y: '50%',
        width: 80,
        height: 80
      }
    }
  ]
});
```