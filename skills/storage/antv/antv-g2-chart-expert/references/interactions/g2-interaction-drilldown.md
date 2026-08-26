---
id: "g2-interaction-drilldown"
title: "G2 Drill Down Interaction (drillDown)"
description: |
  The drillDown interaction is used for click-through on hierarchical data (partition / sunburst chart),
  After clicking a node, only the subtree of that node is displayed, and a breadcrumb navigation is shown at the top.
  Clicking on the breadcrumbs allows for step-by-step backtracking. Only applicable to partition mark.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "drillDown"
  - "drill down"
  - "hierarchical data"
  - "sunburst chart"
  - "partition"
  - "breadcrumb"
  - "interaction"

related:
  - "g2-mark-treemap"
  - "g2-interaction-element-select"

use_cases:
  - "Hierarchical data drill-down exploration in sunburst chart/rectangular partition chart"
  - "Layer-by-layer viewing of organizational structure charts"
  - "Interactive browsing of file directory trees"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/drill-down"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = {
  name: 'Company',
  children: [
    {
      name: 'R&D Department',
      children: [
        { name: 'Frontend Team', value: 12 },
        { name: 'Backend Team', value: 18 },
        { name: 'Algorithm Team', value: 8 },
      ],
    },
    {
      name: 'Marketing Department',
      children: [
        { name: 'Brand Team', value: 6 },
        { name: 'Operations Team', value: 10 },
      ],
    },
    {
      name: 'Design Department',
      children: [
        { name: 'UX Team', value: 7 },
        { name: 'Visual Team', value: 5 },
      ],
    },
  ],
};

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'sunburst',   // Sunburst chart (polar coordinate form of partition)
  data: { value: data },
  encode: { value: 'value', color: 'name' },
  interaction: {
    drillDown: true,   // Enable drill-down interaction
  },
});

chart.render();
```

## Customizing Breadcrumb Style

```javascript
chart.options({
  type: 'sunburst',
  data: { value: data },
  encode: { value: 'value', color: 'name' },
  interaction: {
    drillDown: {
      breadCrumb: {
        rootText: 'Whole Company',  // Root node breadcrumb text, default 'root'
        style: {
          fill: 'rgba(0,0,0,0.65)',
          fontSize: 13,
        },
        active: {
          fill: '#1890ff',          // Breadcrumb text color on hover
        },
        y: 8,                       // Breadcrumb Y-axis offset
      },
    },
  },
});
```

## Common Errors and Fixes

### Error 1: Using `drillDown` for `treemap` instead of `partition`/`sunburst`
```javascript
// ❌ Incorrect: `drillDown` is only applicable to `partition` types (including sunburst charts)
// `treemap` has a dedicated `treemapDrillDown` interaction
chart.options({
  type: 'treemap',
  interaction: { drillDown: true },  // ❌ Should use `treemapDrillDown`
});

// ✅ Correct: Use `treemapDrillDown` for `treemap`
chart.options({
  type: 'treemap',
  interaction: { treemapDrillDown: true },  // ✅
});

// ✅ Correct: Use `drillDown` for `sunburst`/`partition`
chart.options({
  type: 'sunburst',
  interaction: { drillDown: true },  // ✅
});
```

### Error 2: Data is not hierarchical—Drill-down cannot display child nodes
```javascript
// ❌ Flat data has no children, no content after drill-down
chart.options({
  data: [{ name: 'A', value: 10 }, { name: 'B', value: 20 }],  // ❌ Flat
  interaction: { drillDown: true },
});

// ✅ Must use hierarchical data with children
chart.options({
  data: {
    value: { name: 'root', children: [...] },  // ✅ Tree-like
  },
  interaction: { drillDown: true },
});
```