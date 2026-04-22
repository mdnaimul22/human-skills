---
id: "g2-mark-sunburst"
title: "G2 Sunburst Chart Mark"
description: |
  Sunburst Mark. Use the sunburst mark to display multi-level hierarchical data in a concentric circle format, showcasing hierarchical relationships.
  Suitable for organizational structures, file systems, budget allocation, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Sunburst"
  - "sunburst"
  - "Hierarchy"
  - "Multi-level"

related:
  - "g2-mark-treemap"
  - "g2-mark-arc-pie"

use_cases:
  - "Organizational Structure Display"
  - "File System Analysis"
  - "Budget Allocation"

anti_patterns:
  - "Too many hierarchy levels (>4) should use a treemap instead"
  - "Not suitable for too many categories"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/sunburst"
---

## Core Concepts

The radial chart displays multi-level data through concentric circles:
- Each level is represented by a ring
- The inner and outer radii of the ring indicate the level depth
- The angle size represents the numerical value

**Required Extension:**
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

const chart = new Chart({
  container: 'container',
  theme: 'classic',
  autoFit: true,
});

chart.options({
  type: 'sunburst',
  data: {
    type: 'fetch',
    value: 'https://gw.alipayobjects.com/os/antvdemo/assets/data/sunburst.json',
  },
  encode: {
    value: 'sum',
  },
});

chart.render();
```

## Data Configuration Format Explanation

**Why does sunburst use `{ value: data }` or `{ type: 'fetch', value: 'url' }` instead of `data`?**

Hierarchical data is an **object** (containing name/children), not an array, and must use the full form:

```javascript
// ❌ Error: Hierarchical data is not an array, cannot use shorthand
chart.options({
  type: 'sunburst',
  data: hierarchyData,  // ❌ Does not work
});

// ✅ Correct: Hierarchical data must use the full form
chart.options({
  type: 'sunburst',
  data: { value: hierarchyData },  // ✅ Inline data
});

// ✅ Correct: Remote data
chart.options({
  type: 'sunburst',
  data: { type: 'fetch', value: 'https://example.com/data.json' },
});
```

**Shorthand form is only applicable to array data** (meeting three conditions: inline, is an array, and no transform).

---

## Common Variants

### With Labels

```javascript
chart.options({
  type: 'sunburst',
  data: { value: hierarchyData },
  encode: { value: 'sum' },
  labels: [
    {
      text: 'name',
      transform: [{ type: 'overflowHide' }],
    },
  ],
});
```

### Custom Colors

```javascript
chart.options({
  type: 'sunburst',
  data: { value: hierarchyData },
  encode: {
    value: 'sum',
  },
});
```

### Drill-Down Interaction

```javascript
chart.options({
  type: 'sunburst',
  data: { value: hierarchyData },
  encode: { value: 'sum' },
  interaction: {
    drillDown: {
      breadCrumb: {
        rootText: 'Root',
      },
    },
  },
});
```

## Complete Type Reference

```typescript
interface SunburstOptions {
  type: 'sunburst';
  data: { value: HierarchyData } | { type: 'fetch'; value: string };
  encode: {
    value: string;                          // Numerical field (string is acceptable, with special handling)
    color?: (d: HierarchyNode) => unknown;  // ⚠️ Color must use a callback, cannot be a string
  };
  labels?: Array<{
    text: string;
    transform?: Array<{ type: string }>;
  }>;
  interaction?: {
    drillDown?: {
      breadCrumb?: {
        rootText?: string;
      };
    };
  };
}
```

## Radial Chart vs. Rectangle Tree Map

| Feature       | Radial Chart | Rectangle Tree Map |
|---------------|--------------||--------------------|
| Layout        | Circular     | Rectangular        |
| Space Utilization | Low      | High               |
| Hierarchy Display | Concentric Circles | Nested Rectangles  |
| Suitable Hierarchy Levels | ≤4 Levels | Deeper Levels      |

## Common Errors and Fixes

### Error 1: Extension Not Imported

```javascript
// ❌ Issue: sunburst requires an extension library
import { Chart } from '@antv/g2';

// ✅ Correct: Import the plotlib extension
import { plotlib } from '@antv/g2-extension-plot';
import { Runtime, corelib, extend } from '@antv/g2';
const Chart = extend(Runtime, { ...corelib(), ...plotlib() });
```

### Error 2: Hierarchy Too Deep

```javascript
// ⚠️ Note: When the hierarchy exceeds 4 levels, the outer sectors become too small
// It is recommended to use a rectangular tree map instead
```

### Error 3: Incorrect Data Format

```javascript
// ❌ Issue: Hierarchical data cannot be in shorthand form
chart.options({
  type: 'sunburst',
  [{ name: 'A', value: 100 }],  // ❌ Array format, not hierarchical structure
});

// ✅ Correct: Use full form + nested hierarchical structure
chart.options({
  type: 'sunburst',
  {
    value: {
      name: 'Root',
      children: [
        { name: 'A', value: 100 },
        { name: 'B', children: [...] }
      ]
    }
  },
  encode: { value: 'sum' },
});
```

---

## Node Data Access Rules (Important!)

In the hierarchical chart, the parameter `d` received by the callback function **is not the original data object**, but rather a hierarchical node wrapped by G2 using d3-hierarchy. **The original data is stored in `d.data`**.

### Why doesn’t `encode.color: 'label'` work?

**Root Cause**: When `encode` is a string, G2 internally performs `datum[fieldName]`, directly accessing the hierarchical node's property. Since the hierarchical node does not have a `label` property, it returns `undefined`, causing all sectors to display the same color.

```
d['label']        → undefined  ❌ (Hierarchical node has no label property)
d.data['label']   → 'A类'      ✅ (Original data is on d.data)
```

**Special Case**: `encode.value: 'sum'` works as a string because G2 applies **special handling** to the `value` channel for hierarchical marks. Other channels (`color`, `shape`, etc.) do not have this special handling and must use a callback.
### Structure of Callback Parameter d

```javascript
// d is a d3-hierarchy node with the following structure:
{
  value: 100,              // Node value (sum of subtree calculated by d3)
  depth: 2,                // Hierarchy depth (0 = root node)
  height: 0,               // Subtree height (0 for leaf nodes)
  data: {                  // ← Original data is here!
    name: 'Frontend',
    sum: 120,
    label: 'Category A',
    // ... other custom fields
  },
  path: ['root', 'Technology', 'Frontend'],
}
```

### Accessing Fields in encode

```javascript
// ❌ Incorrect: String field names do not work for the color channel
encode: {
  value: 'sum',    // ✅ value channel has special handling
  color: 'label',  // ❌ d['label'] = undefined → all sectors have the same color
}

// ✅ Correct: color must use a callback function
encode: {
  value: 'sum',
  color: (d) => d.data?.label,  // ✅
}
```

### Common Coloring Strategies

```javascript
// Color by second-level parent node (recommended, same category, same color)
color: (d) => d.path?.[1] || d.data?.name

// Color by hierarchy depth
color: (d) => d.depth

// Color by custom field
color: (d) => d.data?.label
color: (d) => d.data?.category

// Color by numerical value (continuous color palette)
color: (d) => d.value
```

### Error 4: Using a string field name in encode.color results in all sectors having the same color

```javascript
// ❌ Incorrect: color: 'label' is equivalent to d['label'], which does not exist on hierarchical nodes → undefined
chart.options({
  type: 'sunburst',
  data: { value: data },
  encode: {
    value: 'sum',
    color: 'label',  // ❌ → All sectors have the same color
  },
});

// ✅ Correct: color must use a callback to access the original field via d.data
chart.options({
  type: 'sunburst',
  data: { value: data },
  encode: {
    value: 'sum',
    color: (d) => d.path?.[1] || d.data?.name,  // ✅ Color by parent node
  },
});
```