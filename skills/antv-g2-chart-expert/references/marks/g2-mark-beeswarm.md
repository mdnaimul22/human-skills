---
id: "g2-mark-beeswarm"
title: "G2 Beeswarm Plot"
description: |
  The beeswarm mark automatically arranges scatter points along a categorical axis to avoid overlap, resembling a honeycomb.
  Each point is tightly arranged without obscuring others. It is suitable for displaying the distribution of single-dimensional numerical values under categorical variables.
  Unlike the random offset of the jitter transform, beeswarm uses a force-directed algorithm for precise arrangement.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "beeswarm"
  - "beeswarm plot"
  - "point distribution"
  - "non-overlapping scatter"
  - "distribution plot"

related:
  - "g2-mark-point-scatter"
  - "g2-transform-jitter"
  - "g2-mark-box-boxplot"

use_cases:
  - "Displaying the precise distribution of data points under each category (without overlap)"
  - "Using in conjunction with box plots to show both summary and raw data"
  - "Precise distribution display for small sample data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/point/#beeswarm"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { dept: 'R&D', salary: 18000 }, { dept: 'R&D', salary: 22000 },
  { dept: 'R&D', salary: 15000 }, { dept: 'R&D', salary: 25000 },
  { dept: 'R&D', salary: 19000 }, { dept: 'R&D', salary: 21000 },
  { dept: 'Sales', salary: 12000 }, { dept: 'Sales', salary: 16000 },
  { dept: 'Sales', salary: 14000 }, { dept: 'Sales', salary: 11000 },
  { dept: 'Design', salary: 17000 }, { dept: 'Design', salary: 20000 },
  { dept: 'Design', salary: 18500 }, { dept: 'Design', salary: 23000 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'point',
  data,
  encode: {
    x: 'dept',
    y: 'salary',
    color: 'dept',
    shape: 'point',
  },
  // beeswarm layout is configured via layout, not as a separate mark type
  // it's actually a point mark + beeswarm layout transformation
  style: { r: 5, fillOpacity: 0.8 },
  // use jitter transform to approximate beeswarm effect (or use beeswarm data transformation)
  transform: [{ type: 'jitter', padding: 0.1 }],
});

chart.render();
```

## Using beeswarm mark (independent type)

```javascript
// G2 v5 also supports type: 'beeswarm' to directly use the beeswarm layout
const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'point',
  data,
  encode: {
    x: 'dept',
    y: 'salary',
    color: 'dept',
  },
  // beeswarm uses a force-directed algorithm to arrange points without overlapping
  style: { r: 4, fillOpacity: 0.75 },
  layout: {
    type: 'beeswarm',   // Use beeswarm layout
    padding: 1,         // Spacing between points
  },
});
```

## Overlay with Box Plot

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'boxplot',
      encode: { x: 'dept', y: 'salary' },
      style: { boxFill: 'transparent', boxStroke: '#999', lineWidth: 1.5 },
    },
    {
      type: 'point',
      encode: { x: 'dept', y: 'salary', color: 'dept' },
      transform: [{ type: 'jitter', padding: 0.1 }],
      style: { r: 3.5, fillOpacity: 0.65 },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Too much data for beeswarm—slow layout calculation and visually cluttered
```javascript
// ❌ Using beeswarm with over a thousand data points is slow and visually saturated
chart.options({
  data: tenThousandRows,   // ❌ Too much data
  transform: [{ type: 'jitter' }],
});

// ✅ Switch to density plot or colored scatter plot for large datasets
// beeswarm is suitable for < 500 data points
chart.options({
  data: smallSample,
  transform: [{ type: 'jitter', padding: 0.08 }],  // ✅ Small sample
});
```