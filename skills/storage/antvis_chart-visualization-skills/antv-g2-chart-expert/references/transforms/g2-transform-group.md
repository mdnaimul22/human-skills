---
id: "g2-transform-group"
title: "G2 Group / GroupX / GroupY Group Aggregation Transform"
description: |
  Group, GroupX, and GroupY are Transforms in G2 v5 used for group aggregation.
  Group aggregates by both x and y channels; GroupX aggregates by the x channel; GroupY aggregates by the y channel.
  Supports aggregation functions such as mean, sum, count, min, max, median, first, and last.
  Commonly used in scenarios like histograms, statistical bar charts, and aggregated line charts.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "group"
  - "groupX"
  - "groupY"
  - "group aggregation"
  - "transform"
  - "statistics"
  - "mean"
  - "sum"

related:
  - "g2-transform-bin"
  - "g2-transform-stacky"
  - "g2-mark-interval-basic"

use_cases:
  - "Calculate average values by category (mean bar chart)"
  - "Sum and display total quantities after grouping by X"
  - "Aggregate detailed data into statistical summaries"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/group-x"
---

## Core Concepts

| Transform | Grouping Dimension | Typical Scenario |
|-----------|--------------------|------------------|
| `groupX`  | x channel (+ color/series) | Average/sum within the same category |
| `groupY`  | y channel | Aggregation by Y grouping |
| `group`   | x + y dual channels | Two-dimensional grouping aggregation |

Aggregation functions are specified in the form of `y: 'mean'`, supporting:  
`mean` (average), `sum` (sum), `count` (count), `min`, `max`, `median`, `first`, `last`

## Basic Usage of GroupX (Calculate Mean by Category)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { category: 'A', value: 10 },
    { category: 'A', value: 20 },
    { category: 'A', value: 30 },
    { category: 'B', value: 40 },
    { category: 'B', value: 50 },
  ],
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'groupX',
      y: 'mean',   // Group by x, calculate mean of y
    },
  ],
});

chart.render();
// Result: A displays mean 20, B displays mean 45
```

## GroupX Aggregation Functions Overview

```javascript
chart.options({
  type: 'interval',
  data: rawData,
  encode: { x: 'category', y: 'value' },
  transform: [
    {
      type: 'groupX',
      y: 'mean',      // Mean
      // y: 'sum',    // Sum
      // y: 'count',  // Count (ignores y channel value, counts the number of bars)
      // y: 'max',    // Maximum
      // y: 'min',    // Minimum
      // y: 'median', // Median
    },
  ],
});
```

## Statistical Count (Frequency Distribution)

```javascript
// Count occurrences of each category
chart.options({
  type: 'interval',
  data: rawData,
  encode: { x: 'category' },    // No need for y channel
  transform: [
    { type: 'groupX', y: 'count' },  // y will be automatically generated as the count value
  ],
});
```

## GroupY Usage (Group by Y)

```javascript
// Group by y in the horizontal direction and calculate the mean (commonly used in horizontal bar charts)
chart.options({
  type: 'interval',
  data: rawData,
  encode: { y: 'category', x: 'value' },
  transform: [
    { type: 'groupY', x: 'mean' },  // Group by y, calculate the mean of x
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

## Multi-Field Aggregation

```javascript
// Aggregate multiple fields simultaneously
chart.options({
  type: 'point',
  data: rawData,
  encode: { x: 'date', y: 'value', size: 'amount' },
  transform: [
    {
      type: 'groupX',
      y: 'mean',       // Calculate mean for y
      size: 'sum',     // Calculate sum for size channel
    },
  ],
});
```

## Using Group in Cell Charts

For charts of type `cell`, it is often necessary to group and aggregate the data before rendering. For example, grouping by UTC day and UTC month of the date, and taking the maximum value of the highest temperature:

```javascript
const chart = new Chart({
  container: 'container',
});

chart.options({
  type: 'cell',
  height: 300,
  data: {
    type: 'inline',
    value: [
      { date: '2012-01-01', temp_max: 12.8 },
      { date: '2012-01-02', temp_max: 10.6 },
      // More data...
    ]
  },
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max',
  },
  transform: [{ type: 'group', color: 'max' }],
  scale: { color: { type: 'sequential', palette: 'gnBu' } },
  style: { inset: 0.5 },
});

chart.render();
```

## Common Errors and Fixes

### Error 1: `transform` written as an object instead of an array
```javascript
// ❌ Incorrect
chart.options({ transform: { type: 'groupX', y: 'mean' } });

// ✅ Correct
chart.options({ transform: [{ type: 'groupX', y: 'mean' }] });
```

### Error 2: Still passing y encode during count aggregation
```javascript
// ❌ y channel is not needed during count aggregation
chart.options({
  encode: { x: 'category', y: 'someField' },
  transform: [{ type: 'groupX', y: 'count' }],  // y: 'count' will ignore encode.y
});

// ✅ Only x channel is needed for count aggregation
chart.options({
  encode: { x: 'category' },    // y is not needed
  transform: [{ type: 'groupX', y: 'count' }],
});
```

### Error 3: Incorrect Use of Group Aggregation in Cell Charts
```javascript
// ❌ Incorrect: No aggregation for duplicate x/y combinations, causing rendering anomalies
chart.options({
  type: 'cell',
  data: weatherData,
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max'
  },
  transform: []  // Missing necessary group aggregation
});

// ✅ Correct: Using group and specifying color aggregation method
chart.options({
  type: 'cell',
  data: weatherData,
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max'
  },
  transform: [{ type: 'group', color: 'max' }]  // Must aggregate color channel
});
```