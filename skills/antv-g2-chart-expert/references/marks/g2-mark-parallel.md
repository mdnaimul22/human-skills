---
id: "g2-mark-parallel"
title: "G2 Parallel Coordinates Mark"
description: |
  Parallel Coordinates Mark. Uses the line mark in conjunction with the parallel coordinate system to display relationships between multi-dimensional data.
  Suitable for scenarios such as multi-dimensional data relationship analysis and data clustering identification.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Parallel Coordinates"
  - "parallel"
  - "Multi-dimensional Data"
  - "Relationship Analysis"

related:
  - "g2-mark-radar"
  - "g2-mark-sankey"

use_cases:
  - "Multi-dimensional Data Relationship Analysis"
  - "Data Clustering Identification"
  - "Feature Engineering"

anti_patterns:
  - "Dimensions < 3 should use scatter plots"
  - "Not suitable for large datasets (>1000)"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/parallel"
---

## Core Concepts

Parallel coordinate systems display multi-dimensional data relationships:
- Use `line` marks
- Combined with `parallel` coordinate systems
- Each line represents multiple dimension values of a data record

**Key Features:**
- Each axis represents a different dimension
- There is no causal relationship between axes
- Axis order can be adjusted

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'line',
  autoFit: true,
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/cars3.json',
  },
  coordinate: { type: 'parallel' },
  encode: {
    position: [
      'economy (mpg)',
      'cylinders',
      'displacement (cc)',
      'power (hp)',
    ],
    color: 'weight (lb)',
  },
  style: {
    lineWidth: 1.5,
    strokeOpacity: 0.4,
  },
});

chart.render();
```

## Common Variants

### Horizontal Layout

```javascript
chart.options({
  type: 'line',
  coordinate: {
    type: 'parallel',
    transform: [{ type: 'transpose' }],
  },
  encode: {
    position: ['dim1', 'dim2', 'dim3'],
    color: 'category',
  },
});
```

### With Interactive Brushing

```javascript
chart.options({
  type: 'line',
  coordinate: { type: 'parallel' },
  data,
  encode: { position: ['A', 'B', 'C', 'D'], color: 'group' },
  interaction: {
    brushAxisHighlight: {
      maskFill: '#d8d0c0',
      maskOpacity: 0.3,
    },
  },
  state: {
    active: { lineWidth: 3, strokeOpacity: 1 },
    inactive: { stroke: '#ccc', opacity: 0.3 },
  },
});
```

### Smooth Curve

```javascript
chart.options({
  type: 'line',
  coordinate: { type: 'parallel' },
  data,
  encode: {
    position: ['A', 'B', 'C'],
    color: 'category',
    shape: 'smooth',  // Smooth Curve
  },
});
```

## Complete Type Reference

```typescript
interface ParallelOptions {
  type: 'line';
  coordinate: {
    type: 'parallel';
    transform?: [{ type: 'transpose' }];
  };
  encode: {
    position: string[];  // Multiple dimension fields
    color?: string;      // Categorical field
  };
  style: {
    lineWidth?: number;
    strokeOpacity?: number;
  };
}
```

## Parallel Coordinates vs. Line Chart

| Feature | Parallel Coordinates | Line Chart |
|------|------------|--------|
| Use Case | Multi-dimensional Relationships | Time Trends |
| Axis Meaning | Different Dimensions | Time Series |
| Line Meaning | One Record | One Metric |

## Common Errors and Fixes

### Error 1: Using the Wrong Coordinate System

```javascript
// ❌ Problem: Using the default coordinate system
coordinate: {}

// ✅ Correct: Using the parallel coordinate system
coordinate: { type: 'parallel' }
```

### Error 2: Incorrect position encoding

```javascript
// ❌ Problem: Using x/y encoding
encode: { x: 'dim1', y: 'dim2' }

// ✅ Correct: Using position array
encode: { position: ['dim1', 'dim2', 'dim3'] }
```

### Error 3: Insufficient Dimensions

```javascript
// ⚠️ Note: It is recommended to have >= 4 dimensions
// 2-3 dimensions should use a scatter plot
```