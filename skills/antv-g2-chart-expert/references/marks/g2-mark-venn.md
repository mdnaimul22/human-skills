---
id: "g2-mark-venn"
title: "G2 Venn Diagram Mark"
description: |
  Venn Diagram Mark. Uses path marks with venn transformation to display intersections and unions between sets.
  Suitable for user group analysis, product feature comparison, skill overlap analysis, and similar scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Venn Diagram"
  - "venn"
  - "set relationships"
  - "intersection"

related:
  - "g2-mark-chord"
  - "g2-mark-sankey"

use_cases:
  - "User group overlap analysis"
  - "Product feature comparison"
  - "Skill overlap analysis"

anti_patterns:
  - "Number of sets >4 should use other charts"
  - "Not suitable for large value differences"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/venn"
---

## Core Concepts

Venn diagrams display the intersection relationships between sets:
- Use `path` marks
- Combine with `venn` data transformation
- Overlapping areas represent intersections

**Data Format:**
- `sets`: Array of set names
- `size`: Size of the set
- `label`: Display label

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'path',
  data: {
    type: 'inline',
    value: [
      { sets: ['WeChat'], size: 1200, label: 'WeChat' },
      { sets: ['Weibo'], size: 800, label: 'Weibo' },
      { sets: ['WeChat', 'Weibo'], size: 300, label: 'Overlap' },
    ],
    transform: [{ type: 'venn' }],
  },
  encode: {
    d: 'path',
    color: 'key',
  },
  labels: [
    { position: 'inside', text: (d) => d.label || '' },
  ],
  style: {
    opacity: (d) => (d.sets.length > 1 ? 0.3 : 0.7),
  },
});

chart.render();
```

## Common Variants

### Three-Set Venn Diagram

```javascript
chart.options({
  type: 'path',
  data: {
    type: 'inline',
    value: [
      { sets: ['Frontend'], size: 12, label: 'Frontend' },
      { sets: ['Backend'], size: 15, label: 'Backend' },
      { sets: ['Design'], size: 8, label: 'Design' },
      { sets: ['Frontend', 'Backend'], size: 5, label: 'Full Stack' },
      { sets: ['Frontend', 'Design'], size: 3 },
      { sets: ['Backend', 'Design'], size: 2 },
      { sets: ['Frontend', 'Backend', 'Design'], size: 1 },
    ],
    transform: [{ type: 'venn' }],
  },
  encode: { d: 'path', color: 'key' },
});
```

### Hollow Venn Diagram

```javascript
chart.options({
  type: 'path',
  data: {
    type: 'inline',
    value: [...],
    transform: [{ type: 'venn' }],
  },
  encode: {
    d: 'path',
    color: 'key',
    shape: 'hollow',  // Hollow style
  },
  style: {
    lineWidth: 3,
  },
});
```

### With Interaction

```javascript
chart.options({
  type: 'path',
  data: { type: 'inline', value: [...], transform: [{ type: 'venn' }] },
  encode: { d: 'path', color: 'key' },
  state: {
    inactive: { opacity: 0.2 },
    active: { opacity: 0.9 },
  },
  interactions: [{ type: 'elementHighlight' }],
});
```

## Complete Type Reference

```typescript
interface VennData {
  sets: string[];    // Array of set names
  size: number;      // Size of the set
  label?: string;    // Display label
}

interface VennOptions {
  type: 'path';
  data: {
    type: 'inline';
    value: VennData[];
    transform: [{ type: 'venn' }];
  };
  encode: {
    d: 'path';
    color: 'key';
  };
}
```

## Venn Diagram vs Other Charts

| Scenario          | Recommended Chart |
|-------------------|-------------------|
| Set Intersection  | Venn Diagram      |
| Hierarchical Structure | Sunburst Chart   |
| Flow Relationships | Sankey Diagram    |

## Common Errors and Fixes

### Error 1: Missing Venn Transform

```javascript
// ❌ Issue: No Venn transform
data: { type: 'inline', value: [...] }

// ✅ Correct: Add Venn transform
data: { type: 'inline', value: [...], transform: [{ type: 'venn' }] }
```

### Error 2: Excessive Number of Sets

```javascript
// ⚠️ Note: It is recommended to have no more than 4 sets
// More than 5 sets can lead to visual clutter
```

### Error 3: Incorrect encode Configuration

```javascript
// ❌ Issue: Using x/y encoding
encode: { x: 'sets', y: 'size' }

// ✅ Correct: Using d encoding for path
encode: { d: 'path', color: 'key' }
```