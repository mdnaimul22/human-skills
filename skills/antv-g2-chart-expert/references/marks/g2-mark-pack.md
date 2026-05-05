---
id: "g2-mark-pack"
title: "G2 Circle Packing (pack)"
description: |
  The pack mark uses circle packing layout to display hierarchical data,
  where parent-child relationships are expressed through the containment of circles, and the size of the circles maps to numerical values.
  The data must be in a tree structure (a nested array containing the children field) or a flat structure with a parent field.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "pack"
  - "circle packing"
  - "hierarchical data"
  - "tree"
  - "nested"

related:
  - "g2-mark-treemap"
  - "g2-core-chart-init"

use_cases:
  - "Displaying size relationships in hierarchical structures (e.g., file directory sizes)"
  - "Showing nested relationships and proportions in categories"
  - "Department sizes in organizational structures"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/other/#pack"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Hierarchical data (tree structure)
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

const chart = new Chart({ container: 'container', width: 600, height: 600 });

chart.options({
  type: 'pack',
  data: {
    value: data,
  },
  encode: {
    value: 'value',   // Leaf node value (determines circle size)
  },
  style: {
    labelFontSize: 11,
    fillOpacity: 0.8,
  },
  legend: false,
});

chart.render();
```

## Data Configuration Format Explanation

**Why does pack use `{ value: data }` instead of `data`?**

In G2 v5, there are two forms of data configuration:

### Abbreviated Form (Array Data Only)

The abbreviated form can be used when the data meets **three conditions**:
1. Inline data
2. **Is an array**
3. No data transformation

```javascript
// ✅ Regular Chart: Data is an array, can use abbreviated form
const arrayData = [
  { genre: 'Sports', sold: 275 },
  { genre: 'Strategy', sold: 115 },
];

chart.options({
  type: 'interval',
  data: arrayData,  // Abbreviated form
});
```

### Full Form (Must Be Used for Hierarchical Data)

Hierarchical data is an **object** (containing `name`/`children`), not an array, and must be used in its full form:

```javascript
// Hierarchical data is an object, not an array
const hierarchyData = {
  name: 'root',
  children: [
    { name: 'A', value: 30 },
    { name: 'B', value: 50 },
  ],
};

// ❌ Wrong: Hierarchical data is not an array, cannot use shorthand
chart.options({
  type: 'pack',
  data: hierarchyData,  // ❌ Does not work
});

// ✅ Correct: Hierarchical data must use the full form
chart.options({
  type: 'pack',
  data: { value: hierarchyData },  // ✅
});
```

### Data Configuration Reference Table

| Data Type | Format | Example |
|---------|------|------|
| Array Data (without transform) | Abbreviated | `data: arrayData` or ` [...]` |
| Array Data (with transform) | Complete | ` { value: [...], transform: [...] }` |
| Hierarchical Data (Object) | Complete | ` { value: { name, children } }` |
| Remote Data | Complete | `data: { type: 'fetch', value: 'url' }` |

---

## Common Errors and Fixes

### Error 1: Directly Passing Tree Object to `data`

```javascript
// ❌ Incorrect: Hierarchical data is not an array, cannot use shorthand form
chart.options({
  type: 'pack',
  data: hierarchyData,   // ❌ Directly passing tree object does not work
});

// ✅ Correct: Hierarchical data must use { value: treeData } form
chart.options({
  type: 'pack',
  data: { value: hierarchyData },  // ✅
});
```

### Error 2: Leaf Nodes Without `value` Field—All Circles Are the Same Size

```javascript
// ❌ Leaf nodes lack a value field, resulting in all nodes being the same size (unable to display differences)
const data = {
  value: {
    name: 'root',
    children: [
      { name: 'A' },  // ❌ No value
      { name: 'B' },
    ],
  }
};

// ✅ Add value field to leaf nodes
const data = {
  value: {
    name: 'root',
    children: [
      { name: 'A', value: 30 },  // ✅
      { name: 'B', value: 50 },
    ],
  }
}
```

### Error 3: Using String Field Name in `encode.color` Causes All Circles to Have the Same Color

```javascript
// ❌ Incorrect: color: 'name' is equivalent to d['name'], hierarchy nodes do not have a 'name' property → undefined
chart.options({
  type: 'pack',
  data: { value: data },
  encode: {
    value: 'value',
    color: 'name',   // ❌ d['name'] = undefined → all circles display the same color
  },
});

// ✅ Correct: color must use a callback function to access the original field via d.data
chart.options({
  type: 'pack',
  data: { value: data },
  encode: {
    value: 'value',
    color: (d) => d.data?.name,           // ✅ Color by the node's own name
    // Or color by the parent node (same category, same color, more intuitive):
    // color: (d) => d.path?.[1] || d.data?.name,
  },
});
```

**Why does `value: 'value'` work as a string, but `color: 'name'` does not?**  
G2 has **special handling** for the `value` channel in hierarchical marks, directly reading the `.value` property computed by d3-hierarchy. However, other channels like `color` and `shape` follow a general path, using the string directly as `datum[field]`, which accesses the hierarchy node instead of the original data. Thus, `datum['name']` naturally results in `undefined`.

### Error 4: Directly using `d.name` in `labels` results in `undefined`

```javascript
// ❌ Error: The original field of the pack node is in `d.data`, `d.name` is undefined
labels: [
  {
    text: (d) => `${d.name}\n${d.value?.toLocaleString()}`,  // ❌ `d.name` is undefined
  },
]

// ✅ Correct: Access the original data field through `d.data`
labels: [
  {
    text: (d) => {
      if (d.height > 0) return '';  // Parent nodes do not display text
      return `${d.data?.name}\n${d.value?.toLocaleString()}`;  // ✅
    },
    position: 'inside',
    fontSize: 10,
    fill: '#000',
  },
]
```

**Root Cause**: In hierarchical charts, G2 encapsulates the original data as hierarchical nodes. The `d` itself is a node object (containing built-in fields such as `depth`, `height`, `value`, etc.), and the entire original data object is stored in `d.data`.

### Error 5: Confusing `data.value` and Node's `value` Field

```javascript
// ⚠️ Note the distinction between the two different `value` fields:
// 1. `data.value` - The value in the data configuration (can be any data type)
// 2. Node's `value` field - The numerical value of the leaf node (determines the circle size)

// ✅ Correct Understanding
chart.options({
  type: 'pack',
  data: {
    value: {           // This is the `value` in the data configuration
      name: 'root',
      children: [
        { name: 'A', value: 30 },  // This is the node's `value` field
      ],
    },
  },
  encode: {
    value: 'value',    // Maps the node's `value` field to the circle size
  },
});
```

---

## Node Data Access Rules (Important!)

In the hierarchical chart, the callback functions (such as `encode`, `labels`'s `text`, etc.) receive a parameter `d` which **is not the original data object**, but rather a hierarchical node wrapped by G2 using d3-hierarchy. **The original data is stored in `d.data`**.

### Why Doesn't `encode.color: 'name'` Work?

**Root Cause**: When `encode` is a string, G2 internally performs `datum[fieldName]`, directly accessing the node object's property. For hierarchical marks, `datum` is a hierarchy node, not the original data object:

```
d['name']        → undefined  ❌ (Hierarchy node does not have a 'name' property)
d.data['name']   → 'Frontend Team'  ✅ (Original data is on `d.data`)
```

**Special Case**: `encode.value: 'value'` appears to work with a string because G2 applies **special handling** to the `value` channel for hierarchical marks, directly reading the node's `value` property (computed by d3-hierarchy). Other channels (`color`, `shape`, etc.) do not have this special handling, and strings will directly use `datum[field]`, resulting in `undefined`.

```javascript
// ❌ Internal execution equivalent to `encode.color: 'name'`:
const color = datum['name']  // datum is a hierarchy node, 'name' property is not on the node → undefined
// Result: All circles use the same color (undefined is mapped to the default color)

// ✅ Correct access using a callback:
const color = datum.data?.['name']  // datum.data is the original data object
```

### Structure of Callback Parameter d

```javascript
// d is a d3-hierarchy node, with the following structure:
{
  value: 100,              // Node value (sum of leaf values calculated by d3)
  depth: 2,                // Hierarchy depth (0 = root node)
  height: 0,               // Subtree height (0 for leaf nodes)
  data: {                  // ← Original data is here!
    name: 'Frontend Team',
    value: 12,
    category: 'tech',
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
  color: 'name',    // ❌ Equivalent to d['name'] = undefined, all circles have the same color
}

// ✅ Correct: All channels except value must use callback functions
encode: {
  value: 'value',
  color: (d) => d.data?.name,  // ✅ Access original field via d.data
}
```

### Accessing Fields in `labels`

```javascript
// ❌ Wrong: d.name is undefined because the original field is in d.data
labels: [
  {
    text: (d) => `${d.name}\n${d.value}`,  // ❌ d.name is undefined
  },
]

// ✅ Correct: Access original fields through d.data
labels: [
  {
    text: (d) => `${d.data?.name}\n${d.value?.toLocaleString()}`,  // ✅
    position: 'inside',
    fontSize: 10,
    fill: '#000',
  },
]
```

### Common Access Patterns

```javascript
// Original fields (name, category, and other custom fields) — Must be accessed via d.data
d.data?.name
d.data?.category
d.data?.type

// Hierarchical node built-in fields (no need for .data) — Can be accessed directly
d.value    // Node value (d3 calculated subtree sum)
d.depth    // Hierarchy depth (0 = root node)
d.height   // Subtree height (leaf nodes are 0)

// Common coloring strategies
color: (d) => d.path?.[1] || d.data?.name   // Color by second-level parent node (recommended, same category, same color)
color: (d) => d.depth                        // Color by hierarchy depth
color: (d) => d.data?.name                   // Color by current node name
color: (d) => d.data?.category               // Color by custom field
color: (d) => d.value                        // Color by value size
```

### Complete Example with Labels

```javascript
chart.options({
  type: 'pack',
  data: { value: data },
  encode: {
    value: 'value',
    color: (d) => d.path?.[1] || d.data?.name,
  },
  style: {
    stroke: '#fff',
    lineWidth: 1,
    fillOpacity: 0.8,
  },
  labels: [
    {
      text: (d) => {
        // Display text only on leaf nodes (height === 0) to avoid parent node text overlap
        if (d.height > 0) return '';
        return `${d.data?.name}\n${d.value?.toLocaleString()}`;
      },
      position: 'inside',
      fontSize: 10,
      fill: '#000',
    },
  ],
  legend: false,
});
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