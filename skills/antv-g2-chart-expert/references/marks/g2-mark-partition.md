---
id: "g2-mark-partition"
title: "G2 Sunburst / Rectangular Partition (partition)"
description: |
  The partition mark uses rectangular partitioning to display hierarchical data, with each layer extending from the parent node, and child nodes filling the width of the parent node.
  Combined with polar coordinates, it can create a sunburst chart—a hierarchical visualization in the form of concentric rings.
  Supports drillDown interaction for hierarchical drilling.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "partition"
  - "sunburst"
  - "hierarchical data"
  - "rectangular partition"
  - "drilldown"

related:
  - "g2-mark-treemap"
  - "g2-interaction-drilldown"
  - "g2-mark-pack"

use_cases:
  - "Sunburst chart to display proportional hierarchical categories (e.g., file directories)"
  - "Hierarchical visualization of organizational structures"
  - "Proportional display of multi-level categorical data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/other/#sunburst"
---

## Minimum Viable Example (Sunburst Chart)

```javascript
import { Chart } from '@antv/g2';

const data = {
  name: 'Total',
  children: [
    {
      name: 'Technology',
      children: [
        { name: 'Frontend', value: 15 },
        { name: 'Backend', value: 20 },
        { name: 'Algorithm', value: 10 },
      ],
    },
    {
      name: 'Product',
      children: [
        { name: 'Product Manager', value: 8 },
        { name: 'User Research', value: 5 },
      ],
    },
    {
      name: 'Design',
      children: [
        { name: 'UX', value: 7 },
        { name: 'Visual', value: 6 },
      ],
    },
  ],
};

const chart = new Chart({ container: 'container', width: 600, height: 600 });

chart.options({
  type: 'sunburst',   // Sunburst chart = partition + polar coordinates (G2 built-in alias)
  data: { value: data },
  encode: {
    value: 'value',   // Leaf node value
  },
  style: {
    fillOpacity: 0.9,
    lineWidth: 1,
    stroke: '#fff',
  },
  interaction: { drillDown: true },  // Optional: Enable drill-down
});

chart.render();
```

## Data Configuration Format Explanation

**Why do `partition/sunburst` use `{ value: data }` instead of `data`?**

Hierarchical data is an **object** (containing `name/children`), not an array, and must use the full form:

```javascript
// ❌ Error: Hierarchical data is not an array, cannot use shorthand
chart.options({
  type: 'partition',
  hierarchyData,  // ❌ Does not work
});

// ✅ Correct: Hierarchical data must use the full form
chart.options({
  type: 'partition',
  data: { value: hierarchyData },  // ✅
});
```

**Shorthand form is only applicable to array data** (meeting three conditions: inline, is an array, and has no transform).

---

## Rectangle Partition Chart (Without Polar Coordinates)

```javascript
chart.options({
  type: 'partition',   // Rectangle partition (not a sunburst chart)
  data: { value: data },
  encode: {
    value: 'value',   // Leaf node value
  },
  layout: {
    valueField: 'value',   // Field determining node width
    sort: (a, b) => b.value - a.value,  // Sort in descending order by value
  },
  style: {
    fillOpacity: 0.85,
    stroke: '#fff',
    lineWidth: 1,
  },
});
```

## Common Errors and Fixes

### Error: Directly passing tree object to data without hierarchy wrapper
```javascript
// ❌ Incorrect
chart.options({
  type: 'sunburst',
  data: treeData,   // ❌ Directly passing tree data
});

// ✅ Correct: Needs to be placed in data.value
chart.options({
  type: 'sunburst',
  data: { value: treeData },  // ✅
});
```

---

## Node Data Access Rules (Important!)

In the hierarchical chart, the parameter `d` received by the callback function **is not the original data object**, but rather a hierarchical node wrapped by G2 using d3-hierarchy. **The original data is stored in `d.data`**.

### Why doesn’t `encode.color: 'category'` work?

**Root Cause**: When `encode` is a string, G2 internally performs `datum[fieldName]`, directly accessing the hierarchy node property. The hierarchy node does not have a `category` property, so it returns `undefined`, causing all areas to display the same color.

```
d['category']        → undefined   ❌ (Hierarchy node has no category property)
d.data['category']   → '技术'      ✅ (Original data is on d.data)
```

**Special Case**: `encode.value: 'value'` works as a string because G2 has **special handling** for the `value` channel of hierarchical marks. Other channels (`color`, `shape`, etc.) do not have this special handling and must use a callback.
### Structure of Callback Parameter d

```javascript
// d is a d3-hierarchy node with the following structure:
{
  value: 100,              // Node value (sum of subtree calculated by d3)
  depth: 2,                // Hierarchy depth (0 = root node)
  height: 0,               // Subtree height (0 for leaf nodes)
  data: {                  // ← Original data is here!
    name: 'Frontend',
    value: 15,
    category: 'Technology',
    // ... Other custom fields
  },
  path: ['root', 'Technology', 'Frontend'],
}
```

### Accessing Fields in encode

```javascript
// ❌ Incorrect: String field names do not work for the color channel
encode: {
  value: 'value',      // ✅ value channel has specialized handling
  color: 'category',   // ❌ d['category'] = undefined → all areas have the same color
}

// ✅ Correct: color must use a callback function
encode: {
  value: 'value',
  color: (d) => d.data?.category,  // ✅
}
```

### Common Coloring Strategies

```javascript
// Color by the second-level parent node (recommended, same category, same color)
color: (d) => d.path?.[1] || d.data?.name

// Color by hierarchy depth
color: (d) => d.depth

// Color by custom field
color: (d) => d.data?.category
color: (d) => d.data?.type

// Color by numerical value (continuous color palette)
color: (d) => d.value
```

### Error 2: Using String Field Name in encode.color Causes All Sectors to Have the Same Color

```javascript
// ❌ Incorrect: color: 'category' is equivalent to d['category'], which does not exist on the hierarchy node → undefined
chart.options({
  type: 'sunburst',
  data: { value: data },
  encode: {
    value: 'value',
    color: 'category',  // ❌ → All sectors have the same color
  },
});

// ✅ Correct: color must use a callback to access the original field via d.data
chart.options({
  type: 'sunburst',
  data: { value: data },
  encode: {
    value: 'value',
    color: (d) => d.path?.[1] || d.data?.name,  // ✅ Color by parent node
  },
});
```

### Error 3: Using `d.name` in `labels` results in `undefined`

```javascript
// ❌ Error: The original field of the partition node is in `d.data`, `d.name` is undefined
labels: [
  {
    text: (d) => d.name,  // ❌ `d.name` is undefined
  },
]

// ✅ Correct: Access the original data field through `d.data`
labels: [
  {
    text: (d) => d.data?.name || '',  // ✅
  },
]
```

### Customizing Colors with Scale

```javascript
encode: {
  value: 'value',
  color: (d) => d.data?.category,
},
scale: {
  color: {
    type: 'sequential',
    palette: 'blues',
  },
}
```