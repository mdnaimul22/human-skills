---
id: "g2-comp-facet-circle"
title: "G2 Circular Facet (facetCircle)"
description: |
  facetCircle divides data into multiple subsets based on a specific field, arranging each subset's chart along a circular path.
  Unlike the rectangular grid of facetRect, facetCircle is suitable for displaying cyclical data (e.g., 12 months in a circular arrangement).
  Each subplot shares the same y-axis range, facilitating comparison.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "facetCircle"
  - "circular facet"
  - "facet"
  - "composition"
  - "cyclical"
  - "small multiples"

related:
  - "g2-comp-facet-rect"
  - "g2-comp-repeat-matrix"

use_cases:
  - "Circular small multiples comparison for 12 months"
  - "Circular facet for cyclical time data (7 days / 12 months)"
  - "Chart arrangement for cyclical categories"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/facet-circle"
---

## Minimum Viable Example (12-Month Circular Facet)

```javascript
import { Chart } from '@antv/g2';

// Daily data for each month
const data = [];
const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
months.forEach((month, mi) => {
  for (let day = 1; day <= 10; day++) {
    data.push({ month, day, value: Math.random() * 100 });
  }
});

const chart = new Chart({ container: 'container', width: 640, height: 640 });

chart.options({
  type: 'facetCircle',
  data,
  encode: { position: 'month' },  // Facet by month (determines the position of each subplot)
  children: [
    {
      type: 'interval',
      encode: { x: 'day', y: 'value', color: 'value' },
      scale: { color: { type: 'sequential', palette: 'blues' } },
      style: { lineWidth: 0 },
      coordinate: { type: 'polar' },  // Use polar coordinates for each subplot
    },
  ],
});

chart.render();
```

## Common Errors and Fixes

### Error: No `coordinate: polar` in children—Subplots are rectangular instead of circular
```javascript
// ❌ Although the facet arrangement in facetCircle is circular, the subplots themselves can still be in Cartesian coordinates
// Typically, a polar coordinate system needs to be specified in children to achieve a circular effect
chart.options({
  type: 'facetCircle',
  encode: { position: 'month' },
  children: [
    {
      type: 'interval',
      encode: { x: 'day', y: 'value' },
      // ❌ Without coordinate: polar, the subplot is a regular bar chart, arranged in a circle but not in polar coordinates
    },
  ],
});

// ✅ Typically, add polar coordinates to the subplots
children: [
  {
    type: 'interval',
    encode: { x: 'day', y: 'value' },
    coordinate: { type: 'polar' },  // ✅
  },
]
```