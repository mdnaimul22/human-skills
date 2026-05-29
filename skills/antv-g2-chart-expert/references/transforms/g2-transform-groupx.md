---
id: "g2-transform-groupx"
title: "G2 GroupX Grouping and Aggregation Transformation"
description: |
  groupX groups data by the values of the x channel and performs aggregation calculations (count, sum, mean, min, max, etc.) on the y channel.
  It is commonly used to directly compute statistical measures from raw row-level data without the need for pre-aggregated data.
  groupY, groupColor, and groupN are its variants, grouping by the y channel, color channel, or a fixed number of groups, respectively.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "groupX"
  - "grouping"
  - "aggregation"
  - "count"
  - "sum"
  - "mean"
  - "transform"
  - "statistics"

related:
  - "g2-transform-stacky"
  - "g2-transform-binx"
  - "g2-mark-interval-basic"

use_cases:
  - "Counting the number of categories from raw row-level data (frequency bar chart)"
  - "Aggregating mean/sum values for each group from detailed data"
  - "Word frequency visualization"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/group"
---

## Minimum Viable Example (Frequency Count Bar Chart)

```javascript
import { Chart } from '@antv/g2';

// Raw row-level data, no need for pre-calculated frequencies
const rawData = [
  { dept: 'R&D' }, { dept: 'R&D' }, { dept: 'R&D' },
  { dept: 'Sales' }, { dept: 'Sales' },
  { dept: 'Design' }, { dept: 'Design' }, { dept: 'Design' }, { dept: 'Design' },
  { dept: 'HR' },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data: rawData,
  encode: {
    x: 'dept',  // Grouping field
    y: '★',     // Placeholder, actual y value calculated by groupX
    color: 'dept',
  },
  transform: [
    {
      type: 'groupX',
      y: 'count',    // Aggregation method for y channel: count per group
    },
  ],
});

chart.render();
```

## Aggregation Methods Quick Reference

```javascript
// Count (number of records in each group)
transform: [{ type: 'groupX', y: 'count' }]

// Sum (sum of y field in each group)
transform: [{ type: 'groupX', y: 'sum' }]

// Mean (average of y field in each group)
transform: [{ type: 'groupX', y: 'mean' }]

// Maximum / Minimum
transform: [{ type: 'groupX', y: 'max' }]
transform: [{ type: 'groupX', y: 'min' }]

// Median
transform: [{ type: 'groupX', y: 'median' }]

// Custom aggregation function
transform: [{ type: 'groupX', y: (values) => values.reduce((a, b) => a + b, 0) / values.length }]
```

## Group by Color (groupColor)

```javascript
// Count the number of males and females in each department
chart.options({
  type: 'interval',
  data: rawEmployeeData,
  encode: { x: 'dept', y: '★', color: 'gender' },
  transform: [
    { type: 'groupX', y: 'count' },   // First, group and count by x and color combination
    { type: 'dodgeX' },               // Then, group and arrange side by side
  ],
});
```

## Mean Line Chart (Drawn Directly from Detailed Data)

```javascript
chart.options({
  type: 'line',
  data: dailySalesData,
  encode: { x: 'month', y: 'dailySales' },
  transform: [
    { type: 'groupX', y: 'mean' },  // Calculate the mean daily sales for each month
  ],
  style: { lineWidth: 2 },
});
```

## KDE Grouping Explanation in Density Charts

When using the `density` chart type with the `kde` transformation, note that the `kde` transformation itself does not rely on `groupX`. Instead, grouping is specified through the `groupBy` parameter. For example:

```javascript
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: irisData,
    transform: [{
      type: 'kde',
      field: 'y',
      groupBy: ['x', 'species'],  // Perform KDE calculation grouped by 'x' and 'species' fields
    }],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'species',
    size: 'size',
    series: 'species',
  },
});
```

In this case, the `kde` transformation automatically handles grouping and density calculation, eliminating the need for an additional `groupX`.

## Common Errors and Fixes

### Error 1: Using the actual field name `encode.y` as `groupX` overrides the y channel
```javascript
// ❌ If you want `groupX` to calculate count, do not use the actual field in `encode.y`
chart.options({
  encode: { x: 'dept', y: 'salary' },
  transform: [{ type: 'groupX', y: 'count' }],  // ⚠️ `count` overrides `salary`
});
// Result: The y-axis displays `count`, not the sum of `salary`

// ✅ If you want `count`, the y field name does not matter (typically use '★' or any placeholder)
chart.options({
  encode: { x: 'dept', y: '★' },
  transform: [{ type: 'groupX', y: 'count' }],  // ✅ Counts the number in each group
});

// ✅ If you want `sum(salary)`, `encode.y` must be 'salary'
chart.options({
  encode: { x: 'dept', y: 'salary' },
  transform: [{ type: 'groupX', y: 'sum' }],  // ✅ Calculates the sum of `salary` for each group
});
```

### Error 2: Confusion with binX — groupX is for existing categories, binX is for numerical binning
```javascript
// ❌ Using groupX for numerical x, each unique value is a group, too many groups
chart.options({
  encode: { x: 'age', y: '★' },
  transform: [{ type: 'groupX', y: 'count' }],  // ❌ age has dozens of unique values
});

// ✅ Numerical x should use binX (bin first, then count)
chart.options({
  encode: { x: 'age', y: '★' },
  transform: [{ type: 'binX', y: 'count', thresholds: 10 }],  // ✅ Binned into 10 buckets
});
```

### Error 3: Incorrect Use of groupX with kde in Density Charts
```javascript
// ❌ Incorrect Example: Mixing groupX and kde in a density chart
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: irisData,
    transform: [
      { type: 'kde', field: 'y', groupBy: ['x'] },
      { type: 'groupX', y: 'mean' }  // ❌ kde already handles grouping and aggregation, groupX is unnecessary
    ]
  },
  encode: { x: 'x', y: 'y', color: 'x' }
});

// ✅ Correct Approach: Use only kde and specify grouping via groupBy
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: irisData,
    transform: [
      { type: 'kde', field: 'y', groupBy: ['x'] }  // ✅ Use only kde transformation
    ]
  },
  encode: { x: 'x', y: 'y', color: 'x', size: 'size' }
});
```

### Error 4: Incorrectly Configuring Encode Mapping Fields in Density Charts
```javascript
// ❌ Incorrect Example: Improper use of fields from KDE output
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{
      type: 'kde',
      field: 'y',
      groupBy: ['x']
    }]
  },
  encode: {
    x: 'x',
    y: 'y',        // ❌ Should use the y field from KDE output (default is 'y')
    color: 'x',
    size: 'size'   // ❌ Should use the size field from KDE output (default is 'size')
  }
});

// ✅ Correct Approach: Ensure fields used in encode match KDE output fields
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [{
      type: 'kde',
      field: 'y',
      groupBy: ['x'],
      as: ['kde_y', 'kde_size']  // ✅ Custom output field names
    }]
  },
  encode: {
    x: 'x',
    y: 'kde_y',      // ✅ Use custom y field name
    color: 'x',
    size: 'kde_size' // ✅ Use custom size field name
  }
});
```