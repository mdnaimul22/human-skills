---
id: "g2-mark-treemap"
title: "G2 Treemap"
description: |
  G2 v5 comes with a built-in treemap Mark, which uses rectangular areas to represent the proportion of each node in hierarchical data.
  The data adopts a nested children tree structure, and leaf node values are mapped via encode.value.
  It supports various tile layout algorithms and hierarchical drill-down interactions.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "treemap"
  - "hierarchical data"
  - "proportion"
  - "hierarchy"
  - "tree"
  - "spec"

related:
  - "g2-mark-arc-pie"
  - "g2-mark-sankey"
  - "g2-core-chart-init"

use_cases:
  - "Displaying file directory/disk usage size"
  - "Sales proportion by product category (multi-level)"
  - "Stock market sector heatmap of gains and losses"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/graph/hierarchy/#treemap"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 800,
  height: 500,
});

// Hierarchical nested data
const data = {
  name: 'root',
  children: [
    {
      name: 'Technology',
      children: [
        { name: 'Frontend', value: 120 },
        { name: 'Backend', value: 180 },
        { name: 'Algorithm', value: 80 },
      ],
    },
    {
      name: 'Product',
      children: [
        { name: 'Mobile', value: 95 },
        { name: 'Web', value: 60 },
      ],
    },
    {
      name: 'Design',
      children: [
        { name: 'UI', value: 70 },
        { name: 'UX', value: 45 },
      ],
    },
  ],
};

chart.options({
  type: 'treemap',
  data: {
    value: data
  },
  encode: {
    value: 'value',   // Leaf node value field
  },
  layout: {
    tile: 'treemapSquarify',    // Layout algorithm (default)
    paddingInner: 2,            // Rectangle spacing
  },
  style: {
    labelText: (d) => d.data?.name || '',
    labelFill: '#fff',
    labelFontSize: 13,
    fillOpacity: 0.85,
  },
  legend: false,
});

chart.render();
```

## Data Configuration Format Explanation

**Why does treemap use `{ value: data }` instead of `data`?**

Hierarchical data is an **object** (containing name/children), not an array, and must use the full form:

```javascript
// ❌ Error: Hierarchical data is not an array, cannot use shorthand
chart.options({
  type: 'treemap',
  data: hierarchyData,  // ❌ Does not work
});

// ✅ Correct: Hierarchical data must use the full form
chart.options({
  type: 'treemap',
  data: { value: hierarchyData },  // ✅
});
```

**Shorthand form is only applicable to array data** (meeting three conditions: inline, is an array, and has no transform).

---

## Complete Configuration Options

```javascript
chart.options({
  type: 'treemap',
  data: {
    value: hierarchicalData
  },
  encode: {
    value: 'value',   // Leaf node value field (determines rectangle area)
  },
  layout: {
    // Tile algorithm selection:
    // 'treemapSquarify' (default, close to square)
    // 'treemapBinary' (binary partition)
    // 'treemapDice' (horizontal partition)
    // 'treemapSlice' (vertical partition)
    // 'treemapSliceDice' (alternating partition)
    tile: 'treemapSquarify',
    paddingInner: 2,      // Spacing between rectangles at the same level (px)
    paddingOuter: 4,      // Outer margin
    paddingTop: 20,       // Top padding (for parent node labels)
    ratio: 1.618,         // Golden ratio (treemapSquarify specific)
    ignoreParentValue: true,  // Ignore parent node's own value
  },
  style: {
    // Rectangle labels
    labelText: (d) => d.data?.name,
    labelFill: '#fff',
    labelFontSize: 12,
    labelPosition: 'top-left',  // Label position
    fillOpacity: 0.8,
    stroke: '#fff',
    lineWidth: 1,
  },
});
```

## Multi-Level Labels (Parent Node + Leaf Node)

```javascript
chart.options({
  type: 'treemap',
  data: {
    value: data
  },
  encode: { value: 'value' },
  layout: {
    tile: 'treemapSquarify',
    paddingInner: 3,
    paddingTop: 24,       // Reserve space for parent node titles
  },
  style: {
    // Display name for leaf nodes
    labelText: (d) => {
      // path is the array path from root to current node
      return d.depth > 1 ? d.data?.name : '';
    },
    // Use large labels for parent nodes (depth=1)
    labelFontSize: (d) => d.depth === 1 ? 14 : 11,
    labelFontWeight: (d) => d.depth === 1 ? 'bold' : 'normal',
    labelFill: '#fff',
    fillOpacity: (d) => d.depth === 1 ? 0.6 : 0.85,
  },
});
```

## Stock Sector Heatmap (Market Rise and Fall)

```javascript
const marketData = {
  name: 'A-shares',
  children: [
    {
      name: 'Technology',
      children: [
        { name: 'Huawei', value: 1200, change: 3.5 },
        { name: 'Tencent', value: 980,  change: -1.2 },
        { name: 'Alibaba', value: 850,  change: 0.8 },
      ],
    },
    {
      name: 'Finance',
      children: [
        { name: 'ICBC', value: 2100, change: 1.1 },
        { name: 'CCB', value: 1800, change: -0.5 },
      ],
    },
  ],
};

chart.options({
  type: 'treemap',
  data: {
    value: marketData
  },
  encode: {
    value: 'value',
    // Color mapped by rise and fall percentage
    color: (d) => d.data?.change ?? 0,
  },
  scale: {
    color: {
      type: 'diverging',
      palette: 'RdYlGn',      // Red (fall) → Yellow (flat) → Green (rise)
      domain: [-5, 0, 5],
    },
  },
  style: {
    labelText: (d) =>
      d.data?.name && d.data?.change != null
        ? `${d.data.name}\n${d.data.change > 0 ? '+' : ''}${d.data.change}%`
        : d.data?.name || '',
    labelFill: '#fff',
    labelFontSize: 12,
  },
  legend: { color: { position: 'top' } },
});
```

## Common Errors and Fixes

### Error 1: Data Format is Not a Tree Structure

```javascript
// ❌ Incorrect: Treemap requires nested tree data, not a flat array
chart.options({
  type: 'treemap',
  data: [
    { name: 'Frontend', value: 120, parent: 'Technology' },   // ❌ Flat format
  ],
});

// ✅ Correct: Requires children nested structure
chart.options({
  type: 'treemap',
  data: {
    value: {
      name: 'root',
      children: [
        {
          name: 'Technology',
          children: [
            { name: 'Frontend', value: 120 },   // ✅ Leaf nodes have value
          ],
        },
      ],
    },
  },
  encode: { value: 'value' },
});
```

### Error 2: Mismatch Between `encode.value` Field Name and Data

```javascript
// ❌ Error: The leaf node field in the data is `size`, but `encode.value` is set to `value`
const data = {
  value: { name: 'root', children: [{ name: 'A', size: 100 }] }
};
chart.options({
  encode: { value: 'value' },   // ❌ Field name mismatch
});

// ✅ Correct
chart.options({
  encode: { value: 'size' },    // ✅ Matches the data field
});
```

---

## Node Data Access Rules (Important!)

In the hierarchical chart, the parameter `d` received by the callback function **is not the original data object**, but rather a hierarchical node wrapped by G2 using d3-hierarchy. **The original data is stored in `d.data`**.

### Why Doesn’t `encode.color: 'growth'` Work?

**Root Cause**: When `encode` is a string, G2 internally performs `datum[fieldName]`, directly accessing the node object's property. For hierarchical marks, `datum` is a hierarchy node, not the original data object:

```
d['growth']        → undefined  ❌ (Hierarchy node does not have the 'growth' property)
d.data['growth']   → 3.5        ✅ (Original data is on `d.data`)
```

**Special Case**: `encode.value: 'value'` appears to work with a string because G2 applies **special handling** to the `value` channel for hierarchical marks, directly reading the node's `value` property (computed by d3-hierarchy). Other channels (`color`, `shape`, etc.) lack this special handling, causing the string to directly access `datum[field]`, resulting in `undefined`.

```javascript
// ❌ Internal execution equivalent to `encode.color: 'growth'`:
const color = datum['growth']  // datum is a hierarchy node, 'growth' is not on the node → undefined
// Result: All rectangles use the same color

// ✅ Callback is required for correct access:
const color = datum.data?.['growth']  // datum.data is the original data object
```

### Structure of Callback Parameter d

```javascript
// d is a d3-hierarchy node with the following structure:
{
  value: 100,              // Node value (sum of leaf values calculated by d3)
  depth: 2,                // Hierarchy depth (0 = root node)
  height: 0,               // Subtree height (0 for leaf nodes)
  data: {                  // ← Original data is here!
    name: 'Frontend',
    value: 120,
    growth: 3.5,
    // ... other custom fields
  },
  path: ['root', 'Technology', 'Frontend'],  // Path from root to current node
}
```

### Accessing Fields in encode

```javascript
// ❌ Incorrect: String field names do not work for channels like color/shape, return undefined
encode: {
  value: 'value',   // ✅ value channel has special handling, strings are valid
  color: 'growth',  // ❌ Equivalent to d['growth'] = undefined, all rectangles have the same color
}

// ✅ Correct: All channels except value must use callback functions
encode: {
  value: 'value',
  color: (d) => d.data?.growth,  // ✅ Access the original field via d.data
}
```

### Common Coloring Strategies

```javascript
// Color by parent node (recommended, same category same color, clear visual grouping)
color: (d) => d.path?.[1] || d.data?.name

// Color by depth level
color: (d) => d.depth

// Color by custom field
color: (d) => d.data?.growth
color: (d) => d.data?.category

// Color by value (continuous color palette)
color: (d) => d.value
```

### Customizing Colors with Scale

```javascript
encode: {
  value: 'value',
  color: (d) => d.data?.growth,
},
scale: {
  color: {
    type: 'diverging',
    palette: 'RdYlGn',
    domain: [-5, 0, 5],
  },
}
```

### Error 3: Using String Field Name in encode.color Causes All Rectangles to Have the Same Color

```javascript
// ❌ Incorrect: color: 'growth' is equivalent to d['growth'], hierarchy nodes do not have a 'growth' property → undefined
chart.options({
  type: 'treemap',
  data: { value: data },
  encode: {
    value: 'value',
    color: 'growth',  // ❌ d['growth'] = undefined → all rectangles display the same color
  },
});

// ✅ Correct: color must use a callback function to access the original field via d.data
chart.options({
  type: 'treemap',
  data: { value: data },
  encode: {
    value: 'value',
    color: (d) => d.data?.growth,  // ✅ Color by growth rate
  },
});
```

### Error 4: Using `d.name` in `labels/style` results in `undefined`

```javascript
// ❌ Error: The original field of the treemap node is in `d.data`, `d.name` is undefined
style: {
  labelText: (d) => d.name,  // ❌ `d.name` is undefined
}

// ✅ Correct: Access the original data field through `d.data`
style: {
  labelText: (d) => d.data?.name || '',  // ✅
}
```