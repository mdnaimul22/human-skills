---
id: "g2-interaction-slider-filter"
title: "G2 Slider Filter"
description: |
  G2 v5 enables the slider filter via `slider: { x: true }` or `interaction: [{ type: 'sliderFilter' }]`,
  allowing users to drag the slider to filter data ranges on the x/y axis. This is commonly used for partial time period filtering in time series charts.
library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "slider"
  - "filter"
  - "time series"
  - "range filter"
  - "spec"

related:
  - "g2-mark-line-basic"
  - "g2-interaction-tooltip"
  - "g2-scale-time"

use_cases:
  - "Drag to view partial time periods in time series line charts"
  - "Zoom in on specific areas of large datasets"
  - "Synchronize time ranges across multiple charts"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/slider"
---

## Basic Usage (Time Series Line Chart + X-Axis Thumbnail Axis)

Add a thumbnail axis at the bottom of the line chart and drag the slider to filter the time range:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 720,
  height: 480,
});

// Generate 30 days of time series data
const data = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(2024, 0, i + 1).toISOString().slice(0, 10),
  value: Math.round(200 + Math.random() * 300),
}));

chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: true,   // Display thumbnail axis below the x-axis
  },
});

chart.render();
```

## Set Initial Display Range

`values` accepts a ratio value within the range `[0, 1]`, controlling the initial selected range of the thumbnail axis:

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: {
      values: [0.6, 1.0],   // Initially display only the last 40% of the data
    },
  },
});
```

## Dual-Axis Thumbnail Axes (Filtering Both X and Y Axes Simultaneously)

Add thumbnail axes to both the x-axis and y-axis, suitable for scatter plots and other two-dimensional data exploration:

```javascript
chart.options({
  type: 'point',
  data: [
    { price: 12000, score: 85, brand: 'A' },
    { price: 8500,  score: 72, brand: 'B' },
    { price: 23000, score: 91, brand: 'C' },
    { price: 5000,  score: 60, brand: 'D' },
    { price: 18000, score: 88, brand: 'E' },
    { price: 31000, score: 95, brand: 'F' },
    { price: 9500,  score: 78, brand: 'G' },
  ],
  encode: { x: 'price', y: 'score', color: 'brand' },
  slider: {
    x: {
      values: [0, 0.7],   // Initial x-axis display: 0-70%
    },
    y: {
      values: [0.2, 1.0], // Initial y-axis display: 20%-100%
    },
  },
});
```

## Custom Label Format

Format the label display at both ends of the slider axis using `labelFormatter`:

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: {
      values: [0.4, 1.0],
      labelFormatter: (value) => {
        // value is the actual data value (original data after scale conversion)
        const date = new Date(value);
        return `${date.getMonth() + 1}月${date.getDate()}日`;
      },
    },
  },
});
```
## Enable Using the Interaction Method

You can also enable `sliderFilter` through the `interaction` array. Both methods produce the same effect:

```javascript
// Method 1: slider property (recommended, more concise)
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: { x: true },
});

// Method 2: interaction array
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  interaction: [
    { type: 'sliderFilter' },
  ],
});
```

## Common Errors and Fixes

### Error: values exceed the range [0, 1]

```javascript
// ❌ values must be within the range [0, 1], representing data proportions
chart.options({
  slider: {
    x: { values: [10, 80] },   // Error: not pixels or indices, but 0-1 proportions
  },
});

// ✅ Correct: use decimals between 0 and 1
chart.options({
  slider: {
    x: { values: [0.1, 0.8] },   // Displays 10% to 80% of the data
  },
});
```

### Error: Using sliderFilter on a Discrete Categorical Axis

```javascript
// ❌ slider is primarily suitable for continuous axes (time axes, numerical axes),
// and performs poorly on purely categorical x-axes, with filtering logic that may not meet expectations
chart.options({
  type: 'interval',
  data: [{ genre: 'Sports', sold: 275 }, { genre: 'Action', sold: 120 }],
  encode: { x: 'genre', y: 'sold' },   // genre is discrete categorical
  slider: { x: true },
});

// ✅ sliderFilter is best suited for time series data or large amounts of continuous numerical data
chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value' },   // date is a time axis
  slider: { x: true },
});
```

### Error: slider written as an array

```javascript
// ❌ slider is an object, not an array
chart.options({
  slider: [{ x: true }],
});

// ✅ slider is an object, x/y are its properties
chart.options({
  slider: { x: true },
  // or enable dual axes simultaneously
  // slider: { x: true, y: true },
});
```

### Error: Incorrect Order of `values` (Start Value Greater Than End Value)

```javascript
// ❌ Start value cannot be greater than end value
chart.options({
  slider: {
    x: { values: [0.8, 0.2] },
  },
});

// ✅ First value is the start position, second value is the end position (both are 0-1 ratios)
chart.options({
  slider: {
    x: { values: [0.2, 0.8] },
  },
});
```