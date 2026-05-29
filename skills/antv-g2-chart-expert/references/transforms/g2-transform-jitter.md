---
id: "g2-transform-jitter"
title: "G2 Jitter Transform (Scatter Overlapping Points)"
description: |
  The jitter transform adds random offsets to data points on a categorical axis, preventing complete overlap of points within the same category.
  jitter applies random offsets to both X and Y, jitterX only to X (commonly used for points on bar charts),
  and jitterY only to Y. It is often used with the point mark to display the distribution of categorical data.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "jitter"
  - "scatter"
  - "point chart"
  - "distribution"
  - "overlap"
  - "beeswarm"
  - "transform"

related:
  - "g2-mark-point-scatter"
  - "g2-transform-dodgex"
  - "g2-transform-stacky"

use_cases:
  - "Display the distribution density of data points within each category (more detailed than box plots)"
  - "Prevent overlapping of multiple data points on a categorical axis"
  - "Overlay with box plots to show both statistical summaries and raw data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/jitter"
---

## Minimum Viable Example (Jitter to Prevent Overlapping in Categorical Scatter Plot)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data: [
    { dept: 'R&D', salary: 18000 }, { dept: 'R&D', salary: 22000 },
    { dept: 'R&D', salary: 15000 }, { dept: 'R&D', salary: 19000 },
    { dept: 'Sales', salary: 12000 }, { dept: 'Sales', salary: 16000 },
    { dept: 'Sales', salary: 14000 }, { dept: 'Sales', salary: 11000 },
    { dept: 'Design', salary: 17000 }, { dept: 'Design', salary: 20000 },
  ],
  encode: {
    x: 'dept',     // Categorical axis (jitter will be applied in this direction)
    y: 'salary',
    color: 'dept',
  },
  transform: [{ type: 'jitter' }],   // Add random jitter in x and y directions
  style: { fillOpacity: 0.7, r: 4 },
});

chart.render();
```

## jitterX (Horizontal Jitter Only)

```javascript
// Suitable for vertical categorical axes — expands only in the x-direction, maintains precise values in the y-direction
chart.options({
  type: 'point',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  transform: [
    {
      type: 'jitterX',
      padding: 0.1,    // Category width ratio (0~0.5), default 0
      random: Math.random,  // Custom random function (can use a fixed seed)
    },
  ],
});
```

## Overlay with Box Plot

```javascript
chart.options({
  type: 'view',
  children: [
    // Box Plot (Display Statistical Summary)
    {
      type: 'boxplot',
      data,
      encode: { x: 'dept', y: 'salary' },
      style: { boxFill: 'transparent', lineWidth: 1.5 },
    },
    // Scatter Plot (Display Raw Data Distribution)
    {
      type: 'point',
      data,
      encode: { x: 'dept', y: 'salary', color: 'dept' },
      transform: [{ type: 'jitter', padding: 0.1 }],
      style: { r: 3, fillOpacity: 0.6 },
    },
  ],
});
```

## Configuration Options

```javascript
transform: [
  {
    type: 'jitter',    // or 'jitterX' / 'jitterY'
    padding: 0,        // category boundary padding (0~0.5), default 0
    paddingX: 0,       // set X padding separately (overrides padding)
    paddingY: 0,       // set Y padding separately (overrides padding)
    random: Math.random, // random function, can be replaced with a fixed seed pseudo-random function
  },
]
```

## Common Errors and Fixes

### Error 1: Using jitter on numerical axes—chaotic effect when both directions are numerical
```javascript
// ❌ Error: When both x and y are numerical, jitter disrupts precise numerical relationships
chart.options({
  type: 'point',
  encode: { x: 'price', y: 'sales' },  // Both are numerical axes
  transform: [{ type: 'jitter' }],      // ❌ Scatter plots inherently do not overlap, no need for jitter
});

// ✅ Jitter applied to scenarios with categorical axes
chart.options({
  encode: { x: 'category', y: 'value' },  // x is categorical
  transform: [{ type: 'jitter' }],         // ✅
});
```

### Error 2: Jitter Effect is Insignificant with Large Point Mark Data Volume—Padding is Too Small
```javascript
// ❌ With default padding: 0, all points jitter only within an extremely small category width range
transform: [{ type: 'jitter' }]  // Default padding is 0, jitter range is very small

// ✅ Increase padding appropriately
transform: [{ type: 'jitter', padding: 0.15 }]  // Use 15% of category width as jitter range
```