---
id: "g2-interaction-brushy-filter"
title: "G2 BrushYFilter Interaction"
description: |
  Brush filtering interaction in the Y-axis direction. Users can drag to select a Y-axis range,
  filtering and displaying data within that range.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "filter"
  - "Y-axis"
  - "data filtering"

related:
  - "g2-interaction-brush-filter"
  - "g2-interaction-brushx-filter"
  - "g2-interaction-brushy-highlight"

use_cases:
  - "Numerical range filtering"
  - "Y-axis range selection"
  - "Filtering outliers"

anti_patterns:
  - "Use BrushXFilter instead when X-axis direction filtering is required"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction"
---

## Core Concepts

The BrushYFilter interaction allows users to drag and select a range on the Y-axis. The chart will automatically filter and display only the data within the selected range.

**Features:**
- Selection is only possible on the Y-axis
- Data is automatically filtered after selection
- Suitable for numerical range filtering

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'point',
  data: [
    { x: 10, y: 100 },
    { x: 20, y: 150 },
    { x: 30, y: 80 },
    { x: 40, y: 200 },
    { x: 50, y: 120 },
  ],
  encode: {
    x: 'x',
    y: 'y',
  },
  interaction: {
    brushYFilter: true,
  },
});

chart.render();
```

## Common Variants

### Custom Styles

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: {
    brushYFilter: {
      brushStyle: {
        fill: '#52c41a',
        fillOpacity: 0.2,
        stroke: '#52c41a',
      },
    },
  },
});
```

### Set Initial Selection Area

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: {
    brushYFilter: {
      selection: [0.3, 0.7],  // Initial selection ratio [start, end]
    },
  },
});
```

## Complete Type Reference

```typescript
interface BrushYFilterInteraction {
  brushYFilter: boolean | {
    brushStyle?: {
      fill?: string;
      fillOpacity?: number;
      stroke?: string;
      lineWidth?: number;
    };
    selection?: [number, number];  // [startRatio, endRatio]
    // Other configurations inherited from BrushFilter
  };
}
```

## Comparison with BrushFilter/BrushXFilter

| Interaction | Selection Direction | Common Use Cases |
|-------------|---------|---------|
| brushFilter | Any direction | General filtering |
| brushXFilter | X direction only | Time range filtering |
| brushYFilter | Y direction only | Numerical range filtering |

## Common Errors and Fixes

### Error 1: Conflict with Other Brush Interactions

```javascript
// ❌ Incorrect: Enabling multiple brush interactions simultaneously may cause conflicts
interaction: {
  brushXFilter: true,
  brushYFilter: true,
}

// ✅ Correct: Choose one based on requirements
interaction: {
  brushYFilter: true,
}
```

### Error 2: Incorrect `selection` Parameter Format

```javascript
// ❌ Incorrect: `selection` should be a ratio value [0-1]
interaction: {
  brushYFilter: { selection: [100, 200] }
}

// ✅ Correct: Use ratio values
interaction: {
  brushYFilter: { selection: [0.2, 0.6] }
}
```