---
id: "g2-mark-regression-curve"
title: "G2 Regression Curve Chart"
description: |
  A regression curve chart overlays a regression trend line on top of a scatter plot. It uses `type: 'view'` to combine
  `type: 'point'` (original data) and `type: 'line'` (regression curve).
  The regression calculation is integrated via a custom callback in `data.transform` using libraries like `d3-regression`.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "regression curve chart"
  - "regression"
  - "linear regression"
  - "trend line"
  - "d3-regression"
  - "scatter plot"

related:
  - "g2-mark-point-scatter"
  - "g2-mark-line-basic"

use_cases:
  - "Demonstrating linear/non-linear relationships between two variables"
  - "Trend prediction"
  - "Correlation analysis"

anti_patterns:
  - "Regression is unreliable with fewer than 10 data points"
  - "Regression lines are unsuitable when variables are not correlated"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/regressioncurve"
---

## Core Concepts

**Regression Plot = `type: 'view'` combines `point` (scatter) + `line` (regression line)**

- Scatter (`type: 'point'`): Displays raw data
- Regression Line (`type: 'line'`): Calls the regression function via the `custom` callback in `data.transform`
- Commonly used regression libraries: `d3-regression` (`regressionLinear`, `regressionQuad`, `regressionExp`, `regressionLog`, `regressionPoly`)

**Regression Function Output Format**: Returns an array of points `[[x0, y0], [x1, y1], ...]`，encoded using `(d) => d[0]` and `(d) => d[1]`

## Linear Regression (Minimum Viable Example)

```javascript
import { Chart } from '@antv/g2';
import { regressionLinear } from 'd3-regression';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'view',
  autoFit: true,
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/linear-regression.json',
  },
  children: [
    // Points: Original Data
    {
      type: 'point',
      encode: { x: (d) => d[0], y: (d) => d[1] },
      scale: { x: { domain: [0, 1] }, y: { domain: [0, 5] } },
      style: { fillOpacity: 0.75, fill: '#1890ff' },
    },
    // Line: Regression Curve
    {
      type: 'line',
      data: {
        transform: [
          {
            type: 'custom',
            callback: regressionLinear(),  // d3-regression function
          },
        ],
      },
      encode: { x: (d) => d[0], y: (d) => d[1] },
      style: { stroke: '#30BF78', lineWidth: 2 },
      labels: [
        {
          text: 'y = 1.7x + 3.01',
          selector: 'last',
          position: 'right',
          textAlign: 'end',
          dy: -8,
        },
      ],
      tooltip: false,
    },
  ],
  axis: {
    x: { title: 'Independent Variable X' },
    y: { title: 'Dependent Variable Y' },
  },
});

chart.render();
```

## Polynomial Regression (Quadratic Regression)

```javascript
import { regressionQuad } from 'd3-regression';

chart.options({
  type: 'view',
  autoFit: true,
  data: [
    { x: -4, y: 5.2 }, { x: -3, y: 2.8 }, { x: -2, y: 1.5 },
    { x: -1, y: 0.8 }, { x: 0, y: 0.5 }, { x: 1, y: 0.8 },
    { x: 2, y: 1.5 }, { x: 3, y: 2.8 }, { x: 4, y: 5.2 },
  ],
  children: [
    {
      type: 'point',
      encode: { x: 'x', y: 'y' },
      style: { fillOpacity: 0.75, fill: '#1890ff' },
    },
    {
      type: 'line',
      transform: [
        {
          type: 'custom',
          callback: regressionQuad()
            .x((d) => d.x)
            .y((d) => d.y)
            .domain([-4, 4]),
        },
      ],
      encode: { x: (d) => d[0], y: (d) => d[1] },
      style: { stroke: '#30BF78', lineWidth: 2 },
      labels: [
        {
          text: 'y = 0.3x² + 0.5',
          selector: 'last',
          textAlign: 'end',
          dy: -8,
        },
      ],
      tooltip: false,
    },
  ],
});
```

## Exponential Regression

```javascript
import { regressionExp } from 'd3-regression';

// In the line sub-mark
{
  type: 'line',
  data: {
    transform: [
      {
        type: 'custom',
        callback: regressionExp(),
      },
    ],
  },
  encode: { x: (d) => d[0], y: (d) => d[1], shape: 'smooth' },
  style: { stroke: '#30BF78', lineWidth: 2 },
  tooltip: false,
}
```

## d3-regression Common Functions

| Function | Regression Type | Applicable Scenarios |
|------|---------|---------|
| `regressionLinear()` | Linear y = ax + b | Linear correlation |
| `regressionQuad()` | Quadratic y = ax² + bx + c | Parabolic relationship |
| `regressionPoly()` | Polynomial | Complex curves |
| `regressionExp()` | Exponential y = ae^(bx) | Exponential growth/decay |
| `regressionLog()` | Logarithmic y = a·ln(x) + b | Decreasing growth rate |
| `regressionPow()` | Power law y = ax^b | Power law relationship |

## Common Errors and Fixes

### Error 1: Regression Function Placed in the Wrong Location

```javascript
// ❌ Incorrect: Custom regression should be placed in the data.transform of the line sub-mark
chart.options({
  type: 'view',
   {
    transform: [{ type: 'custom', callback: regressionLinear() }],  // ❌ Placed on the parent view data
  },
  children: [{ type: 'point', encode: { x: 'x', y: 'y' } }],
});

// ✅ Correct: Each sub-mark has an independent data source
chart.options({
  type: 'view',
  data,  // Scatter plot data
  children: [
    { type: 'point', encode: { x: 'x', y: 'y' } },  // Scatter plot uses parent data
    {
      type: 'line',
      data: {
        transform: [{ type: 'custom', callback: regressionLinear().x(d => d.x).y(d => d.y) }],
      },                                               // ✅ Regression line has independent data
      encode: { x: (d) => d[0], y: (d) => d[1] },
    },
  ],
});
```

### Error 2: Incorrect Access Method for `encode` Field

```javascript
// ❌ Incorrect: d3-regression outputs an array [[x, y], ...], not an object
{
  type: 'line',
  encode: { x: 'x', y: 'y' },  // ❌ d[0] is not d.x
}

// ✅ Correct: Use a function to access array indices
{
  type: 'line',
  encode: { x: (d) => d[0], y: (d) => d[1] },  // ✅
}
```

### Error 3: Data Format Mismatch When Not Specifying `.x()`/`.y()`

```javascript
// ❌ Issue: By default, d3-regression assumes data is in the [x, y] array format
const data = [{ x: 1, y: 2 }, { x: 3, y: 4 }];  // Object format
// regressionLinear() defaults to reading d[0], d[1], which does not match the object format

// ✅ Correct: Explicitly specify field access methods
callback: regressionLinear()
  .x((d) => d.x)   // ✅ Specify x field
  .y((d) => d.y),  // ✅ Specify y field
```

### Error 4: Missing `data` Keyword

```javascript
// ❌ Incorrect
children: [
  {
    type: 'line',
    {
      transform: [{ type: 'custom', callback: regressionLinear() }],
    },                             // ❌ Isolated {} syntax error, missing `data:` key
    encode: { x: (d) => d[0], y: (d) => d[1] },
  },
]

// ✅ Correct
children: [
  {
    type: 'line',
     {                        // ✅ Must have `data:` key
      transform: [{ type: 'custom', callback: regressionLinear() }],
    },
    encode: { x: (d) => d[0], y: (d) => d[1] },
  },
]
```