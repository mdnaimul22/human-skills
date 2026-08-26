---
id: "g2-transform-sortx"
title: "G2 SortX Transformation"
description: |
  SortX sorts categorical data on the x-axis by a specified field or function,
  commonly used to arrange bar charts in descending order of values, creating ranking charts.
  For multi-series sorting by group totals, use the built-in reducer: 'sum', without custom functions.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "sortX"
  - "sorting"
  - "ranking"
  - "transform"
  - "bar chart sorting"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-transform-dodgex"

use_cases:
  - "Creating bar charts sorted in descending order by value (ranking charts)"
  - "Customizing sorting order for categorical axes"
  - "Sorting multi-series stacked charts by group totals"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-04-02"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/sort-x"
---

## Minimum Viable Example (Sorted by Value in Descending Order)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { city: 'Beijing', gdp: 3.6 },
    { city: 'Shanghai', gdp: 4.3 },
    { city: 'Guangzhou', gdp: 2.8 },
    { city: 'Shenzhen', gdp: 3.2 },
    { city: 'Hangzhou', gdp: 1.8 },
    { city: 'Chengdu', gdp: 2.0 },
  ],
  encode: { x: 'city', y: 'gdp' },
  transform: [
    {
      type: 'sortX',
      by: 'y',           // Sort by y-channel values
      reverse: true,     // true = descending order (maximum value on the left)
    },
  ],
  coordinate: { transform: [{ type: 'transpose' }] },   // Convert to horizontal ranking chart
});

chart.render();
```

## Configuration Options

```javascript
transform: [
  {
    type: 'sortX',
    by: 'y',          // Channel name to sort by ('y' | 'x' | 'color', etc.)
    reducer: 'max',   // Group aggregation method (see below for details), default 'max'
    reverse: true,    // Whether to reverse the order (default false = ascending)
    slice: 10,        // Retain only the top N items (used for Top N charts)
  },
],
```

**`reducer` Built-in Values** (aggregates multiple y values within a group in multi-series/stacked scenarios):

| Value | Description |
|----|------|
| `'max'` | Takes the maximum value in the group (default) |
| `'min'` | Takes the minimum value in the group |
| `'sum'` | Takes the sum of the group ← **Use this for sorting multi-series by total volume** |
| `'mean'` | Takes the mean value of the group |
| `'median'` | Takes the median value of the group |
| `'first'` | Takes the first value in the group |
| `'last'` | Takes the last value in the group |

## Top N Ranking Chart (Displaying Top 10 Only)

```javascript
chart.options({
  type: 'interval',
  data: fullData,
  encode: { x: 'name', y: 'score' },
  transform: [
    {
      type: 'sortX',
      by: 'y',
      reverse: true,
      slice: 10,   // Display top 10 only
    },
  ],
  coordinate: { transform: [{ type: 'transpose' }] },
  axis: { x: { title: null } },
});
```

## Custom Sorting (by Specified Field)

```javascript
// Sort by the 'rank' field in the data
chart.options({
  type: 'interval',
  data,
  encode: { x: 'name', y: 'value' },
  transform: [
    { type: 'sortX', by: 'rank', reverse: false },
  ],
});
```

## Sort by Group Total (Multi-Series Stacked Chart)

In a multi-series chart, each x group has multiple data points. Use the built-in `reducer: 'sum'` to sort by the sum of y values for each group, **no custom function required**:

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'city', y: 'value', color: 'type' },
  transform: [
    { type: 'stackY' },
    {
      type: 'sortX',
      by: 'y',
      reducer: 'sum',   // ✅ Built-in summation, sort by total sum of all series for each city
      reverse: true,
    },
  ],
});
```

## Sorting Considerations in Radial Coordinate Systems

When using the `radial` coordinate system, the behavior of SortX is consistent with the conventional Cartesian coordinate system, but the following points should be noted:

1. **x and y channel mapping**: In radial coordinate systems, x is typically mapped to the angle (i.e., circumferential direction), and y is mapped to the radius (i.e., distance from the center). Therefore, `by: 'y'` actually sorts the radius.
2. **Necessity of sorting**: Due to the "radius feedback effect" in radial charts, where outer rings may appear longer than inner rings even with smaller values, it is **highly recommended to sort the data when using radial coordinate systems** to ensure visual accuracy.
3. **Sorting direction control**: `reverse: true` arranges the data in descending order, with the largest values closest to the outer ring; `reverse: false` does the opposite.

```javascript
// ✅ Correct: Sort by y value in radial coordinate system and render
chart.options({
  type: 'interval',
  data: [
    { movie: 'Movie A', rating: 9.2, genre: 'Sci-Fi' },
    { movie: 'Movie B', rating: 8.7, genre: 'Action' },
    { movie: 'Movie C', rating: 8.5, genre: 'Sci-Fi' },
    { movie: 'Movie D', rating: 7.9, genre: 'Comedy' },
    { movie: 'Movie E', rating: 7.2, genre: 'Action' },
    { movie: 'Movie F', rating: 6.8, genre: 'Comedy' }
  ].sort((a, b) => b.rating - a.rating), // Pre-sort data
  coordinate: { type: 'radial', innerRadius: 0.35 },
  encode: {
    x: 'movie',
    y: 'rating',
    color: 'rating',
  },
  scale: {
    y: { domain: [0, 10] },
  },
  style: {
    radius: 5,
    fillOpacity: 0.95,
  },
  labels: [{
    text: 'rating',
    position: 'inside',
    style: { fontWeight: 'bold', fill: 'white' },
  }],
  axis: {
    x: { label: { autoRotate: true, style: { fontSize: 10 } } },
    y: { label: true, grid: false, style: { fontSize: 9 } },
  },
  interaction: [{ type: 'elementHighlightByColor' }],
});
```

## Common Errors and Fixes

### Error: Replacing Built-in Reducer with Custom Function and Misusing Non-existent `{ value }` Parameter

`sortX` does not have an API like `by: ({ value }) => ...`. `by` only accepts a **channel name string**, and aggregation logic is controlled via the `reducer`. The signature for a custom `reducer` function is `(GI, V) => number` (`GI` = array of row indices for the group, `V` = array of values for the entire column), not an array of data objects.

```javascript
// ❌ Error: by does not accept a function, and ({ value }) parameter does not exist
transform: [
  {
    type: 'sortX',
    by: ({ value }) => d3.sum(value, (d) => d.sales),   // ❌ by can only be a string
    reverse: true,
  },
],

// ❌ Same error: Even without d3, the function form is incorrect
transform: [
  {
    type: 'sortX',
    by: ({ value }) => value.reduce((sum, d) => sum + d.value, 0),  // ❌ by does not support functions
    reverse: true,
  },
],

// ✅ Correct: Sort by group sum using built-in reducer: 'sum'
transform: [
  {
    type: 'sortX',
    by: 'y',
    reducer: 'sum',   // ✅ Built-in aggregation, no need for custom function
    reverse: true,
  },
],
```

### Error: Using Unimported `d3` in Any Callback

G2 internally uses d3, but the `d3` object is not exposed to the user's code scope. Calling `d3.sum()`, `d3.max()`, etc., will throw a `ReferenceError: d3 is not defined`. If custom logic is required, use native JavaScript instead:

```javascript
// d3.sum(arr, d => d.v)  →  arr.reduce((s, d) => s + d.v, 0)
// d3.max(arr, d => d.v)  →  Math.max(...arr.map(d => d.v))
// d3.min(arr, d => d.v)  →  Math.min(...arr.map(d => d.v))
// d3.mean(arr, d => d.v) →  arr.reduce((s, d) => s + d.v, 0) / arr.length
```

### Error: Incorrect Use of x/y Mapping in Radial Coordinates Causes Sorting to Fail

In radial coordinates, if the field that should be used for sorting is incorrectly mapped to the x channel, while the angle is mapped to the y channel, `sortX` will not achieve the expected effect. The correct approach is to map the sorting field to the y channel and ensure the data is pre-sorted by that field.

```javascript
// ❌ Error: Incorrectly mapping rating to the x channel in radial coordinates
chart.options({
  type: 'interval',
  data: [
    { movie: 'Movie A', rating: 9.2, genre: 'Sci-Fi' },
    { movie: 'Movie B', rating: 8.7, genre: 'Action' },
    // ...
  ],
  coordinate: { type: 'radial', innerRadius: 0.2 },
  encode: {
    x: 'rating',       // ❌ Error: rating should be mapped to the y channel
    y: 'movie',        // ❌ Error: movie should be mapped to the x channel
    color: 'rating',
  },
  transform: [
    {
      type: 'sortX',
      by: 'rating',    // ❌ Error: by should be 'y'
      reverse: false,
    },
  ],
});

// ✅ Correct: Mapping rating to the y channel, movie to the x channel, and pre-sorting data
chart.options({
  type: 'interval',
  data: [
    { movie: 'Movie A', rating: 9.2, genre: 'Sci-Fi' },
    { movie: 'Movie B', rating: 8.7, genre: 'Action' },
    // ...
  ].sort((a, b) => b.rating - a.rating),
  coordinate: { type: 'radial', innerRadius: 0.35 },
  encode: {
    x: 'movie',        // ✅ Correct: movie mapped to the x channel (angle)
    y: 'rating',       // ✅ Correct: rating mapped to the y channel (radius)
    color: 'rating',
  },
});
```