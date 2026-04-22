---
id: "g2-mark-boxplot"
title: "G2 Boxplot: Automatic Statistical Box Plot"
description: |
  Boxplot is a composite Mark in G2 v5 that automatically calculates Q1/Q2/Q3/whiskers/outliers from raw data.
  It generates a standard box plot directly from detailed data without requiring manual calculation of the five-number summary.
  Unlike the box mark (which requires manually providing statistical values like Q1/Q3), boxplot includes built-in statistical computation logic.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "boxplot"
  - "box plot"
  - "automatic statistics"
  - "distribution"
  - "Q1"
  - "Q3"
  - "median"
  - "outlier"

related:
  - "g2-mark-box-boxplot"
  - "g2-mark-point-scatter"
  - "g2-transform-bin"

use_cases:
  - "Directly plot box plots using detailed data (no pre-calculation needed)"
  - "Compare distributions across multiple datasets"
  - "Display data distribution shapes and outliers"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/statistics/box/#boxplot"
---

## Differences with box mark

| | `boxplot` | `box` |
|--|-----------|-------|
| Input Data | Detailed data (automatically calculates statistics) | Requires manual provision of fields such as Q1/Q3 |
| Complexity | Composite Mark (includes box + whiskers + outliers) | Single Mark (only draws the box) |
| Applicable Scenarios | Most scenarios (recommended) | When data is pre-aggregated |

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'boxplot',
  data: [
    { group: 'A', value: 10 },
    { group: 'A', value: 14 },
    { group: 'A', value: 12 },
    { group: 'A', value: 25 },   // outlier
    { group: 'A', value: 11 },
    { group: 'A', value: 13 },
    { group: 'B', value: 20 },
    { group: 'B', value: 22 },
    { group: 'B', value: 18 },
    { group: 'B', value: 5 },    // outlier
    { group: 'B', value: 21 },
  ],
  encode: {
    x: 'group',   // group field
    y: 'value',   // numerical field (automatically calculates statistics)
  },
});

chart.render();
```

## Configure Style

```javascript
chart.options({
  type: 'boxplot',
  data,
  encode: {
    x: 'category',
    y: 'score',
    color: 'category',   // Color by category
  },
  style: {
    boxFill: '#1890ff',          // Box fill color
    boxFillOpacity: 0.3,         // Box opacity
    boxStroke: '#1890ff',        // Box stroke color
    medianStroke: '#ff4d4f',     // Median line color
    medianLineWidth: 2,          // Median line width
    whiskerStroke: '#666',       // Whisker line color
    outlierFill: '#ff4d4f',      // Outlier color
    outlierR: 4,                 // Outlier radius
  },
});
```

## Horizontal Box Plot

```javascript
chart.options({
  type: 'boxplot',
  data,
  encode: {
    x: 'score',      // x-axis is numerical
    y: 'category',   // y-axis is categorical
  },
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

## Polar Coordinate Box Plot

```javascript
chart.options({
  type: 'box',
  data: [
    { x: "Oceania", y: [1, 9, 16, 22, 24] },
    { x: "East Europe", y: [1, 5, 8, 12, 16] },
    { x: "Australia", y: [1, 8, 12, 19, 26] },
    { x: "South America", y: [2, 8, 12, 21, 28] },
    { x: "North Africa", y: [1, 8, 14, 18, 24] },
    { x: "North America", y: [3, 10, 17, 28, 30] },
    { x: "West Europe", y: [1, 7, 10, 17, 22] },
    { x: "West Africa", y: [1, 6, 8, 13, 16] }
  ],
  encode: {
    x: 'x',
    y: 'y', // The y field itself is a [min, Q1, median, Q3, max] array
    color: 'x' // Map color using x (region)
  },
  coordinate: {
    type: 'polar', // Polar coordinates
    innerRadius: 0.2 // Optional: Set inner radius to avoid overcrowding at the center
  },
  scale: {
    x: {
      paddingInner: 0.6,
      paddingOuter: 0.3
    },
    y: {
      zero: true
    }
  },
  style: {
    stroke: "black"
  },
  axis: {
    y: {
      tickCount: 5
    }
  },
  tooltip: {
    items: [
      { channel: 'y', name: 'min' },
      { channel: 'y1', name: 'q1' },
      { channel: 'y2', name: 'q2' },
      { channel: 'y3', name: 'q3' },
      { channel: 'y4', name: 'max' }
    ]
  },
  legend: false // Hide legend (since color corresponds to x-axis)
});
```

## Violin Plot (Violin Shape)

```javascript
chart.options({
  type: 'boxplot',
  data,
  encode: {
    x: 'category',
    y: 'value',
    color: 'category',
    shape: 'violin',  // Set shape to 'violin' to achieve the violin plot effect
  },
  style: {
    opacity: 0.5,
    strokeOpacity: 0.5,
    point: false,     // Hide outliers
  },
});
```

## Common Errors and Fixes

### Error: Using box instead of boxplot without providing statistical fields
```javascript
// ❌ Error: box mark requires manually providing Q1/median/Q3/min/max fields
chart.options({
  type: 'box',
  data: rawDetailData,   // Raw detail data
  encode: { x: 'group', y: 'value' },  // ❌ box requires y to be [min, Q1, median, Q3, max]
});

// ✅ When using raw detail data, use boxplot (automatically calculates statistics)
chart.options({
  type: 'boxplot',
  data: rawDetailData,
  encode: { x: 'group', y: 'value' },  // ✅ boxplot automatically calculates
});
```

### Error: Incorrect combination of density and boxplot when drawing violin plots
```javascript
// ❌ Error: Using boxplot alone and setting shape: 'violin' does not achieve a true density contour
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'boxplot',
      encode: {
        x: 'x',
        y: 'y',
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

// ✅ Correct approach: Use a combination of density + boxplot to achieve a violin plot
chart.options({
  type: 'view',
  data,
  children: [
    // Kernel Density Estimation (KDE)
    {
      type: 'density',
      data: {
        transform: [
          {
            type: 'kde',
            field: 'y',
            groupBy: ['x', 'species'],
          },
        ],
      },
      encode: {
        x: 'x',
        y: 'y',
        color: 'species',
        size: 'size',
        series: 'species',
      },
      style: {
        fillOpacity: 0.7,
      },
      tooltip: false,
    },
    // Boxplot with violin shape (displaying only statistical information)
    {
      type: 'boxplot',
      encode: {
        x: 'x',
        y: 'y',
        color: 'species',
        shape: 'violin',
      },
      style: {
        opacity: 0.8,
        strokeOpacity: 0.6,
        point: false,
      },
    },
  ],
});
```

### Error: Polar Coordinate Box Plot Uses `boxplot` Instead of `box`
```javascript
// ❌ Error: Using `boxplot` to handle aggregated five-number summary data
chart.options({
  type: 'boxplot',
  data: [
    { x: "Oceania", y: [1, 9, 16, 22, 24] },
    { x: "East Europe", y: [1, 5, 8, 12, 16] }
  ],
  encode: { x: 'x', y: 'y' }
});

// ✅ Correct: Using `box` mark to handle aggregated five-number summary data
chart.options({
  type: 'box',
  data: [
    { x: "Oceania", y: [1, 9, 16, 22, 24] },
    { x: "East Europe", y: [1, 5, 8, 12, 16] }
  ],
  encode: { x: 'x', y: 'y' }
});
```

### Error: Incorrect tooltip items configuration
```javascript
// ❌ Error: Using non-existent channel names in tooltip items
chart.options({
  type: 'box',
  data,
  encode: { x: 'x', y: 'y' },
  tooltip: {
    items: [
      { channel: 'y0', name: 'min' }, // Error! y0 is a channel name, not a field name
      { channel: 'y1', name: 'Q1' },
      { channel: 'y2', name: 'median' },
      { channel: 'y3', name: 'Q3' },
      { channel: 'y4', name: 'max' }
    ]
  }
});

// ✅ Correct: Using correct channel names
chart.options({
  type: 'box',
  data,
  encode: { x: 'x', y: 'y' },
  tooltip: {
    items: [
      { channel: 'y', name: 'min' },
      { channel: 'y1', name: 'q1' },
      { channel: 'y2', name: 'q2' },
      { channel: 'y3', name: 'q3' },
      { channel: 'y4', name: 'max' }
    ]
  }
});
```