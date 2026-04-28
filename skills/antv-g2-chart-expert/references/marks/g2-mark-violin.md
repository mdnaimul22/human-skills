---
id: "g2-mark-violin"
title: "G2 Violin Plot Mark"
description: |
  Violin plot mark. Combines density and boxplot, using kernel density estimation to display data distribution shapes.
  Suitable for scenarios such as multi-group data distribution comparison and exploring data distribution patterns.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "violin plot"
  - "violin"
  - "density distribution"
  - "statistical analysis"

related:
  - "g2-mark-boxplot"
  - "g2-mark-density"

use_cases:
  - "Multi-group data distribution comparison"
  - "Data distribution pattern exploration"
  - "Outlier detection"

anti_patterns:
  - "Use boxplot for small datasets (<20)"
  - "Not suitable for discrete data"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/violin"
---

## Core Concepts

The violin plot combines a box plot with kernel density estimation (KDE):
- Displays the complete shape of the data distribution
- Overlays statistical information from the box plot
- Generates a density contour through KDE

**Main Components:**
- Density Contour: Shows the density of the data distribution
- Box Plot: Displays the median and quartiles
- Median Line: Marks the position of the median

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'view',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
  },
  children: [
    {
      type: 'density',
      data: {
        transform: [
          { type: 'kde', field: 'y', groupBy: ['x', 'species'] },
        ],
      },
      encode: {
        x: 'x',
        y: 'y',
        series: 'species',
        color: 'species',
        size: 'size',
      },
      tooltip: false,
    },
    {
      type: 'boxplot',
      encode: {
        x: 'x',
        y: 'y',
        series: 'species',
        color: 'species',
        shape: 'violin',
      },
      style: {
        opacity: 0.5,
        strokeOpacity: 0.5,
        point: false,
      },
    },
  ],
});

chart.render();
```

## Common Variants

### Polar Coordinate Violin Plot

```javascript
chart.options({
  type: 'view',
  coordinate: { type: 'polar' },
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
  },
  children: [
    {
      type: 'density',
      data: { transform: [{ type: 'kde', field: 'y', groupBy: ['x', 'species'] }] },
      encode: { x: 'x', y: 'y', series: 'species', color: 'species', size: 'size' },
      tooltip: false,
    },
    {
      type: 'boxplot',
      encode: { x: 'x', y: 'y', series: 'species', color: 'species', shape: 'violin' },
      style: { opacity: 0.5, strokeOpacity: 0.5, point: false },
    },
  ],
});
```

### Pure Density Chart

```javascript
chart.options({
  type: 'density',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
    transform: [
      { type: 'kde', field: 'y', groupBy: ['x'], size: 20 },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'x',
    size: 'size',
  },
  tooltip: false,
});
```

### With Outlier Markers

```javascript
chart.options({
  type: 'view',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/morley.json',
  },
  children: [
    {
      type: 'density',
      data: { transform: [{ type: 'kde', field: 'Speed', groupBy: ['Expt'] }] },
      encode: { x: 'Expt', y: 'Speed', size: 'size', color: 'Expt' },
      style: { fillOpacity: 0.4 },
      tooltip: false,
    },
    {
      type: 'boxplot',
      encode: { x: 'Expt', y: 'Speed', color: 'Expt', shape: 'violin' },
      style: {
        opacity: 0.8,
        point: { fill: 'red', size: 3 },  // Outlier markers
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface ViolinOptions {
  type: 'view';
  data: any; // Original data source
  children: [
    {
      type: 'density';
      data: {
        transform: [
          {
            type: 'kde';
            field: string;      // Numerical field
            groupBy: string[];  // Grouping field (must include x-axis field and grouping field)
            size?: number;      // Number of sampling points, defaults to 10, recommended to set between 20~50 for smoother curves
          }
        ]
      };
      encode: {
        x: string;
        y: string;
        size: 'size';
        color?: string;
        series: string;
      };
      tooltip?: boolean; // Recommended to disable to avoid duplication with boxplot
    },
    {
      type: 'boxplot';
      encode: {
        x: string;
        y: string;
        shape: 'violin';
        color?: string;
        series: string;
      };
      style?: {
        opacity?: number;
        strokeOpacity?: number;
        point?: boolean | object; // Whether to display outliers
      };
    }
  ];
}
```

## Violin Plot vs. Box Plot

| Feature         | Violin Plot       | Box Plot          |
|-----------------|-------------------|-------------------|
| Distribution Info| Full Density      | Statistical Summary|
| Multi-modality Detection | Supported | Not Supported    |
| Simplicity      | More Complex      | Concise           |

## Common Errors and Fixes

### Error 1: Missing KDE Transformation

```javascript
// ❌ Problem: No Kernel Density Estimation
data: { type: 'fetch', value: 'data.json' }

// ✅ Correct: Add kde transformation
data: {
  type: 'fetch',
  value: 'data.json',
  transform: [{ type: 'kde', field: 'y', groupBy: ['x', 'species'] }],
}
```

### Error 2: Insufficient Data Volume

```javascript
// ⚠️ Note: It is recommended to have at least 20-30 data points per group
// When data volume is low, it is recommended to use a box plot
```

### Error 3: Missing Boxplot Overlay

```javascript
// ❌ Issue: Only density chart, missing statistical information
children: [{ type: 'density', ... }]

// ✅ Correct: Overlay boxplot
children: [
  { type: 'density', ... },
  { 
    type: 'boxplot', 
    encode: { 
      shape: 'violin',
      x: 'x',
      y: 'y',
      series: 'species',
      color: 'species'
    } 
  },
]
```

### Error 4: Incorrect KDE Transform Configuration

```javascript
// ❌ Issue: Incomplete or missing groupBy fields
transform: [{ type: 'kde', field: 'y', groupBy: ['x'] }]

// ✅ Correct: Ensure groupBy includes all grouping fields
transform: [{ type: 'kde', field: 'y', groupBy: ['x', 'species'] }]
```

### Error 5: Incomplete encode Mapping

```javascript
// ❌ Issue: Missing necessary encode mapping
encode: { x: 'x', y: 'y' }

// ✅ Correct: Ensure all required fields are mapped
encode: {
  x: 'x',
  y: 'y',
  series: 'species',
  color: 'species',
  size: 'size'
}
```