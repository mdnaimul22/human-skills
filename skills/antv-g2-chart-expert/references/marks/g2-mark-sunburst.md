---
id: "g2-mark-sunburst"
title: "G2 Sunburst"
description: |
  The sunburst mark uses concentric circles (polar coordinates) to display multi-level hierarchical data, from the @antv/g2-extension-plot extension library.
  The radial depth of the rings represents the hierarchy, and the arc angle represents the value size.
  Note: sunburst and partition are two separate marks:
  sunburst is a circular layout (polar coordinates, requires extension), and partition is a rectangular icicle layout (Cartesian coordinates, @antv/g2 core).

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Sunburst"
  - "sunburst"
  - "Hierarchy"
  - "Multi-level"
  - "hierarchy"
  - "polar"
  - "g2-extension-plot"

related:
  - "g2-mark-partition"
  - "g2-mark-treemap"
  - "g2-mark-arc-pie"

use_cases:
  - "Organizational structure display"
  - "File system analysis"
  - "Hierarchical proportion of budget allocation"

anti_patterns:
  - "Hierarchy too deep (>4 levels) should use treemap or partition"
  - "Do not use type: 'partition' with polar coordinates to replace sunburst, use sunburst directly"
  - "Do not write data as an array, sunburst's data is a { value: treeRoot } object"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-04-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/sunburst"
---

## partition vs sunburst Comparison

| Feature | sunburst (Sunburst Chart) | partition (Rectangular Partition) |
|---------|----------------------------------|-----------------------------------|
| Source  | `@antv/g2-extension-plot`, requires `extend` | `@antv/g2` core, no extension needed |
| Coordinate System | Polar (concentric circles) | Cartesian (rectangular) |
| Visual Form | Concentric rings | Rectangular icicle |
| data Format | `{ value: treeRoot }` or fetch | Array `[treeRoot]` or fetch |
| Path in Callback | `d.path` is a **string** `'A / B / C'` | `d.path` is an **array** `['A', 'B', 'C']` |

## Import Extensions (Required)

```javascript
import { plotlib } from '@antv/g2-extension-plot';
import { Runtime, corelib, extend } from '@antv/g2';

const Chart = extend(Runtime, { ...corelib(), ...plotlib() });
```

## Minimum Viable Example

```javascript
import { plotlib } from '@antv/g2-extension-plot';
import { Runtime, corelib, extend } from '@antv/g2';

const Chart = extend(Runtime, { ...corelib(), ...plotlib() });

const chart = new Chart({ container: 'container', autoFit: true });

chart.options({
  type: 'sunburst',
  data: {
    type: 'fetch',
    value: 'https://gw.alipayobjects.com/os/antvdemo/assets/data/sunburst.json',
  },
  encode: { value: 'sum' },
  labels: [
    {
      text: 'name',
      transform: [{ type: 'overflowHide' }],
    },
  ],
});

chart.render();
```

## Data Format Description

The `data` for `sunburst` is a `{ value: treeRoot }` object (single tree), not an array:

```javascript
// ✅ Correct: Inline data, single tree root object
chart.options({
  type: 'sunburst',
  data: {
    value: {
      name: 'root',
      children: [
        { name: 'Group 1', children: [{ name: 'Group 1-1', sum: 100 }] },
        { name: 'Group 2', sum: 200 },
      ],
    },
  },
  encode: { value: 'sum' },
});

// ✅ Correct: Remote fetch
chart.options({
  type: 'sunburst',
  data: { type: 'fetch', value: 'https://example.com/tree.json' },
  encode: { value: 'sum' },
});

// ❌ Incorrect: Cannot directly pass an array (partition syntax)
chart.options({
  type: 'sunburst',
  data: [{ name: 'root', children: [...] }],  // ❌ Does not work
});
```

## Data Structure in Callback Functions

After sunburst flattening, the structure of `d` in the callback:

```javascript
{
  name: 'Group1-1',             // Node name
  value: 100,                   // Node value (subtree summary)
  depth: 2,                     // Hierarchy depth (root node is 1)
  path: 'Group1 / Group1-1',    // ← Path is a string (separated by /)
  'ancestor-node': 'Group1',    // First-level ancestor node name
  x: [x0, x1],
  y: [y0, y1],
}
```

**Note**: `path` is a **string**, separated by ` / `, which is different from the array in partition.

## encode coloring strategy

After sunburst flattening, built-in fields (`name`, `depth`, `path`, `ancestor-node`) can be specified using strings;
Custom fields from the original data are not in the flattened records and need to be derived using a callback via `path`:

```javascript
// ✅ Default coloring (by ancestor-node, same category same color)
encode: { value: 'sum' }  // color defaults to 'ancestor-node'

// ✅ Color by name field (built-in field, string can be used)
encode: { value: 'sum', color: 'name' }

// ✅ Color by the first two levels of the path (callback)
encode: {
  value: 'sum',
  color: (d) => {
    const parts = d.path.split(' / ');
    return [parts[0], parts[1]].join('/');
  },
}

// ✅ Color by depth level
encode: { value: 'sum', color: (d) => d.depth }
```

## Polar Coordinate Customization

```javascript
// Adjust inner and outer radius
chart.options({
  type: 'sunburst',
  data: { value: treeData },
  encode: { value: 'sum' },
  coordinate: {
    type: 'polar',
    innerRadius: 0.3,   // default 0.2
    outerRadius: 0.9,
  },
});

// Revert to Cartesian coordinates (results in a rectangular layout similar to partition, but using partition is more appropriate)
coordinate: { type: 'cartesian' }
```

## Drill-Down Interaction

```javascript
chart.options({
  type: 'sunburst',
  data: { value: treeData },
  encode: { value: 'sum' },
  interaction: {
    drillDown: {
      breadCrumb: {
        rootText: 'Total Name',
        style: { fontSize: '14px', fill: '#333' },
        active: { fill: 'red' },
      },
      isFixedColor: true,   // Maintain original color after drill-down
    },
  },
});
```

## Common Errors and Fixes

### Error 1: Extension Library Not Imported
```javascript
// ❌ Error: Directly using Chart from '@antv/g2', sunburst is not registered
import { Chart } from '@antv/g2';
chart.options({ type: 'sunburst', ... });  // ❌ Unknown mark type: sunburst

// ✅ Correct: Register plotlib via extend
import { plotlib } from '@antv/g2-extension-plot';
import { Runtime, corelib, extend } from '@antv/g2';
const Chart = extend(Runtime, { ...corelib(), ...plotlib() });
```

### Error 2: Using Array Format with `partition` in `data`
```javascript
// ❌ Incorrect: Sunburst does not accept arrays
chart.options({
  type: 'sunburst',
  data: [{ name: 'root', children: [...] }],
});

// ✅ Correct: Sunburst uses a `{ value: root }` object
chart.options({
  type: 'sunburst',
  data: { value: { name: 'root', children: [...] } },
});
```

### Error 3: Treating `path` as an Array
```javascript
// ❌ Incorrect: `path` in sunburst is a string
color: (d) => d.path[1]          // Retrieves the 2nd character, not the 2nd level path

// ✅ Correct: Split first
color: (d) => d.path.split(' / ')[1]
```