---
id: "g2-mark-arc-diagram"
title: "G2 Arc Diagram Mark"
description: |
  Arc diagram mark. Uses a combination of line and point to display the link relationship between nodes.
  Suitable for relationship network analysis, social networks, knowledge graphs, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "arc diagram"
  - "relationship graph"
  - "network"

related:
  - "g2-mark-chord"
  - "g2-mark-sankey"

use_cases:
  - "Relationship network analysis"
  - "Social networks"
  - "Knowledge graphs"

anti_patterns:
  - "Hierarchical structures should use tree diagrams"
  - "Not suitable for too many nodes"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/arc-diagram"
---

## Core Concepts

The arc-link diagram visualizes the connections between nodes:
- Nodes are arranged along a linear axis or in a circular layout
- Arcs represent connections between nodes
- Supports both linear and circular layouts

**Key Features:**
- One-dimensional layout approach
- Clearly presents ring and bridge structures
- Node ordering affects visual appearance

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

// Data preprocessing: Calculate arc coordinates
const processData = (nodes, links) => {
  const arcData = [];
  const nodePositions = {};

  nodes.forEach((node, i) => {
    nodePositions[node.id] = i * 15 + 50;
  });

  links.forEach((link) => {
    const sourceX = nodePositions[link.source];
    const targetX = nodePositions[link.target];
    const distance = Math.abs(targetX - sourceX);
    const arcHeight = Math.min(150, distance * 0.1);

    for (let i = 0; i <= 15; i++) {
      const t = i / 15;
      const x = sourceX + (targetX - sourceX) * t;
      const y = 600 - arcHeight * Math.sin(Math.PI * t);
      arcData.push({ x, y, linkId: `${link.source}-${link.target}` });
    }
  });

  return { arcData, nodePositions, nodes };
};

chart.options({
  type: 'view',
  data: { type: 'fetch', value: 'relationship.json' },
  // ... Data processing and rendering
});

chart.render();
```

## Common Variants

### Circular Layout

```javascript
chart.options({
  type: 'view',
  coordinate: { type: 'polar' },  // Polar coordinate system
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'x', y: 'y', series: 'linkId' },
    },
    {
      type: 'point',
      encode: { x: 'angle', y: 'radius', color: 'group' },
    },
  ],
});
```

### With Node Labels

```javascript
chart.options({
  type: 'view',
  children: [
    { type: 'line', data: arcData, encode: { x: 'x', y: 'y', series: 'linkId' } },
    { type: 'point', data: nodeData, encode: { x: 'x', y: 'y', color: 'group' } },
    { type: 'text', data: nodeData, encode: { x: 'x', y: 'y', text: 'name' } },
  ],
});
```

### With Interactive Highlighting

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data: arcData,
      encode: { x: 'x', y: 'y', series: 'linkId' },
      style: { strokeOpacity: 0.4 },
      state: {
        active: { strokeOpacity: 1, lineWidth: 2 },
      },
    },
  ],
  interactions: [{ type: 'elementHighlight' }],
});
```

## Complete Type Reference

```typescript
interface ArcDiagramData {
  nodes: Array<{ id: string; label: string; group?: string }>;
  links: Array<{ source: string; target: string; value?: number }>;
}

// Arc diagrams consist of multiple layers:
// 1. line - arc connections
// 2. point - nodes
// 3. text - labels (optional)
```

## Arc-Length Linkage Chart vs Chord Chart

| Feature | Arc-Length Linkage Chart | Chord Chart |
|------|------------|--------|
| Node Layout | Linear/Circular | Circular |
| Linking Method | Arcs Overlapping | Tiled, Non-Overlapping |
| Applicable Scenarios | Relationship Display | Flow Display |

## Common Errors and Fixes

### Error 1: Nodes Not Sorted

```javascript
// ⚠️ Note: Node sorting affects visual effects
// It is recommended to sort by community or degree
```

### Error 2: Excessive Connections

```javascript
// ⚠️ Note: Excessive connections can lead to visual clutter
// It is recommended to filter or aggregate some connections
```

### Error 3: Missing Data Preprocessing

```javascript
// ❌ Problem: Directly using raw data
 { nodes: [...], links: [...] }

// ✅ Correct: Preprocess to calculate coordinates
data: { transform: [{ type: 'custom', callback: processData }] }
```