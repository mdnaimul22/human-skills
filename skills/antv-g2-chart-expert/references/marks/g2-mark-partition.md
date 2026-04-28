---
id: "g2-mark-partition"
title: "G2 Partition (Rectangular Partition) Chart"
description: |
  The partition mark uses a rectangular (icicle) layout to display hierarchical data, where each level extends downward from the parent node's position, and child nodes fill the parent node's width proportionally based on their values. It uses Cartesian coordinates, with the horizontal axis representing the value domain and the vertical axis representing the hierarchy depth. It is part of the @antv/g2 core and does not require additional extension libraries.
  Note: partition and sunburst are two independent marks and cannot be mixed: partition uses a rectangular layout (Cartesian coordinates), while sunburst uses an annular layout (polar coordinates, from @antv/g2-extension-plot).

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "partition"
  - "rectangular partition"
  - "icicle"
  - "icicle chart"
  - "hierarchical data"
  - "hierarchy"
  - "drillDown"
  - "drill down"

related:
  - "g2-mark-treemap"
  - "g2-mark-sunburst"
  - "g2-interaction-drilldown"
  - "g2-mark-pack"

use_cases:
  - "Rectangular partition display of hierarchical data (e.g., call stack flame graphs, file directory structures)"
  - "Proportional visualization of multi-level categorical data"
  - "Hierarchical structure exploration with drill-down interaction support"

anti_patterns:
  - "Do not use partition to create sunburst charts; use sunburst instead (requires @antv/g2-extension-plot)"
  - "Do not write data as { value: treeRoot }; partition data should be in array form"
  - "Do not access fields using d.data?.name; partition callbacks receive flattened records, so use d.name directly"
  - "All nodes (including root and intermediate nodes) must explicitly set the value field—partition does not automatically sum child nodes; if the root node lacks a value, all rectangles will have a width of 0 and stack at x=0"
  - "Do not use d['ancestor-node'] for branch coloring—this field equals the node's own name; use d.path[1] || d.path[0] for branch coloring"
  - "The return value of the encode.color function is the domain key for the color channel, and scale.color.domain must match the function's actual return values exactly—if the function returns hex color values but the domain contains data names, the Ordinal scale will append the hex values to the domain, causing garbled legend entries like #E63946"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-04-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/graph/hierarchy/#partition"
---

## partition vs sunburst Comparison

| Feature | partition (Rectangle Partition) | sunburst (Sunburst Chart) |
|---------|---------------------------------|---------------------------|
| Source  | `@antv/g2` core, no extension required | `@antv/g2-extension-plot`, requires `extend` |
| Coordinate System | Cartesian (rectangular) | Polar (concentric circles) |
| Visual Form | Rectangle icicle | Concentric rings |
| Data Format | Array `[treeRoot]` | `{ value: treeRoot }` |
| Field Access in Callback | Direct `d.name`, `d.depth`, `d.value` | Direct `d.name`, `d.depth`, `d.path` (string) |

## Minimum Viable Example

Data Structure: Single root array with three fields: `name`/`value`/`children`. **All nodes (including the root and intermediate nodes) must explicitly set `value`**——partition will not automatically accumulate child nodes, and the absence of `value` in the root node will result in all rectangles having a width of 0 and overlapping.

The following mock data simulates annual budget allocation (4 categories, 3 levels deep):

```javascript
import { Chart } from '@antv/g2';

const data = [
  {
    name: 'Annual Budget',
    value: 1550,
    children: [
      {
        name: 'Product R&D',
        value: 600,
        children: [
          {
            name: 'Frontend',
            value: 220,
            children: [
              { name: 'React', value: 90 },
              { name: 'Vue', value: 80 },
              { name: 'CSS', value: 50 },
            ],
          },
          {
            name: 'Backend',
            value: 230,
            children: [
              { name: 'Java', value: 100 },
              { name: 'Python', value: 80 },
              { name: 'Go', value: 50 },
            ],
          },
          {
            name: 'Mobile',
            value: 150,
            children: [
              { name: 'iOS', value: 80 },
              { name: 'Android', value: 70 },
            ],
          },
        ],
      },
      {
        name: 'Marketing',
        value: 400,
        children: [
          {
            name: 'Digital Marketing',
            value: 180,
            children: [
              { name: 'SEO', value: 70 },
              { name: 'SEM', value: 60 },
              { name: 'Social Media', value: 50 },
            ],
          },
          {
            name: 'Brand Promotion',
            value: 130,
            children: [
              { name: 'Design', value: 70 },
              { name: 'Content', value: 60 },
            ],
          },
          {
            name: 'Event Operations',
            value: 90,
            children: [
              { name: 'Online', value: 50 },
              { name: 'Offline', value: 40 },
            ],
          },
        ],
      },
      {
        name: 'Operational Support',
        value: 300,
        children: [
          {
            name: 'Customer Service',
            value: 130,
            children: [
              { name: 'Pre-sales', value: 60 },
              { name: 'After-sales', value: 70 },
            ],
          },
          {
            name: 'Data Analysis',
            value: 100,
            children: [
              { name: 'BI', value: 60 },
              { name: 'Algorithm', value: 40 },
            ],
          },
          {
            name: 'Technical Support',
            value: 70,
            children: [
              { name: 'Operations', value: 40 },
              { name: 'Security', value: 30 },
            ],
          },
        ],
      },
      {
        name: 'Infrastructure',
        value: 250,
        children: [
          {
            name: 'Cloud Computing',
            value: 120,
            children: [
              { name: 'AWS', value: 60 },
              { name: 'Self-built IDC', value: 60 },
            ],
          },
          {
            name: 'Toolchain',
            value: 130,
            children: [
              { name: 'CI/CD', value: 50 },
              { name: 'Monitoring', value: 40 },
              { name: 'Logging', value: 40 },
            ],
          },
        ],
      },
    ],
  },
];

const chart = new Chart({ container: 'container', autoFit: true, height: 400 });

chart.options({
  type: 'partition',
  data,
  encode: {
    value: 'value',
    color: (d) => d.path[1] || d.path[0],
  },
  scale: {
    color: {
      range: [
        'rgb(91, 143, 249)',
        'rgb(90, 216, 166)',
        'rgb(246, 189, 22)',
        'rgb(232, 104, 74)',
        'rgb(154, 100, 220)',
      ],
    },
  },
  labels: [
    {
      text: 'name',
      position: 'inside',
      transform: [{ type: 'overflowHide' }],
    },
  ],
  style: { inset: 0.5 },
  axis: { x: { title: 'Budget (10,000 RMB)' } },
});

chart.render();
```

## Data Format Description

The `data` of `partition` is an **array**, where each item is a tree root node (supports multiple roots).

**Key: All nodes must explicitly set `value`**, the partition layout will not automatically accumulate the values of child nodes. The `value` of non-leaf nodes should equal the sum of the `value` of all its leaf nodes.

```javascript
// ✅ Correct: Root and intermediate nodes explicitly set value
chart.options({
  type: 'partition',
  data: [
    {
      name: 'root',
      value: 300,          // ← Root node must have value (= sum of all leaves)
      children: [
        {
          name: 'A',
          value: 200,      // ← Intermediate nodes must also have value
          children: [
            { name: 'A1', value: 120 },
            { name: 'A2', value: 80 },
          ],
        },
        { name: 'B', value: 100 },
      ],
    },
  ],
});

// ❌ Error: Root node missing value → all rectangles have width 0, stacked at x=0
chart.options({
  type: 'partition',
  data: [{ name: 'root', children: [...] }],   // ❌ Missing value, chart crashes
});

// ❌ Error: Cannot use { value: treeRoot } object wrapper (sunburst syntax)
chart.options({
  type: 'partition',
  data: { value: { name: 'root', children: [...] } },   // ❌ Does not work
});
```

## Data Structure in Callback Functions

`partition` flattens the tree data before rendering. The `d` received in the callback is a **flattened record**, allowing direct field access:

```javascript
// Structure of d (after flattening)
{
  name: 'diffProps',                                    // Node name
  value: 120,                                           // Node value
  depth: 3,                                             // Depth level (root node is 0)
  path: ['main', 'render', 'reconcile', 'diffProps'],  // Path array from root to current node
  'ancestor-node': 'diffProps',  // Note: Equals the node's own name, not the top-level ancestor
  childNodeCount: 0,             // Number of child nodes (0 for leaf nodes)
  x: [x0, x1],                  // Horizontal position range
  y: [y0, y1],                   // Vertical position range (i.e., depth level)
}
```

**Color by Branch (Top-Level Category)**: Use `d.path[1]` (2nd element in path = top-level child name), not `d['ancestor-node']` (which equals the node's own name and has no grouping effect):

```javascript
// ✅ Color by branch (same color for nodes in the same top-level subtree)
encode: { color: (d) => d.path[1] || d.path[0] }
// path[1] is undefined for root nodes, fallback to path[0] (root node's own name)

// ✅ Color by node name (unique color for each node)
encode: { color: 'name' }

// ✅ Color by depth level
encode: { color: (d) => d.depth }

// ❌ Error: ancestor-node equals the node's own name, not the "top-level ancestor"
encode: { color: (d) => d['ancestor-node'] }  // Equivalent to d.name, no grouping effect

// ❌ Error: partition does not use d3-hierarchy wrapping, d.data does not exist
encode: { color: (d) => d.data?.name }
```

## labels Position Selection

- **Shallow Tree (≤ 6 levels)**: Use `position: 'inside'`, text is displayed inside the rectangle, and automatically hidden by `overflowHide` when too narrow
- **Deep Tree (> 6 levels)**: Use `position: 'left'` + `dx: 8`, text starts from the left edge of the rectangle, suitable for scenes with smaller line heights

```javascript
// Shallow Tree (Recommended)
labels: [{ text: 'name', position: 'inside', transform: [{ type: 'overflowHide' }] }]

// Deep Tree (Official example usage, suitable for 10+ levels)
labels: [{ text: 'name', position: 'left', dx: 8, transform: [{ type: 'overflowHide' }] }]
```

## layout Configuration

```javascript
chart.options({
  type: 'partition',
  data: [...],
  encode: { value: 'value', color: 'name' },
  layout: {
    sort: (a, b) => b.value - a.value,  // Sort child nodes in descending order by value
    fillParent: true,                   // Child nodes fill the parent node's width (default true)
    // valueField: 'value',             // Value field name (default 'value')
    // nameField: 'name',               // Name field name (default 'name')
  },
});
```

## Drill-Down Interaction

`partition` comes with a built-in `drillDown` interaction, allowing users to drill down by clicking on a node:

```javascript
chart.options({
  type: 'partition',
  data: [...],
  encode: { value: 'value', color: 'name' },
  interaction: {
    drillDown: true,  // Enabled by default
  },
});
```

## Common Errors and Fixes

### Error 1: Root Node Missing `value` → All Rectangles Stacked at `x=0`

The `partition` layout calculates the root node's width using `node.value` (`x1 = x0 + value`). When the root node's `value` is 0, its width becomes 0, and all child nodes start at `x=0` with widths determined by their respective `value`. This causes severe overlap among sibling nodes.

```javascript
// ❌ Error: Root node without value, child nodes start at x=0, causing overlap
chart.options({
  type: 'partition',
  data: [
    {
      name: 'root',
      // value is missing!
      children: [
        { name: 'A', value: 150 },  // x=[0, 150]
        { name: 'B', value: 200 },  // x=[0, 200] ← Overlaps with A!
      ],
    },
  ],
});

// ✅ Correct: All nodes explicitly set with value
chart.options({
  type: 'partition',
  data: [
    {
      name: 'root',
      value: 350,   // ← Must be present, equal to the sum of all leaf values
      children: [
        { name: 'A', value: 150 },  // x=[0, 150]
        { name: 'B', value: 200 },  // x=[150, 350] ← Correct
      ],
    },
  ],
});
```

### Error 2: Mixing partition and sunburst
```javascript
// ❌ Incorrect: Using partition with polar coordinates to achieve a sunburst chart
chart.options({
  type: 'partition',
  coordinate: { type: 'polar' },  // ❌ partition does not support polar coordinate sunburst charts
});

// ✅ Correct: Sunburst charts should use sunburst (requires @antv/g2-extension-plot)
import { plotlib } from '@antv/g2-extension-plot';
import { Runtime, corelib, extend } from '@antv/g2';
const Chart = extend(Runtime, { ...corelib(), ...plotlib() });

chart.options({
  type: 'sunburst',
  data: { value: treeRoot },  // sunburst uses { value: root } object
  encode: { value: 'sum' },
});
```

### Error 3: Using sunburst object format for data
```javascript
// ❌ Incorrect: partition does not accept { value: root } object
chart.options({
  type: 'partition',
  data: { value: { name: 'root', children: [...] } },
});

// ✅ Correct: partition uses an array, and the root node must explicitly set value
chart.options({
  type: 'partition',
  data: [{ name: 'root', value: 1000, children: [...] }],
});
```

### Error 4: Accessing Fields with `d.data?.name` in `labels`
```javascript
// ❌ Incorrect: d3-hierarchy syntax, partition is flattened, `d.data` does not exist
labels: [{ text: (d) => d.data?.name }]

// ✅ Correct: Directly access the flattened field
labels: [{ text: 'name' }]
labels: [{ text: (d) => d.name }]
```

### Error 5: Misusing ancestor-node for branch coloring
```javascript
// ❌ Incorrect: ancestor-node equals the node's own name, resulting in all nodes having different colors with no grouping effect
encode: { color: (d) => d['ancestor-node'] }

// ✅ Correct: Use path[1] to get the first-level child node name for branch coloring
encode: { color: (d) => d.path[1] || d.path[0] }
```

### Error 6: Mismatch between `encode.color` function return value and `scale.color.domain`

The return value of the `encode.color` function is the **domain key** for the color channel, and `scale.color.domain` must exactly match the value actually returned by the function.

If the function returns a hex color value while the `domain` is filled with data names, the Ordinal scale in `@antv/scale` will **dynamically append** the unknown hex string to the domain, resulting in garbled entries like `#E63946` in the legend.

```javascript
// ❌ Error: Function returns hex color value, but domain is data field name
// Ordinal scale appends '#E63946'/'#BDBDBD' to domain, causing legend to display hex string entries
encode: {
  color: (d) => ['产品研发', '基础设施'].includes(d.path[1]) ? '#E63946' : '#BDBDBD',
},
scale: {
  color: {
    domain: ['产品研发', '市场营销', '运营支持', '基础设施'],  // ❌ Mismatch with function return value
    range: ['#E63946', '#BDBDBD', '#BDBDBD', '#E63946'],
  },
},
// Result: Domain is polluted to ['产品研发', '市场营销', '运营支持', '基础设施', '#E63946', '#BDBDBD']
// Legend displays 6 entries, including '#E63946' and '#BDBDBD' strings

// ✅ Correct: Function returns semantic labels, scale.domain precisely matches return values
encode: {
  color: (d) => ['产品研发', '基础设施'].includes(d.path[1]) ? 'highlight' : 'muted',
},
scale: {
  color: {
    domain: ['highlight', 'muted'],  // ✅ Exact match with function return values
    range: ['#E63946', '#BDBDBD'],
  },
},
// Legend displays only 2 semantic entries with correct color mapping
```

If you do not need a legend and only want to specify color mappings, you can directly use `range` without setting `domain` (leveraging Ordinal's automatic domain collection):

```javascript
// ✅ When legend labels are not needed: Use range directly, allowing Ordinal to automatically collect domain
encode: { color: (d) => d.path[1] || d.path[0] },
scale: {
  color: {
    range: ['rgb(91,143,249)', 'rgb(90,216,166)', 'rgb(246,189,22)', 'rgb(232,104,74)'],
  },
},
```