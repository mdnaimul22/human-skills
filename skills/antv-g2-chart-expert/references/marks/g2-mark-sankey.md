---
id: "g2-mark-sankey"
title: "G2 Sankey Diagram (sankey)"
description: |
  G2 v5 comes with a built-in sankey Mark, used to display multi-stage flow/energy distribution,
  with a data format consisting of an array of links containing source, target, and value.
  Node width is automatically determined by incoming/outgoing flow.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Sankey Diagram"
  - "sankey"
  - "Flow Diagram"
  - "Energy Flow"
  - "Conversion Funnel"
  - "spec"

related:
  - "g2-mark-funnel"
  - "g2-recipe-funnel"
  - "g2-core-chart-init"

use_cases:
  - "Displaying energy/material flow distribution"
  - "Multi-step user conversion path analysis"
  - "Budget/fund flow visualization"
  - "Supply chain flow diagram"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/graph/network/#sankey"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 800,
  height: 500,
});

// Links array: each record represents a flow
const links = [
  { source: 'Visit', target: 'Register', value: 8000 },
  { source: 'Visit', target: 'Direct Leave', value: 2000 },
  { source: 'Register', target: 'Activate', value: 5000 },
  { source: 'Register', target: 'Churn', value: 3000 },
  { source: 'Activate', target: 'Pay', value: 2000 },
  { source: 'Activate', target: 'Free Use', value: 3000 },
];

chart.options({
  type: 'sankey',
  data: {
    value: {
      links,    // Links array (required)
      // nodes optional, automatically extracted from links if not provided
    },
  },
  layout: {
    nodeAlign: 'justify',   // Node alignment: 'left'|'right'|'center'|'justify'
    nodePadding: 0.03,      // Node vertical padding (0-1)
  },
  style: {
    labelSpacing: 3,
    nodeLineWidth: 1,
    linkFillOpacity: 0.4,
  },
  legend: false,
});

chart.render();
```

## Sankey Diagram with Color Differentiation

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 900,
  height: 600,
});

const links = [
  { source: 'Coal', target: 'Electricity', value: 150 },
  { source: 'Oil', target: 'Transportation', value: 120 },
  { source: 'Natural Gas', target: 'Heating', value: 80 },
  { source: 'Electricity', target: 'Industry', value: 90 },
  { source: 'Electricity', target: 'Residential', value: 60 },
  { source: 'Transportation', target: 'Highway', value: 80 },
  { source: 'Transportation', target: 'Aviation', value: 40 },
];

chart.options({
  type: 'sankey',
  data: {
    value: { links },
  },
  layout: {
    nodeAlign: 'center',
    nodePadding: 0.03,
    nodeWidth: 0.02,       // Node width (relative to canvas)
  },
  scale: {
    color: {
      type: 'ordinal',
      // Color follows the source node
    },
  },
  style: {
    labelSpacing: 4,
    labelFontWeight: 'bold',
    labelFontSize: 12,
    nodeLineWidth: 1.2,
    linkFillOpacity: 0.35,
  },
  legend: false,
});

chart.render();
```

## Complete Configuration Options

```javascript
chart.options({
  type: 'sankey',
  data: {
    value: {
      links: [
        { source: 'A', target: 'B', value: 10 },  // source/target are node names
      ],
      nodes: [     // Optional, automatically inferred
        { key: 'A' },
        { key: 'B' },
      ],
    },
  },

  layout: {
    nodeId: (d) => d.key,      // Node ID extraction (default d.key)
    nodeAlign: 'justify',       // 'left'|'right'|'center'|'justify'
    nodeWidth: 0.02,            // Node width (relative to canvas width, 0-1)
    nodePadding: 0.02,          // Vertical padding between nodes
    nodeSort: null,             // Node sorting function
    linkSort: null,             // Link sorting function
    iterations: 6,              // Number of layout iterations
  },

  style: {
    labelSpacing: 3,            // Spacing between label and node
    labelFontSize: 12,
    labelFontWeight: 'normal',
    nodeLineWidth: 1,           // Node border width
    nodeStroke: '#fff',         // Node border color
    linkFillOpacity: 0.4,       // Link opacity
  },
});
```

## Common Errors and Fixes

### Error 1: Incorrect Data Format — Directly Passing the `links` Array

```javascript
// ❌ Incorrect: Sankey's data requires wrapping in { value: { links } }
chart.options({
  type: 'sankey',
  data: links,   // ❌ Directly passing the array
});

// ✅ Correct
chart.options({
  type: 'sankey',
  data: {
    value: { links },   // ✅ Requires { value: { links } } structure
  },
});
```

### Error 2: Broken Links Due to Inconsistent Source/Target Node Names

```javascript
// ❌ Error: '电力' and '电力公司' are treated as two different nodes
const links = [
  { source: '煤炭',   target: '电力',   value: 100 },
  { source: '电力公司', target: '工业', value: 80 },   // ❌ Inconsistent names!
];

// ✅ Correct: Use exactly the same name for the same node in source and target
const links = [
  { source: '煤炭', target: '电力', value: 100 },
  { source: '电力', target: '工业', value: 80 },   // ✅ Exact match
];
```
### Error 3: Presence of Cycles (Circular References) in the Chart

```javascript
// ❌ Sankey charts do not support circular flows
const links = [
  { source: 'A', target: 'B', value: 10 },
  { source: 'B', target: 'A', value: 5 },   // ❌ Forms a cycle! Layout anomaly
];

// ✅ Sankey charts are only suitable for directed acyclic flow data
```