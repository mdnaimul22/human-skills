---
id: "g2-interaction-brushx-filter"
title: "G2 BrushXFilter Interaction"
description: |
  Brush selection and filtering interaction along the X-axis. Users can drag to select a range on the X-axis,
  filtering and displaying data within that range.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "filter"
  - "X-axis"
  - "data filtering"

related:
  - "g2-interaction-brush-filter"
  - "g2-interaction-brushy-filter"
  - "g2-interaction-brushx-highlight"

use_cases:
  - "Time range filtering"
  - "X-axis range selection"
  - "Data zoom and view"

anti_patterns:
  - "Use BrushYFilter instead when Y-axis filtering is required"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction"
---

## Core Concepts

The BrushXFilter interaction allows users to drag and select a range on the X-axis. The chart will automatically filter and display only the data within the selected range.

**Features:**
- Selection is only possible on the X-axis
- Data is automatically filtered after selection
- Supports resetting the selection

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
  data: [
    { date: '2024-01', value: 100 },
    { date: '2024-02', value: 120 },
    { date: '2024-03', value: 150 },
    { date: '2024-04', value: 130 },
    { date: '2024-05', value: 160 },
  ],
  encode: {
    x: 'date',
    y: 'value',
  },
  interaction: {
    brushXFilter: true,
  },
});

chart.render();
```

## Common Variants

### Custom Styles

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  interaction: {
    brushXFilter: {
      brushStyle: {
        fill: '#1890ff',
        fillOpacity: 0.2,
        stroke: '#1890ff',
      },
    },
  },
});
```

### Set Initial Selection Area

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  interaction: {
    brushXFilter: {
      selection: [0.2, 0.8],  // Initial selection area ratio [start, end]
    },
  },
});
```

## Complete Type Reference

```typescript
interface BrushXFilterInteraction {
  brushXFilter: boolean | {
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

## Comparison with BrushFilter/BrushYFilter

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
  brushXFilter: true,
}
```

### Error 2: Incorrect `selection` Parameter Format

```javascript
// ❌ Incorrect: `selection` should be a ratio value [0-1]
interaction: {
  brushXFilter: { selection: ['2024-01', '2024-03'] }
}

// ✅ Correct: Use ratio values
interaction: {
  brushXFilter: { selection: [0.2, 0.6] }
}
```