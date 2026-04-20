---
id: "g2-mark-point-bubble"
title: "G2 Bubble Chart"
description: |
  A bubble chart is an extension of a scatter plot, using a third channel, size (bubble size), to encode an additional numerical dimension.
  By binding a numerical field to encode.size, G2 automatically maps the value to the area of a circle (rather than the radius).
  It is suitable for simultaneously displaying the relationship between three numerical dimensions.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "bubble chart"
  - "bubble"
  - "scatter plot"
  - "point"
  - "three dimensions"
  - "size"

related:
  - "g2-mark-point-scatter"
  - "g2-scale-linear"

use_cases:
  - "Three-dimensional data relationships (e.g., GDP, population, life expectancy)"
  - "Using bubble size to express a third metric"
  - "Displaying intensity in comparison matrices"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/point/#bubble"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { country: 'China',    gdp: 17.7, population: 14.1, life: 77 },
  { country: 'United States',    gdp: 25.5, population: 3.3,  life: 79 },
  { country: 'India',    gdp: 3.4,  population: 14.2, life: 70 },
  { country: 'Japan',    gdp: 4.2,  population: 1.26, life: 84 },
  { country: 'Brazil',    gdp: 1.8,  population: 2.15, life: 76 },
  { country: 'Germany',    gdp: 4.1,  population: 0.83, life: 81 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: {
    x: 'gdp',          // X-axis: GDP (trillions USD)
    y: 'life',         // Y-axis: Life Expectancy (years)
    size: 'population', // Bubble size: Population (billions)
    color: 'country',  // Color: Country
    shape: 'circle',
  },
  scale: {
    size: {
      range: [8, 60],   // Bubble radius range (px), min/max
    },
  },
  style: {
    fillOpacity: 0.7,
    lineWidth: 1,
    stroke: '#fff',
  },
  labels: [
    {
      text: 'country',
      position: 'inside',
      style: { fontSize: 10 },
    },
  ],
  tooltip: {
    items: [
      { channel: 'x', name: 'GDP (trillions)', valueFormatter: (v) => `$${v}T` },
      { channel: 'y', name: 'Life Expectancy', valueFormatter: (v) => `${v} years` },
      { channel: 'size', name: 'Population', valueFormatter: (v) => `${v} billion` },
    ],
  },
});

chart.render();
```

## Configure the size scale

```javascript
scale: {
  size: {
    type: 'linear',   // Default: Linear mapping of values to size
    range: [5, 50],   // [Minimum radius, Maximum radius] (px)
    // Note: G2 maps by area rather than radius, which is visually more accurate
  },
}
```

## Common Errors and Fixes

### Error 1: Size Channel Bound to String Category Instead of Numerical Value
```javascript
// ❌ Incorrect: Size channel should be bound to a numerical field, not a category
chart.options({
  encode: {
    size: 'country',  // ❌ String, cannot be mapped to size
  },
});

// ✅ Correct: Size bound to a numerical field
chart.options({
  encode: {
    size: 'population',  // ✅ Numerical, can be mapped to bubble size
  },
});
```

### Error 2: Failure to Set `scale.size.range`—Bubble Size Too Small or Too Large
```javascript
// ❌ Default range may result in inappropriate bubble sizes (obscuring other data or nearly invisible)
chart.options({
  encode: { size: 'value' },
  // ❌ Missing scale.size.range
});

// ✅ Explicitly set an appropriate bubble size range
chart.options({
  encode: { size: 'value' },
  scale: {
    size: { range: [8, 48] },  // ✅ Suitable visual range
  },
});
```