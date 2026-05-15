---
id: "g2-interaction-brushx-highlight"
title: "G2 BrushXHighlight Interaction"
description: |
  Brush selection and highlight interaction along the X-axis. Users can drag to select a range on the X-axis,
  highlighting data elements within that range.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "highlight"
  - "X-axis"
  - "data exploration"

related:
  - "g2-interaction-brush"
  - "g2-interaction-brushy-highlight"
  - "g2-interaction-brushx-filter"

use_cases:
  - "Time range highlighting"
  - "X-axis range selection highlighting"
  - "Data comparative analysis"

anti_patterns:
  - "Use BrushXFilter instead when data filtering is required"
  - "Use BrushYHighlight instead when Y-axis selection is needed"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction"
---

## Core Concepts

The BrushXHighlight interaction allows users to drag and select a range along the X-axis. Data elements within the selected area are highlighted, while others are dimmed.

**Features:**
- Selection only along the X-axis
- Highlights data instead of filtering
- Suitable for data exploration and comparative analysis

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { category: 'A', value: 100 },
    { category: 'B', value: 150 },
    { category: 'C', value: 80 },
    { category: 'D', value: 200 },
    { category: 'E', value: 120 },
  ],
  encode: {
    x: 'category',
    y: 'value',
  },
  interaction: {
    brushXHighlight: true,
  },
});

chart.render();
```

## Common Variants

### Custom Brush Style

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  interaction: {
    brushXHighlight: {
      brushStyle: {
        fill: '#1890ff',
        fillOpacity: 0.3,
      },
    },
  },
});
```

### Custom Highlight State

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  interaction: {
    brushXHighlight: {
      selectedHandles: ['handle-e', 'handle-w'],  // Displayed drag handles
    },
  },
  state: {
    active: {
      fill: '#1890ff',
      stroke: '#0050b3',
      lineWidth: 2,
    },
    inactive: {
      fillOpacity: 0.3,
    },
  },
});
```

## Complete Type Reference

```typescript
interface BrushXHighlightInteraction {
  brushXHighlight: boolean | {
    brushStyle?: {
      fill?: string;
      fillOpacity?: number;
      stroke?: string;
    };
    selectedHandles?: string[];  // ['handle-e', 'handle-w']
    // Other configurations inherited from BrushHighlight
  };
}
```

## Comparison with BrushHighlight/BrushYHighlight

| Interaction | Selection Direction | Common Use Cases |
|-------------|---------|---------|
| brushHighlight | Any direction | General highlighting |
| brushXHighlight | X direction only | Categorical/time range highlighting |
| brushYHighlight | Y direction only | Numerical range highlighting |

## Differences from BrushXFilter

| Feature          | BrushXHighlight | BrushXFilter |
|------------------|-----------------|--------------|
| Data Processing  | Highlight       | Filter & Hide|
| Non-Selected Data| Dimmed but Visible | Completely Hidden |
| Applicable Scenarios | Data Exploration, Comparison | Data Filtering, Zooming |

## Common Errors and Fixes

### Error 1: Confusion with Filter Interaction

```javascript
// ❌ Incorrect: Using highlight instead of filter
interaction: { brushXHighlight: true }

// ✅ Correct: Choose based on requirements
// Need highlighting: brushXHighlight
// Need filtering: brushXFilter
```

### Error 2: State Style Not Configured

```javascript
// ⚠️ Note: The default highlight effect may not be obvious
// It is recommended to configure state for better visual effects
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  interaction: { brushXHighlight: true },
  state: {
    active: { fill: '#1890ff' },
    inactive: { fillOpacity: 0.2 },
  },
});
```