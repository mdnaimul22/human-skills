---
id: "g2-interaction-treemap-drilldown"
title: "G2 Treemap Drill-Down (treemapDrillDown)"
description: |
  treemapDrillDown provides hierarchical drill-down interaction for treemaps,
  allowing users to click on a rectangle to navigate to the next level. A breadcrumb navigation is displayed at the top for returning to the parent level.
  Unlike drillDown (used for partition/sunburst), this interaction is specifically designed for treemap layouts.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "treemapDrillDown"
  - "treemap"
  - "drill-down"
  - "hierarchy"
  - "breadcrumb"
  - "interaction"

related:
  - "g2-mark-treemap"
  - "g2-interaction-drilldown"
  - "g2-mark-partition"

use_cases:
  - "Multi-level directory/file size visualization"
  - "Product category hierarchy sales analysis"
  - "Organizational structure treemap drill-down"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/hierarchy/treemap/#treemap-drill-down"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Multi-level hierarchical data
const hierarchyData = {
  name: 'Total Sales',
  children: [
    {
      name: 'Electronics',
      children: [
        { name: 'Mobile Phones', value: 400 },
        { name: 'Computers', value: 350 },
        { name: 'Tablets', value: 200 },
      ],
    },
    {
      name: 'Clothing',
      children: [
        { name: 'Menswear', value: 280 },
        { name: 'Womenswear', value: 320 },
      ],
    },
    {
      name: 'Food',
      children: [
        { name: 'Snacks', value: 180 },
        { name: 'Beverages', value: 150 },
      ],
    },
  ],
};

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'treemap',
  data: hierarchyData,
  encode: { value: 'value', color: 'name' },
  style: {
    labelText: (d) => d.data.name,
    labelFill: '#fff',
    stroke: '#fff',
    lineWidth: 1,
  },
  interaction: {
    treemapDrillDown: {
      // Breadcrumb navigation style
      breadCrumbFill: 'rgba(0,0,0,0.85)',
      breadCrumbFontSize: 12,
      activeFill: 'rgba(0,0,0,0.5)',
    },
  },
});

chart.render();
```

## treemapDrillDown vs drillDown Comparison

```javascript
// treemapDrillDown: Designed specifically for treemap (rectangle tree map)
chart.options({
  type: 'treemap',
  interaction: { treemapDrillDown: true },
});

// drillDown: Used for partition (sunburst/icicle chart)
chart.options({
  type: 'partition',
  interaction: { drillDown: true },
  coordinate: { type: 'polar' },   // Sunburst chart uses polar coordinates
});
```

## Common Errors and Fixes

### Error: Using treemapDrillDown on a non-treemap mark
```javascript
// ❌ treemapDrillDown is only applicable to treemap marks
chart.options({
  type: 'partition',   // ❌ Applies drillDown, not treemapDrillDown
  interaction: { treemapDrillDown: true },
});

// ✅ Partition uses drillDown
chart.options({
  type: 'partition',
  interaction: { drillDown: true },   // ✅
});

// ✅ Treemap uses treemapDrillDown
chart.options({
  type: 'treemap',
  interaction: { treemapDrillDown: true },  // ✅
});
```

### Error: Data is not a nested hierarchical structure
```javascript
// ❌ Flat data cannot drill down
chart.options({
  type: 'treemap',
  data: [{ name: 'a', value: 10 }, { name: 'b', value: 20 }],  // ❌ No hierarchy
  interaction: { treemapDrillDown: true },
});

// ✅ Requires nested children structure
chart.options({
  type: 'treemap',
  data: { name: 'root', children: [...] },  // ✅ Nested hierarchy
  interaction: { treemapDrillDown: true },
});
```