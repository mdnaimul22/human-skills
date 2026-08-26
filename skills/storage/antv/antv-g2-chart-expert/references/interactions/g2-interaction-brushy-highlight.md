---
id: "g2-interaction-brushy-highlight"
title: "G2 BrushYHighlight Interaction"
description: |
  Brush selection and highlight interaction in the Y-axis direction. Users can drag to select a Y-axis range,
  highlighting data elements within that range.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "brush"
  - "highlight"
  - "Y-axis"
  - "data exploration"

related:
  - "g2-interaction-brush"
  - "g2-interaction-brushx-highlight"
  - "g2-interaction-brushy-filter"

use_cases:
  - "Numeric range highlighting"
  - "Y-axis range selection highlighting"
  - "Outlier identification"

anti_patterns:
  - "Use BrushYFilter instead when data filtering is required"
  - "Use BrushXHighlight instead when X-axis selection is needed"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction"
---

## Core Concepts

The BrushYHighlight interaction allows users to drag and select a range along the Y-axis. Data elements within the selected area are highlighted, while others are dimmed.

**Features:**
- Selection is only possible along the Y-axis
- Highlights data instead of filtering it
- Suitable for exploring data within numerical ranges

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
    brushYHighlight: true,
  },
});

chart.render();
```

## Common Variants

### Custom Brush Style

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: {
    brushYHighlight: {
      brushStyle: {
        fill: '#52c41a',
        fillOpacity: 0.3,
      },
    },
  },
});
```

### Custom Highlight State

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: {
    brushYHighlight: {
      selectedHandles: ['handle-n', 'handle-s'],  // Displayed drag handles
    },
  },
  state: {
    active: {
      fill: '#52c41a',
      r: 8,
    },
    inactive: {
      fillOpacity: 0.3,
    },
  },
});
```

## Complete Type Reference

```typescript
interface BrushYHighlightInteraction {
  brushYHighlight: boolean | {
    brushStyle?: {
      fill?: string;
      fillOpacity?: number;
      stroke?: string;
    };
    selectedHandles?: string[];  // ['handle-n', 'handle-s']
    // Other configurations inherited from BrushHighlight
  };
}
```

## Comparison with BrushHighlight/BrushXHighlight

| Interaction | Selection Direction | Common Use Cases |
|-------------|---------|---------|
| brushHighlight | Any direction | General highlighting |
| brushXHighlight | X direction only | Categorical/time range highlighting |
| brushYHighlight | Y direction only | Numerical range highlighting |

## Differences from BrushYFilter

| Feature          | BrushYHighlight | BrushYFilter |
|------------------|-----------------|--------------|
| Data Processing  | Highlight       | Filter & Hide|
| Non-Selected Data| Dimmed but Visible | Completely Hidden |
| Applicable Scenarios | Data Exploration, Comparison | Data Filtering, Zooming |

## Common Errors and Fixes

### Error 1: Confusion with Filter Interaction

```javascript
// ❌ Incorrect: Using highlight instead of filtering data
interaction: { brushYHighlight: true }

// ✅ Correct: Choose based on requirements
// Need highlighting: brushYHighlight
// Need filtering: brushYFilter
```

### Error 2: State Style Not Configured

```javascript
// ⚠️ Note: Default highlight effect may not be obvious
// It is recommended to configure state for better visual effects
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  interaction: { brushYHighlight: true },
  state: {
    active: { fill: '#52c41a', r: 8 },
    inactive: { fillOpacity: 0.2 },
  },
});
```