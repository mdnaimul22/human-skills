---
id: "g2-comp-view"
title: "G2 View Composition"
description: |
  View Composition is used to create multi-view charts. It allows combining multiple marks together,
  sharing configurations such as data, scales, and axes.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "composition"
  - "view"
  - "multi-view"
  - "composite chart"

related:
  - "g2-comp-space-layer"
  - "g2-comp-space-flex"
  - "g2-core-chart-init"

use_cases:
  - "multi-series charts"
  - "composite charts"
  - "multi-mark charts with shared configurations"

anti_patterns:
  - "single-mark charts do not require View Composition"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition"
---

## Core Concepts

View compositions allow combining multiple marks:
- Share data and configurations
- Unified management of scales and axes
- Support nested compositions

**Features:**
- Child marks inherit parent configurations
- Support data merging
- Configurable axes, legends, etc.

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'view',
  data: [
    { month: 'Jan', value: 100, type: 'A' },
    { month: 'Feb', value: 120, type: 'A' },
    { month: 'Jan', value: 80, type: 'B' },
    { month: 'Feb', value: 90, type: 'B' },
  ],
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'type' },
    },
    {
      type: 'point',
      encode: { x: 'month', y: 'value', color: 'type' },
    },
  ],
});

chart.render();
```

## Common Variants

### Shared Axis Configuration

```javascript
chart.options({
  type: 'view',
  data,
  axis: {
    x: { title: 'Month' },
    y: { title: 'Value' },
  },
  children: [
    { type: 'line', encode: { x: 'month', y: 'value', color: 'type' } },
    { type: 'point', encode: { x: 'month', y: 'value', color: 'type' } },
  ],
});
```

### Shared Scale

```javascript
chart.options({
  type: 'view',
  data,
  scale: {
    color: {
      range: ['#1890ff', '#52c41a'],
    },
  },
  children: [
    { type: 'line', encode: { x: 'month', y: 'value', color: 'type' } },
    { type: 'point', encode: { x: 'month', y: 'value', color: 'type' } },
  ],
});
```

### Sub-mark Independent Data

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      data: [{ category: 'A', value: 100 }],
      encode: { x: 'category', y: 'value' },
    },
    {
      type: 'line',
      data: [{ x: 0, y: 50 }, { x: 1, y: 150 }],
      encode: { x: 'x', y: 'y' },
      scale: { x: { type: 'identity' }, y: { domain: [0, 200] } },
    },
  ],
});
```

### Configuration with Legend

```javascript
chart.options({
  type: 'view',
  data,
  encode: { color: 'type' },
  legend: {
    color: { position: 'top' },
  },
  children: [
    { type: 'line', encode: { x: 'month', y: 'value', color: 'type' } },
    { type: 'point', encode: { x: 'month', y: 'value', color: 'type' } },
  ],
});
```

## Complete Type Reference

```typescript
interface ViewComposition {
  type: 'view';
  data?: DataOption;
  encode?: EncodeOption;
  scale?: ScaleOption;
  axis?: AxisOption;
  legend?: LegendOption;
  transform?: TransformOption[];
  slider?: SliderOption;
  children: MarkSpec[];  // Child mark array
}
```

## Differences with SpaceLayer/SpaceFlex

| Composition Type | Use Case | Features |
|------------------|----------|----------|
| view | Multiple mark overlays | Shared coordinate system |
| spaceLayer | Multi-layer overlays | Independent coordinate system |
| spaceFlex | Multi-view arrangement | Side-by-side/stacked layout |

## Common Errors and Fixes

### Error 1: Incorrect `children` Format

```javascript
// ❌ Incorrect: `children` should be an array
chart.options({
  type: 'view',
  children: { type: 'line', ... },
});

// ✅ Correct
chart.options({
  type: 'view',
  children: [{ type: 'line', ... }],
});
```

### Error 2: Sub-mark type not specified

```javascript
// ❌ Error: Sub-mark must have a type
chart.options({
  type: 'view',
  children: [{ encode: { x: 'a', y: 'b' } }],
});

// ✅ Correct
chart.options({
  type: 'view',
  children: [{ type: 'line', encode: { x: 'a', y: 'b' } }],
});
```

### Error 3: Confusing Data and Children Data

```javascript
// ⚠️ Note: The data of the View will be merged with the data of the child mark
// If the child mark has its own data, it will override the parent's data

// Method 1: Parent provides data
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'a', y: 'b' } },
  ],
});

// Method 2: Child mark has independent data
chart.options({
  type: 'view',
  children: [
    { type: 'line', data, encode: { x: 'a', y: 'b' } },
  ],
});
```

### Error 4: Improper Use of Density and Boxplot Leading to Blank Screen

```javascript
// ❌ Incorrect: Incorrect data format for density and boxplot
// Density requires data transformed by KDE, including y and size fields
// Boxplot requires raw data for internal statistical calculations
chart.options({
  type: 'view',
  data: rawData,
  children: [
    {
      type: 'density',
      encode: { x: 'category', y: 'value', size: 'size' },
    },
    {
      type: 'boxplot',
      encode: { x: 'category', y: 'value' },
    },
  ],
});

// ✅ Correct: Use transform for KDE conversion to ensure correct data format
chart.options({
  type: 'view',
  data: {
    type: 'inline',
    value: rawData,
  },
  children: [
    {
      type: 'density',
      data: {
        transform: [
          {
            type: 'kde',
            field: 'value',
            groupBy: ['category'],
            size: 50, // Controls the granularity of the density curve
          },
        ],
      },
      encode: {
        x: 'category',
        y: 'value',
        size: 'size',
        series: 'category',
      },
      style: {
        fillOpacity: 0.7,
      },
      tooltip: false,
    },
    {
      type: 'boxplot',
      encode: {
        x: 'category',
        y: 'value',
        series: 'category',
        shape: 'violin', // Optional, for violin plot
      },
      style: {
        opacity: 0.8,
        strokeOpacity: 0.6,
        point: false, // Optional, hides outliers
      },
    },
  ],
});
```