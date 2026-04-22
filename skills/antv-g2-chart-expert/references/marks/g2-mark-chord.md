---
id: "g2-mark-chord"
title: "G2 Chord Mark"
description: |
  Create a chord diagram using Chord Mark. Chord diagrams are used to display flow relationships between nodes,
  commonly seen in scenarios such as trade flows, migration data, and capital flows.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Chord Diagram"
  - "Chord"
  - "Relationship Diagram"
  - "Flow Diagram"
  - "Matrix Visualization"

related:
  - "g2-mark-sankey"
  - "g2-mark-link"
  - "g2-coord-polar"

use_cases:
  - "Display trade flows between countries/regions"
  - "Visualize population migration data"
  - "Analyze capital flow relationships"
  - "Show collaboration relationships between departments"

anti_patterns:
  - "Poor visualization with too many nodes (>20)"
  - "Not suitable for displaying simple one-way relationships (use Sankey instead)"
  - "Not suitable for displaying hierarchical data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/relationship/chord"
---

## Core Concepts

Chord Mark is a composite mark in G2 v5 used for drawing chord diagrams:
- **Node**: Polygons on the arc, representing entities
- **Link**: Banded areas connecting nodes, representing flow relationships
- **Layout**: Automatically calculates node positions and link shapes

**Key Configurations:**
- `encode.source`: Source node field of the edge
- `encode.target`: Target node field of the edge
- `encode.value`: Weight field of the edge
- `layout`: Layout configuration (node width, spacing, etc.)

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

// Chord diagram data: nodes + edges
const data = {
  nodes: [
    { key: 'A', name: 'Product A' },
    { key: 'B', name: 'Product B' },
    { key: 'C', name: 'Product C' },
  ],
  links: [
    { source: 'A', target: 'B', value: 100 },
    { source: 'B', target: 'C', value: 80 },
    { source: 'C', target: 'A', value: 60 },
  ],
};

chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: {
    source: 'source',
    target: 'target',
    value: 'value',
  },
});

chart.render();
```

## Common Variants

### With Node Labels

```javascript
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: {
    source: 'source',
    target: 'target',
    value: 'value',
    nodeKey: 'key',  // Node identifier field
  },
  nodeLabels: [
    { text: 'name', position: 'outside', fontSize: 12 },
  ],
});
```

### Custom Layout

```javascript
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: {
    source: 'source',
    target: 'target',
    value: 'value',
  },
  layout: {
    nodeWidthRatio: 0.05,    // Node width ratio (0, 1)
    nodePaddingRatio: 0.1,   // Node padding ratio [0, 1)
    sortBy: 'weight',        // Sorting method: 'id' | 'weight' | 'frequency' | null
  },
});
```

### Custom Styles

```javascript
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: {
    source: 'source',
    target: 'target',
    value: 'value',
    nodeColor: 'key',        // Node color mapping
    linkColor: 'source',     // Link color mapping
  },
  style: {
    node: {
      opacity: 1,
      lineWidth: 1,
    },
    link: {
      opacity: 0.5,
      lineWidth: 1,
    },
  },
});
```

### With Tooltip

```javascript
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: {
    source: 'source',
    target: 'target',
    value: 'value',
  },
  tooltip: {
    node: {
      title: '',
      items: [(d) => ({ name: d.key, value: d.value })],
    },
    link: {
      title: '',
      items: [(d) => ({ name: `${d.source} → ${d.target}`, value: d.value })],
    },
  },
});
```

## Spec Complete Structure Quick Reference

```javascript
chart.options({
  type: 'chord',
  data: {
    // Data (nodes + links structure)
    value: {
      nodes: [...],
      links: [...],
    },
  },
  // Channel mapping
  encode: {
    source: 'source',        // Source node of the edge
    target: 'target',        // Target node of the edge
    value: 'value',          // Weight of the edge
    nodeKey: 'key',          // Node identifier field
    nodeColor: 'key',        // Node color
    linkColor: 'source',     // Link color
  },

  // Layout configuration
  layout: {
    nodeWidthRatio: 0.05,
    nodePaddingRatio: 0.1,
    sortBy: null,            // 'id' | 'weight' | 'frequency' | function
  },

  // Style
  style: {
    node: { opacity: 1, lineWidth: 1 },
    link: { opacity: 0.5, lineWidth: 1 },
    label: { fontSize: 10 },
  },

  // Labels
  nodeLabels: [{ text: 'name', position: 'outside' }],
  linkLabels: [],

  // Tooltip
  tooltip: { ... },

  // Animation
  animate: {
    node: { enter: { type: 'fadeIn' } },
    link: { enter: { type: 'fadeIn' } },
  },
});
```

## Complete Type Reference

```typescript
interface ChordSpec {
  type: 'chord';
  data: {
    value: {
      nodes: Array<{ key: string; [key: string]: any }>;
      links: Array<{ source: string; target: string; value: number; [key: string]: any }>;
    };
  }
  encode?: {
    source?: string;
    target?: string;
    value?: string;
    nodeKey?: string;
    nodeColor?: string;
    linkColor?: string;
  };
  layout?: {
    nodeWidthRatio?: number;   // (0, 1), default: 0.05
    nodePaddingRatio?: number; // [0, 1), default: 0.1
    sortBy?: 'id' | 'weight' | 'frequency' | ((data: any) => any) | null;
  };
  style?: {
    node?: { opacity?: number; lineWidth?: number; fill?: string };
    link?: { opacity?: number; lineWidth?: number; fill?: string };
    label?: { fontSize?: number; fill?: string };
  };
  nodeLabels?: LabelOption[];
  linkLabels?: LabelOption[];
  tooltip?: TooltipOption;
  animate?: AnimateOption;
}
```

## Common Errors and Fixes

### Error 1: Incorrect Data Format

```javascript
// ❌ Incorrect: Using a flat array
chart.options({
  type: 'chord',
  data: [
    { source: 'A', target: 'B', value: 100 },
  ],
});

// ✅ Correct: Using nodes + links structure
chart.options({
  type: 'chord',
  data: {
    value: {
      nodes: [{ key: 'A' }, { key: 'B' }],
      links: [{ source: 'A', target: 'B', value: 100 }],
    }
  },
  encode: { source: 'source', target: 'target', value: 'value' },
});
```

### Error 2: Mismatched Node Keys

```javascript
// ❌ Error: source/target in links do not match keys in nodes
const data = {
  nodes: [{ key: 'ProductA' }],
  links: [{ source: 'A', target: 'B', value: 100 }],  // 'A' ≠ 'ProductA'
};

// ✅ Correct: Ensure consistent keys
const data = {
  nodes: [{ key: 'A' }, { key: 'B' }],
  links: [{ source: 'A', target: 'B', value: 100 }],
};
```

### Error 3: Missing Value Encoding

```javascript
// ❌ Incorrect: Weight field not specified
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: { source: 'source', target: 'target' },
});

// ✅ Correct: Value field specified
chart.options({
  type: 'chord',
  data: {
    value: data
  },
  encode: { source: 'source', target: 'target', value: 'value' },
});
```