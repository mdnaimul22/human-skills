---
id: "g2-mark-tree"
title: "G2 Tree Chart"
description: |
  The tree mark renders hierarchical data (tree-like JSON) into a tree structure,
  automatically laying out nodes (point marks) and links (link marks),
  supporting horizontal/vertical/radial layouts. It is suitable for organizational charts, decision trees, and hierarchical classification displays.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "tree"
  - "树形图"
  - "层级"
  - "组织架构"
  - "树状"
  - "hierarchy"

related:
  - "g2-mark-treemap"
  - "g2-mark-partition"
  - "g2-mark-sankey"

use_cases:
  - "Organizational chart display"
  - "Decision tree visualization"
  - "File directory tree display"
  - "Categorical hierarchy visualization"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/hierarchy/tree/"
---
## Minimum Viable Example (Horizontal Tree Chart)

```javascript
import { Chart } from '@antv/g2';

// Tree data (nested JSON format)
const treeData = {
  name: 'Headquarters',
  children: [
    {
      name: 'R&D Department',
      children: [
        { name: 'Frontend Team', value: 10 },
        { name: 'Backend Team', value: 15 },
        { name: 'Algorithm Team', value: 8 },
      ],
    },
    {
      name: 'Marketing Department',
      children: [
        { name: 'Brand Team', value: 6 },
        { name: 'Operations Team', value: 9 },
      ],
    },
    {
      name: 'Product Department',
      children: [
        { name: 'B2B Products', value: 7 },
        { name: 'B2C Products', value: 5 },
      ],
    },
  ],
};

const chart = new Chart({ container: 'container', width: 800, height: 500 });

chart.options({
  type: 'tree',
  data: treeData,
  layout: {
    // Layout direction: false=vertical (top→bottom), true=horizontal (left→right)
    // G2 tree uses d3-hierarchy tidy tree layout
  },
  encode: {
    value: 'value',  // Node size encoding field (optional)
  },
  // Node style
  nodeLabels: [
    { text: 'name', style: { fontSize: 12, dx: 6 } },
  ],
  // Link style
  style: {
    nodeSize: 5,
    nodeFill: '#5B8FF9',
    linkStroke: '#aaa',
    linkLineWidth: 1.5,
  },
});

chart.render();
```

## Vertical Tree Chart (Top-Down)

```javascript
chart.options({
  type: 'tree',
  data: treeData,
  coordinate: { transform: [{ type: 'transpose' }] },  // Transpose to vertical
  nodeLabels: [
    {
      text: 'name',
      style: { fontSize: 11, textBaseline: 'bottom', dy: -6 },
    },
  ],
  style: {
    nodeFill: '#52c41a',
    nodeSize: 6,
    linkShape: 'smooth',  // Use smooth curves for links
  },
});
```

## Radial Tree Chart (Radial)

```javascript
chart.options({
  type: 'tree',
  data: treeData,
  coordinate: { type: 'polar', innerRadius: 0.1 },  // Polar coordinate = radial layout
  style: {
    nodeFill: '#ff7875',
    nodeSize: 4,
  },
  nodeLabels: [
    {
      text: 'name',
      style: {
        fontSize: 10,
        textAlign: (d) => (d.x > Math.PI ? 'right' : 'left'),
      },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Passing Flat Data Instead of Nested JSON
```javascript
// ❌ tree mark requires nested JSON (children field), does not accept flat arrays
chart.options({
  type: 'tree',
  data: [
    { id: 1, parent: null, name: 'Root' },
    { id: 2, parent: 1, name: 'Child' },
  ],  // ❌ Flat data cannot be used directly
});

// ✅ Nested format is required
chart.options({
  type: 'tree',
  data: { name: 'Root', children: [{ name: 'Child' }] },  // ✅ Nested JSON
});
```

### Error: Confusion between Tree and Treemap
```javascript
// Tree: Displays hierarchical relationships (nodes + lines, emphasizing hierarchy and connections)
chart.options({ type: 'tree',  data: { value: hierarchyData } });

// Treemap: Displays hierarchical data proportions by area (nested rectangles, emphasizing size and ratio)
chart.options({ type: 'treemap',  data: { value: hierarchyData } });
```

---

## Node Data Access Rules (Important!)

In the hierarchical chart, the parameter `d` received by the callback function **is not the original data object**, but rather a hierarchical node wrapped by G2 using d3-hierarchy. **The original data is stored in `d.data`**.

### Callback Parameter d Structure

```javascript
// d is a d3-hierarchy node, with the following structure:
{
  value: 10,               // Node value (sum of subtree calculated by d3)
  depth: 2,                // Hierarchy depth (0 = root node)
  height: 0,               // Subtree height (0 for leaf nodes)
  data: {                  // ← Original data is here!
    name: 'Frontend Team',
    value: 10,
    // ... other custom fields
  },
  path: ['Root', 'R&D Department', 'Frontend Team'],
}
```

### Accessing Fields in nodeLabels

When the `nodeLabels` of the tree mark uses the string `'name'`, G2 internally looks up `d.data['name']` (with special handling), so the string form works. However, to access computed properties (`depth`, `height`) or for conditional rendering, a callback must be used:

```javascript
// ✅ String form (tree's nodeLabels has special handling for data fields)
nodeLabels: [
  { text: 'name', style: { fontSize: 12 } },
]

// ✅ Callback form (required for conditional logic or accessing node properties)
nodeLabels: [
  {
    text: (d) => {
      if (d.height > 0) return d.data?.name;  // Parent nodes display name
      return `${d.data?.name}\n(${d.value})`;  // Leaf nodes display name + value
    },
    style: { fontSize: 12 },
  },
]
```

### encode.color Must Use Callback

Like other mark levels, the `encode.color` string does **not work** for trees:

```javascript
// ❌ Wrong: color: 'type' is equivalent to d['type'] = undefined
encode: {
  value: 'value',
  color: 'type',  // ❌ → undefined → all nodes have the same color
}

// ✅ Correct: Must use callback
encode: {
  value: 'value',
  color: (d) => d.data?.type,  // ✅ Access original field via d.data
}
```