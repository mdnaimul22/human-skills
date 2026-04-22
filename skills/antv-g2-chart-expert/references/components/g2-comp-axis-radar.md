---
id: "g2-comp-axis-radar"
title: "G2 Radar Chart Axis (AxisRadar)"
description: |
  A dedicated axis component for radar charts. It displays multiple dimension axes and scales in a polar coordinate system,
  and is one of the core components of radar charts.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "axis"
  - "radar chart"
  - "polar coordinates"
  - "axis"

related:
  - "g2-coord-polar"
  - "g2-mark-radar"
  - "g2-comp-axis-config"

use_cases:
  - "Multi-dimensional display of radar charts"
  - "Axis in polar coordinate system"
  - "Performance evaluation charts"

anti_patterns:
  - "Not applicable to Cartesian coordinate system charts"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/component/axis"
---

## Core Concepts

AxisRadar is a specialized coordinate axis component for radar charts:
- Displays radial axes in a polar coordinate system
- Supports axis labels for multiple dimensions
- Automatically calculates axis angles and positions

**Features:**
- Automatically connects axes to form a grid
- Supports custom axis styles
- Works in conjunction with the polar coordinate system

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'line',
  coordinate: { type: 'polar' },
  data: [
    { item: 'Design', score: 70 },
    { item: 'Development', score: 60 },
    { item: 'Marketing', score: 50 },
    { item: 'Sales', score: 80 },
    { item: 'Support', score: 90 },
  ],
  encode: {
    x: 'item',
    y: 'score',
  },
  axis: {
    x: {
      // Radar chart X-axis configuration
      title: false,
      tickLine: null,
    },
    y: {
      // Radar chart Y-axis (radial axis)
      title: 'Score',
      grid: true,
      gridConnect: 'line',  // Grid connection method
    },
  },
});

chart.render();
```

## Common Variants

### Custom Grid Style

```javascript
chart.options({
  type: 'line',
  coordinate: { type: 'polar' },
  data,
  encode: { x: 'item', y: 'score' },
  axis: {
    y: {
      grid: true,
      gridConnect: 'line',
      gridLineWidth: 1,
      gridStroke: '#e8e8e8',
      gridType: 'line',
    },
  },
});
```

### Hide Axis Lines

```javascript
chart.options({
  type: 'line',
  coordinate: { type: 'polar' },
  data,
  encode: { x: 'item', y: 'score' },
  axis: {
    x: { line: null },
    y: { line: null },
  },
});
```

### Custom Labels

```javascript
chart.options({
  type: 'line',
  coordinate: { type: 'polar' },
  data,
  encode: { x: 'item', y: 'score' },
  axis: {
    x: {
      labelFormatter: (val) => val.toUpperCase(),
      labelSpacing: 10,
    },
    y: {
      labelFormatter: (val) => `${val}%`,
    },
  },
});
```

## Complete Type Reference

```typescript
interface AxisRadarOptions {
  // Basic Configuration
  title?: string | { text: string; style?: object };
  tickLine?: null | { length?: number; style?: object };
  line?: null | { style?: object };

  // Label Configuration
  labelFormatter?: string | ((val: any) => string);
  labelSpacing?: number;
  labelStyle?: object;

  // Grid Configuration
  grid?: boolean;
  gridConnect?: 'line' | 'curve';  // Grid connection method
  gridLineWidth?: number;
  gridStroke?: string;
  gridType?: 'line' | 'circle';

  // Radar Chart Specific
  radar?: {
    count: number;   // Number of axes
    index: number;   // Index of the current axis
  };
}
```

## Differences from Ordinary Axes

| Feature | Ordinary Axes | Radar Chart Axes |
|---------|----------------|------------------|
| Coordinate System | Cartesian | Polar |
| Axis Direction | Horizontal/Vertical | Radial |
| Grid | Rectangular | Polygonal/Circular |
| Label Position | Both ends of the axis | Outer side of the axis end |

## Common Errors and Fixes

### Error 1: Failure to Use Polar Coordinate System

```javascript
// ❌ Incorrect: Radar chart axes require a polar coordinate system
chart.options({
  type: 'line',
  data,
  encode: { x: 'item', y: 'score' },
  axis: { y: { gridConnect: 'line' } },
});

// ✅ Correct: Add polar coordinate system
chart.options({
  type: 'line',
  coordinate: { type: 'polar' },
  data,
  encode: { x: 'item', y: 'score' },
  axis: { y: { gridConnect: 'line' } },
});
```

### Error 2: Incorrect `gridConnect` Parameter

```javascript
// ❌ Error: `gridConnect` only supports 'line' or 'curve'
axis: { y: { gridConnect: 'polygon' } }

// ✅ Correct
axis: { y: { gridConnect: 'line' } }
```