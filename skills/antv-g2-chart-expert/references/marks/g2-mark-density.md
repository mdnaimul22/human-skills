---
id: "g2-mark-density"
title: "G2 Density Plot (density)"
description: |
  The density mark transforms scatter distributions into continuous density distribution curves or area charts using Kernel Density Estimation (KDE),
  visualizing the probability density of the data. It must be used in conjunction with the KDE data transformation (data.transform) for preprocessing,
  and is suitable for visualizing distributions with a large number of overlapping points.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "density"
  - "Density Plot"
  - "KDE"
  - "Distribution"
  - "Kernel Density"
  - "Violin"

related:
  - "g2-mark-boxplot"
  - "g2-mark-point-scatter"
  - "g2-data-kde"

use_cases:
  - "Displaying the distribution shape of continuous numerical data"
  - "Violin plot (density + polar coordinates + symmetric transformation)"
  - "Comparing data distributions with box plots"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/density"
---

## Core Concepts

**Density mark must be used in conjunction with KDE data transformation**:

- KDE is a **Data Transform**, configured in `data.transform`
- Encode channels required for density mark: `x`, `y`, `size`, `series` (all required)

**Key Configuration Structure**:
```javascript
chart.options({
  type: 'density',
  data: {
    type: 'fetch',  // or 'inline'
    value: '...',
    transform: [{ type: 'kde', field: 'y', groupBy: ['x', 'species'] }],
  },
  encode: {
    x: 'x',
    y: 'y',       // ← KDE output field (default 'y'), not the original field name!
    size: 'size', // ← KDE output field (default 'size')
    series: 'species', // Required: series grouping
  },
});
```

**⚠️ `encode.y` must correspond to the KDE output field (default `'y'`), not the original field name**: Regardless of what `field` is named (e.g., `'value'`, `'score'`), KDE output is always written to the field specified by `as` (default `['y', 'size']`).

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'density',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
    transform: [
      {
        type: 'kde',           // KDE data transformation
        field: 'y',            // Field for kernel density estimation
        groupBy: ['x', 'species'],  // Grouping fields
      },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'species',
    size: 'size',      // Required: Maps density size
    series: 'species', // Required: Series grouping
  },
  tooltip: false,
});

chart.render();
```

## Grouped Density Plot (Multi-Category Comparison)

```javascript
chart.options({
  type: 'density',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
    transform: [
      {
        type: 'kde',
        field: 'y',
        groupBy: ['x'],  // Group by x
        size: 20,        // Bandwidth parameter
      },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'x',
    size: 'size',
    series: 'x',
  },
  tooltip: false,
});
```

## Polar Coordinate Density Chart

```javascript
chart.options({
  type: 'density',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
    transform: [
      { type: 'kde', field: 'y', groupBy: ['x', 'species'] },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'species',
    size: 'size',
    series: 'species',
  },
  coordinate: { type: 'polar' },  // Polar coordinate system
  tooltip: false,
});
```

## Common Errors and Fixes

### Error 1: Incorrect Position of kde Configuration

```javascript
// ❌ Incorrect: kde is not data.type, but data.transform
chart.options({
  type: 'density',
  data: {
    type: 'kde',  // ❌ Incorrect! kde is not a data connector type
    field: 'value',
  },
});

// ✅ Correct: kde is a data transformation, placed in data.transform
chart.options({
  type: 'density',
  data: {
    type: 'fetch',
    value: 'https://example.com/data.json',
    transform: [{ type: 'kde', field: 'y', groupBy: ['x'] }],  // ✅ Correct
  },
});
```

### Error 2: Missing Required Encode Channels

```javascript
// ❌ Error: Missing size and series channels
chart.options({
  type: 'density',
  data: { /* ... */ },
  encode: { x: 'x', y: 'y' },  // ❌ Missing size and series
});

// ✅ Correct: Includes all required channels
chart.options({
  type: 'density',
  data: { /* ... */ },
  encode: {
    x: 'x',
    y: 'y',
    size: 'size',      // Required
    series: 'species', // Required
  },
});
```

### Error 3: `encode.y` Uses the Original Field Name Instead of the KDE Output Field Name

The most common naming confusion: the original field is named `value`, but mistakenly assuming `encode` also uses `y: 'value'`.

```javascript
// ❌ Error: `field: 'value'` is the input for KDE; however, `encode.y` should use the KDE output field
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{ type: 'kde', field: 'value', groupBy: ['group'] }],
    //                                ↑ The original field is named 'value'
  },
  encode: {
    x: 'group',
    y: 'value',  // ❌ 'value' is the original scalar, not the KDE output density array
    size: 'size',
    series: 'group',
  },
});

// ✅ Correct: `encode.y` corresponds to the KDE output field (default `as[0] = 'y'`)
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{ type: 'kde', field: 'value', groupBy: ['group'] }],
  },
  encode: {
    x: 'group',
    y: 'y',      // ✅ The default KDE output field name is 'y', not 'value'
    size: 'size',
    series: 'group',
  },
});
```

**Memory Rule**: `field` is the **input** for KDE, `as` (default `['y', 'size']`) is the **output** of KDE, and encode must use the **output field name**.

### Error 4: Zero Variance or Single-Point Groups Cause KDE Degeneration (Blank Chart)

When a group has only 1 data point or all values are identical (variance = 0), the internal KDE calculation results in min=max, leading to division by zero and NaN values. Consequently, the density plot for that group is not rendered.

```javascript
// ❌ Problematic Data: Zero Variance / Single Point, KDE Fails Silently
const data = [
  { group: 'Low Load', value: 0 },           // Only 1 point
  { group: 'Medium Load', value: 20 },
  { group: 'Medium Load', value: 20 },          // 9 identical values
  // ...
];

// ✅ Solution 1: Specify min/max to Expand KDE Range, Avoiding Zero Interval
transform: [{
  type: 'kde',
  field: 'value',
  groupBy: ['group'],
  min: -10,   // Manually set range to ensure min ≠ max
  max: 50,
}]

// ✅ Solution 2: Use Box Plot or Scatter Plot Instead of Density Plot for Insufficient Data
// KDE requires at least 5-10 distinct values per group to produce meaningful density curves
```

### Error 5: Directly Using Raw Data

```javascript
// ❌ Incorrect: Raw data is not transformed by KDE, missing size field
chart.options({
  type: 'density',
  data: rawPoints,  // ❌ Requires KDE transformation first
  encode: { x: 'x', y: 'y', size: 'size' },
});

// ✅ Correct: Using data.transform for KDE preprocessing
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawPoints,
    transform: [{ type: 'kde', field: 'y', groupBy: ['x'] }],
  },
  encode: { x: 'x', y: 'y', size: 'size', series: 'x' },
});
```

### Error 6: Incorrect Data Passing in Composite Views

In composite views (`type: 'view'`), if the `children` sub-charts do not explicitly declare `data`, they will inherit the parent's data. However, if a sub-chart requires specific data transformations (such as KDE), it must explicitly declare its own `data` configuration.

```javascript
// ❌ Incorrect: Sub-chart does not declare data, KDE transformation cannot be applied
chart.options({
  type: 'view',
  data: rawData,
  children: [{
    type: 'density',
    // Missing data configuration, transform is invalid
    encode: { x: 'x', y: 'y', size: 'size', series: 'species' },
  }]
});

// ✅ Correct: Sub-chart explicitly declares data and applies KDE transformation
chart.options({
  type: 'view',
  data: rawData,
  children: [{
    type: 'density',
    data: {
      // Explicitly declare data, even if it is the same as the parent
      type: 'inline',
      value: rawData,
      transform: [{ type: 'kde', field: 'y', groupBy: ['x', 'species'] }],
    },
    encode: { x: 'x', y: 'y', size: 'size', series: 'species' },
  }]
});
```

### Error 7: Insufficient Data Due to Improper KDE Grouping Field Configuration

When the `groupBy` field is too granular, resulting in too few data points within certain groups (e.g., less than or equal to 1), KDE cannot compute an effective density distribution, and the group will not be rendered.

```javascript
// ❌ Error: groupBy includes too many fields, causing some groups to have only one data point
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{ 
      type: 'kde', 
      field: 'y', 
      groupBy: ['x', 'species', 'extraCategory'] // Overly granular grouping, may result in groups with only one point
    }],
  },
  encode: { x: 'x', y: 'y', size: 'size', series: 'species' },
});

// ✅ Correct: Reasonably select groupBy fields to ensure sufficient data points in each group
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{ 
      type: 'kde', 
      field: 'y', 
      groupBy: ['x', 'species'] // Reasonable grouping, ensuring sufficient data in each group
    }],
  },
  encode: { x: 'x', y: 'y', size: 'size', series: 'species' },
});
```

### Error 8: Blank Chart Due to Mismatch Between KDE Output Field Names and encode Mapping

When using `as` to customize output field names in KDE transformations, ensure that the `y` and `size` channels in `encode` reference the correct custom field names.

```javascript
// ❌ Error: KDE output field names are density_x and density_y, but encode references default field names
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{
      type: 'kde',
      field: 'y',
      groupBy: ['x'],
      as: ['density_x', 'density_y']
    }]
  },
  encode: {
    x: 'x',
    y: 'y',       // ❌ Should be 'density_x'
    size: 'size', // ❌ Should be 'density_y'
    series: 'x'
  }
});

// ✅ Correct: encode references custom field names from KDE output
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{
      type: 'kde',
      field: 'y',
      groupBy: ['x'],
      as: ['density_x', 'density_y']
    }]
  },
  encode: {
    x: 'x',
    y: 'density_x',  // ✅ Correct reference to custom field name
    size: 'density_y', // ✅ Correct reference to custom field name
    series: 'x'
  }
});
```

### Error 9: Insufficient Samples per Group After KDE Grouping Causes Blank Chart

The KDE algorithm requires each group to have enough sample points (it is recommended that each group has at least 5~10 different values) to effectively calculate the density distribution. If there are too few samples per group after grouping, it may cause the chart to render as blank.

```javascript
// ❌ Error: Insufficient samples per group after grouping
const insufficientData = [
  { group: 'A', value: 1 },
  { group: 'A', value: 1 },
  { group: 'B', value: 2 },
  { group: 'B', value: 2 }
];

chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: insufficientData,
    transform: [{ type: 'kde', field: 'value', groupBy: ['group'] }]
  },
  encode: { x: 'group', y: 'y', size: 'size', series: 'group' }
});

// ✅ Solution: Merge groups or increase sample size, or use a different chart type
const sufficientData = [
  { group: 'A', value: 1 }, { group: 'A', value: 1.1 }, { group: 'A', value: 1.2 },
  { group: 'A', value: 1.3 }, { group: 'A', value: 1.4 }, { group: 'B', value: 2 },
  { group: 'B', value: 2.1 }, { group: 'B', value: 2.2 }, { group: 'B', value: 2.3 },
  { group: 'B', value: 2.4 }
];
```

## Configuration Options

### encode Channel

| Property | Description                                      | Required |
|----------|--------------------------------------------------|----------|
| x        | X-axis field, time or ordered categorical field  | ✓        |
| y        | Y-axis field, numerical field (KDE output field) | ✓        |
| size     | Density size field (generated after KDE transformation) | ✓        |
| series   | Series grouping field                           | ✓        |
| color    | Color mapping field                             |          |

### Coordinate System

| Coordinate System | Type         | Usage               |
|-------------------|--------------|---------------------|
| Cartesian         | `'cartesian'` | Default, used in density plots, etc. |
| Polar             | `'polar'`     | Polar violin plots, etc. |
| Symmetric         | `'transpose'` | Symmetric violin plots, etc. |