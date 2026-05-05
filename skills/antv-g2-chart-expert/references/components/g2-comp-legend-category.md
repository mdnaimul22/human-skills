---
id: "g2-comp-legend-category"
title: "G2 Category Legend (LegendCategory)"
description: |
  Category legend component, used to display discrete category legend items.
  It is the most commonly used legend type, suitable for the visualization of categorical data.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "legend"
  - "category"

related:
  - "g2-comp-legend-config"
  - "g2-scale-ordinal"
  - "g2-interaction-legend-filter"

use_cases:
  - "Category legend for bar charts"
  - "Series legend for line charts"
  - "Group legend for scatter plots"

anti_patterns:
  - "Continuous data should use continuous legend (LegendContinuous)"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/component/legend"
---

## Core Concepts

LegendCategory is a categorical legend component:
- Displays discrete category legend items
- Each item contains an icon and a label
- Supports interactions (click to filter, hover to highlight)

**Features:**
- Automatically infers from color/shape channels
- Supports horizontal and vertical layouts
- Supports custom icons

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
    { category: 'A', type: 'X', value: 100 },
    { category: 'A', type: 'Y', value: 150 },
    { category: 'B', type: 'X', value: 120 },
    { category: 'B', type: 'Y', value: 180 },
  ],
  encode: {
    x: 'category',
    y: 'value',
    color: 'type',
  },
  legend: {
    color: {
      position: 'top',
      layout: {
        justifyContent: 'center',
      },
    },
  },
});

chart.render();
```

## Common Variants

### Vertical Layout

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      position: 'right',
      layout: {
        flexDirection: 'column',
      },
    },
  },
});
```

### Custom Label Format

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      labelFormatter: (val) => `Type: ${val}`,
    },
  },
});
```

### Add Title

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      title: 'Type',
      position: 'top',
    },
  },
});
```

### Customizing Chart Icons

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      itemMarker: 'square',  // 'circle' | 'square' | 'line' | ...
      itemMarkerSize: 12,
    },
  },
});
```

### Grid Layout

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      cols: 3,  // Display 3 items per row
      layout: { justifyContent: 'center' },
    },
  },
});
```

### Disable Interaction

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: {
    color: {
      itemMarker: 'circle',
    },
  },
  interaction: {
    legendFilter: false,  // Disable click filtering
  },
});
```

## Complete Type Reference

```typescript
interface LegendCategoryOptions {
  // Position and Layout
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  layout?: {
    flexDirection?: 'row' | 'column';
    justifyContent?: 'flex-start' | 'center' | 'flex-end';
    flexWrap?: 'wrap' | 'nowrap';
  };
  cols?: number;  // Number of columns in grid layout

  // Title
  title?: string | string[];

  // Icon
  itemMarker?: string | ((id: any, index: number) => string);
  itemMarkerSize?: number;
  itemMarkerLineWidth?: number;
  itemSpacing?: number;

  // Label
  labelFormatter?: string | ((val: any) => string);
  maxItemWidth?: number;

  // Style
  style?: {
    fill?: string;
    fontSize?: number;
    // More styles...
  };

  // Other
  dx?: number;
  dy?: number;
}
```

## Differences from Continuous Legends

| Feature | Categorical Legend | Continuous Legend |
|------|---------|---------|
| Data Type | Discrete Categories | Continuous Values |
| Display Method | Icon + Label List | Color Ramp + Scale |
| Interaction | Click to Filter | No Filtering |
| Applicable Scenarios | Categorical Data | Numerical Mapping |

## Common Errors and Fixes

### Error 1: Incorrect `position` Parameter

```javascript
// ❌ Incorrect: `position` should be a predefined value
legend: { color: { position: 'top-left' } }

// ✅ Correct
legend: { color: { position: 'top' } }
```

### Error 2: Unmapped Color Channel

```javascript
// ❌ Incorrect: No color channel, legend will not display
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  legend: { color: { position: 'top' } },
});

// ✅ Correct: Add color channel
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  legend: { color: { position: 'top' } },
});
```

### Error 3: Incorrect itemMarker Type

```javascript
// ❌ Error: itemMarker should be a predefined shape name or a function
legend: { color: { itemMarker: 'triangle-up' } }

// ✅ Correct: Use a supported shape
legend: { color: { itemMarker: 'triangle' } }
// or
legend: { color: { itemMarker: (id, i) => i === 0 ? 'circle' : 'square' } }
```