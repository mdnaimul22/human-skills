---
id: "g2-comp-legend-continuous"
title: "G2 Continuous Legend (legendContinuous)"
description: |
  Continuous legend is used to display the mapping relationship between continuous values and colors, commonly seen in heatmaps, geographic visualizations, and other scenarios.
  It supports two forms: ribbon and block, and allows configuration of label formatting, range, etc.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "legend"
  - "continuous legend"
  - "ribbon"
  - "color legend"
  - "heatmap"

related:
  - "g2-comp-legend-config"
  - "g2-comp-legend-category"
  - "g2-scale-sequential"

use_cases:
  - "Color mapping explanation for heatmaps"
  - "Value range legend for geographic visualizations"
  - "Color encoding for continuous values"

anti_patterns:
  - "Categorical data should use categorical legend (legendCategory)"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/legend"
---

## Core Concepts

Continuous Legend displays the mapping of continuous numerical values to visual channels (usually color):
- When `encode.color` is mapped to a continuous numerical field, the legend automatically becomes a continuous legend
- Supports linear scale (linear), threshold scale (threshold), and quantile/quantize scale (quantile/quantize)
- Defaults to a ribbon display

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = Array.from({ length: 100 }, (_, i) => ({
  x: i % 10,
  y: Math.floor(i / 10),
  value: Math.random() * 100,
}));

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },  // value is a continuous numerical value
  scale: { color: { palette: 'Blues' } },
  legend: {
    color: {
      position: 'right',
      length: 200,
      labelFormatter: (v) => Number(v).toFixed(0),  // Note: v might be a string, so conversion is needed
    },
  },
});

chart.render();
```

## Complete Configuration Options

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  legend: {
    color: {
      // ── Position ─────────────────────────────────
      position: 'right',       // 'top' | 'bottom' | 'left' | 'right'
      layout: {
        justifyContent: 'center',
      },

      // ── Size ─────────────────────────────────
      length: 200,             // Color ribbon length (px)
      size: 20,                // Color ribbon width/height (px)

      // ── Title ─────────────────────────────────
      title: 'Value Range',
      titleFontSize: 12,

      // ── Label ─────────────────────────────────
      labelFormatter: (v) => Number(v).toFixed(1),  // Note: v may be a string, convert first
      labelAlign: 'value',     // 'value' | 'range'

      // ── Style ─────────────────────────────────
      style: {
        ribbonFill: 'black',   // Default ribbon fill color (when no color mapping)
      },
    },
  },
});
```

## Common Variants

### Threshold Legend (Segmented Color Band)

```javascript
// When using threshold/quantize/quantile scales, the legend automatically becomes segmented
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  scale: {
    color: {
      type: 'quantize',       // Segmented scale
      domain: [0, 100],
      range: ['#f7fbff', '#6baed6', '#08519c'],  // 3 color segments
    },
  },
  legend: {
    color: {
      position: 'right',
    },
  },
});
```

### Horizontal Color Strip

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  legend: {
    color: {
      position: 'bottom',
      length: 400,
      size: 15,
      layout: { justifyContent: 'center' },
    },
  },
});
```

### Customizing Color Ramp

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  scale: {
    color: {
      type: 'linear',
      domain: [0, 100],
      range: ['#e6f5ff', '#0066cc'],  // Gradient range
    },
  },
  legend: {
    color: {
      position: 'right',
      labelFormatter: (v) => `${Number(v)}°C`,  // Note: v may be a string, so conversion is required
    },
  },
});
```

### size Channel Legend

```javascript
// The size channel will also generate a continuous legend
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', size: 'value' },
  legend: {
    size: {
      position: 'right',
      title: 'Size',
    },
  },
});
```

## Complete Type Reference

```typescript
interface LegendContinuousOptions {
  position?: 'top' | 'bottom' | 'left' | 'right';
  layout?: FlexLayout;
  title?: string | string[];
  length?: number;           // Ribbon length
  size?: number;             // Ribbon width
  labelFormatter?: string | ((value: number) => string);
  labelAlign?: 'value' | 'range';
  style?: {
    ribbonFill?: string;
    [key: string]: any;
  };
}
```

## Continuous Legend vs Categorical Legend

| Feature | Continuous Legend | Categorical Legend |
|---------|------------|------------|
| Data Type | Continuous Values | Discrete Categories |
| Visual Form | Color Ramp/Block | Legend Item List |
| Scale | linear, threshold, quantize | band, ordinal |
| Use Cases | Heatmaps, Maps, Bubble Charts | Bar Charts, Line Charts |

## Common Errors and Fixes

### Error 1: Using Continuous Legend for Categorical Data

```javascript
// ❌ Issue: 'category' is a categorical field and should not use a continuous legend
encode: { color: 'category' }  // Categorical data
// Continuous legend displays poorly

// ✅ Correct: Categorical data automatically uses a categorical legend
// G2 automatically selects the legend type based on the data type
```

### Error 2: Incorrect Parameter Type for labelFormatter

```javascript
// ❌ Issue: The parameter `v` of labelFormatter may be of type string (not number)
// G2 continuous legends pass scale values as strings, directly calling .toFixed() will throw an error
labelFormatter: (v) => v.toFixed(1)   // ❌ TypeError: v.toFixed is not a function
labelFormatter: (v) => v * 100        // ❌ Returns a number instead of a string

// ✅ Correct: Convert to a number first, then format, and finally return a string
labelFormatter: (v) => Number(v).toFixed(1)          // ✅ Keep 1 decimal place
labelFormatter: (v) => `${(Number(v) * 100).toFixed(0)}%`  // ✅ Percentage format
labelFormatter: (v) => `${parseFloat(v).toFixed(0)}m`      // ✅ With unit
```

### Error 3: Length Setting Too Small

```javascript
// ❌ Problem: Color band length is too small, causing label overlap
legend: { color: { length: 50 } }  // Too short

// ✅ Correct: Set an appropriate length based on the number of labels
legend: { color: { length: 200 } }  // Appropriate
```

## Selection with legendCategory

- **Using Continuous Legend**: When the color/size channel is mapped to a continuous numerical field
- **Using Categorical Legend**: When the color channel is mapped to a categorical field

G2 automatically selects the correct legend type based on the scale type, eliminating the need for manual specification.