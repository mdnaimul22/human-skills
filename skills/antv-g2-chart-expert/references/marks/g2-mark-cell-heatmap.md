---
id: "g2-mark-cell-heatmap"
title: "G2 Heatmap (Cell Mark)"
description: |
  Create a matrix heatmap using Cell Mark, where the color intensity represents the value at the intersection of two categorical dimensions.
  Commonly used in correlation analysis, time-category distribution, and other scenarios. This article uses the Spec mode.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "cell"
tags:
  - "heatmap"
  - "Cell"
  - "heatmap"
  - "matrix"
  - "correlation"
  - "color mapping"
  - "spec"

related:
  - "g2-core-encode-channel"
  - "g2-scale-sequential"
  - "g2-comp-legend-config"

use_cases:
  - "Displaying intersection values of two categorical dimensions (e.g., correlation matrix)"
  - "Time heatmap (e.g., daily activity levels per week)"
  - "User behavior matrix analysis"

anti_patterns:
  - "Use density plots or contour plots instead when data is continuous for x/y"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/heatmap/basic"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'cell',
  data: [
    { week: 'Mon', hour: '6AM',  value: 10 },
    { week: 'Mon', hour: '12PM', value: 80 },
    { week: 'Mon', hour: '6PM',  value: 60 },
    { week: 'Tue', hour: '6AM',  value: 5  },
    { week: 'Tue', hour: '12PM', value: 95 },
    { week: 'Tue', hour: '6PM',  value: 70 },
    { week: 'Wed', hour: '6AM',  value: 20 },
    { week: 'Wed', hour: '12PM', value: 75 },
    { week: 'Wed', hour: '6PM',  value: 55 },
  ],
  encode: {
    x: 'week',
    y: 'hour',
    color: 'value',    // Color intensity represents value magnitude
  },
  scale: {
    color: { 
      type: 'sequential',   // Explicitly specify sequential color scale
      palette: 'YlOrRd'     // Sequential palette: YlOrRd | Blues | Viridis, etc.
    },
  },
  style: {
    inset: 1,    // Cell spacing (px)
  },
});

chart.render();
```

## Heatmap with Numeric Labels

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'week', y: 'hour', color: 'value' },
  scale: {
    color: { type: 'sequential', palette: 'Blues' },
  },
  labels: [
    {
      text: 'value',
      style: {
        fontSize: 11,
        fill: (d) => d.value > 60 ? 'white' : '#333',  // White text for dark backgrounds
      },
    },
  ],
  style: { inset: 2 },
});
```

## Correlation Coefficient Matrix

```javascript
// Correlation Analysis Heatmap (Diverging Color Scale from -1 to 1)
chart.options({
  type: 'cell',
  data: correlationData,  // [{ x: 'VariableA', y: 'VariableB', corr: 0.75 }, ...]
  encode: {
    x: 'x',
    y: 'y',
    color: 'corr',
  },
  scale: {
    color: {
      type: 'sequential',  // Explicitly specify as sequential color scale
      palette: 'RdBu',     // Diverging color scale: Red-White-Blue
      domain: [-1, 1],     // Fixed numerical range
    },
  },
  labels: [
    {
      text: (d) => d.corr.toFixed(2),
      style: { fontSize: 10 },
    },
  ],
});
```

## Calendar Heatmap (GitHub Style)

```javascript
// Daily activity calendar view
chart.options({
  type: 'cell',
  data: dailyData,   // [{ date: '2024-01-01', weekday: 'Mon', week: 1, value: 5 }, ...]
  encode: {
    x: 'week',      // Week number (1-53)
    y: 'weekday',   // Day of the week
    color: 'value',
  },
  scale: {
    color: { type: 'sequential', palette: 'Greens', domain: [0, 20] },
    y: {
      domain: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    },
  },
  style: { inset: 2, radius: 2 },
  axis: {
    y: { title: null },
    x: { title: null, tickCount: 4 },
  },
});
```

## Terrain Elevation Heatmap

```javascript
// Simulated terrain elevation data
const terrainData = [];
for (let x = 0; x <= 50; x += 2) {
  for (let y = 0; y <= 50; y += 2) {
    // Simulated mountain terrain: elevation distribution of two peaks
    const elevation1 = 100 * Math.exp(-((x - 15) ** 2 + (y - 15) ** 2) / 200);
    const elevation2 = 80 * Math.exp(-((x - 35) ** 2 + (y - 35) ** 2) / 150);
    const elevation = elevation1 + elevation2 + 10; // Base elevation
    terrainData.push({ x, y, elevation });
  }
}

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

chart.options({
  type: 'cell',
  data: terrainData,
  encode: {
    x: 'x',
    y: 'y',
    color: 'elevation',
  },
  style: {
    stroke: '#333',
    lineWidth: 0.5,
    inset: 0.5,
  },
  scale: {
    color: {
      type: 'sequential',
      palette: 'viridis',
    },
  },
  legend: {
    color: {
      length: 300,
      layout: { justifyContent: 'center' },
      labelFormatter: (value) => `${Math.round(value)}m`,
    },
  },
  tooltip: {
    title: 'Elevation Information',
    items: [
      { field: 'x', name: 'Longitude' },
      { field: 'y', name: 'Latitude' },
      {
        field: 'elevation',
        name: 'Elevation',
        valueFormatter: (value) => `${Math.round(value)}m`,
      },
    ],
  },
});

chart.render();
```

## Common Errors and Fixes

### Error 1: Missing scale configuration in the color channel results in discrete colors
```javascript
// ❌ Issue: color defaults to discrete color scale, unsuitable for continuous values
chart.options({ type: 'cell', encode: { x: 'a', y: 'b', color: 'value' } });
// value is a continuous numerical value but is mapped to discrete colors

// ✅ Correct: Specify a continuous color palette and explicitly set the type to sequential
chart.options({
  type: 'cell',
  encode: { x: 'a', y: 'b', color: 'value' },
  scale: { 
    color: { 
      type: 'sequential',   // Explicitly specify as sequential color scale
      palette: 'Blues'      // or 'YlOrRd', 'Viridis', etc.
    } 
  },
});
```

### Error 2: Uneven Cell Size
```javascript
// ❌ Issue: Cell deformation when there is a large difference in the number of categories on the x/y axes
// ✅ Solution: Set the aspect ratio of the Chart to be close to the ratio of the number of x/y categories
const chart = new Chart({
  container: 'container',
  width: xCategories.length * 40,    // 40px per cell
  height: yCategories.length * 40,
});
```

### Error 3: Incorrect Use of transform.group Leading to Duplicate or Missing Data
```javascript
// ❌ Issue: When there are duplicate combinations in the x/y channels, not using group aggregation will result in multiple overlapping cells or data loss
chart.options({
  type: 'cell',
  data: [
    { day: 1, month: 0, temp: 10 },
    { day: 1, month: 0, temp: 15 }, // Two temperature records for the same day and month
  ],
  encode: {
    x: 'day',
    y: 'month',
    color: 'temp'
  }
});
// The above code may only display one of the values or show multiple overlapping cells

// ✅ Correct: Use transform.group to aggregate duplicate data (e.g., take the maximum, average, etc.)
chart.options({
  type: 'cell',
  data: [
    { day: 1, month: 0, temp: 10 },
    { day: 1, month: 0, temp: 15 },
  ],
  encode: {
    x: 'day',
    y: 'month',
    color: 'temp'
  },
  transform: [{
    type: 'group',
    color: 'max'  // For data with the same x/y combination, take the maximum value of temp
  }]
});
```

### Error 4: Abnormal color mapping due to incorrect setting of scale.type as sequential
```javascript
// ❌ Issue: The color channel does not explicitly set scale.type to 'sequential', which may result in unexpected color mapping
chart.options({
  type: 'cell',
  encode: { x: 'a', y: 'b', color: 'value' },
  scale: { color: { palette: 'Blues' } } // Only palette is set, type is not specified
});

// ✅ Correct: Explicitly specify scale.type as 'sequential'
chart.options({
  type: 'cell',
  encode: { x: 'a', y: 'b', color: 'value' },
  scale: { 
    color: { 
      type: 'sequential',  // Explicitly specified as sequential
      palette: 'Blues' 
    } 
  }
});
```

### Error 5: Palette Name Case Sensitivity Causes Palette Not Found
```javascript
// ❌ Issue: Palette name case mismatch, e.g., 'gnBu' should actually be 'GnBu'
chart.options({
  type: 'cell',
  data,
  encode: { x: 'day', y: 'month', color: 'temp' },
  scale: {
    color: { type: 'sequential', palette: 'gnBu' } // Lowercase g does not match actual naming
  }
});

// ✅ Correct: Use the correct palette name (note the case)
chart.options({
  type: 'cell',
  data,
  encode: { x: 'day', y: 'month', color: 'temp' },
  scale: {
    color: { type: 'sequential', palette: 'GnBu' } // Correct uppercase G
  }
});
```

### Error 6: Data Undefined or Incorrectly Referenced
```javascript
// ❌ Issue: Using an undefined variable 'data'
const processedData = data.map(...);

// ✅ Correct: Ensure the data variable is properly defined
const rawData = [...];
const processedData = rawData.map(...);
```

### Error 7: Incorrect Animation Configuration Syntax
```javascript
// ❌ Issue: animate.enter should be an object, not a string or other type
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  animate: 'fadeIn' // Incorrect configuration
});

// ✅ Correct: Use the standard animation configuration object
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },
  animate: {
    enter: {
      type: 'fadeIn',
      duration: 1000
    }
  }
});
```