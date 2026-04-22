---
id: "g2-data-sort"
title: "G2 Data Sorting"
description: |
  The sort data transformation orders the data, similar to Array.prototype.sort.
  It is configured in data.transform and pre-processes the data order before rendering.
  Commonly used in scenarios such as pie charts, bar charts for rankings, where data needs to be arranged by size.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "sort"
  - "sorting"
  - "data order"
  - "data transform"

related:
  - "g2-data-filter"
  - "g2-data-fold"
  - "g2-transform-sortx"
  - "g2-transform-sorty"

use_cases:
  - "Pie chart sectors arranged by size"
  - "Bar chart sorted by value"
  - "Ranking data display"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/sort"
---

## Core Concepts

**sort is a Data Transform, not a Mark Transform**

- Data transform configurations are set in `data.transform`
- Uses a callback comparison function (similar to Array.sort)
- Executed during the data loading phase, affecting all marks using the data

**Difference from mark transform sortX/sortY/sortColor:**
- Data sort: Directly sorts the original data array
- Mark sortX/sortY/sortColor: Sorts by visual channel values, can sort after aggregation

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: [
      { category: 'A', value: 30 },
      { category: 'B', value: 50 },
      { category: 'C', value: 20 },
      { category: 'D', value: 40 },
    ],
    transform: [
      {
        type: 'sort',
        callback: (a, b) => b.value - a.value,  // Descending order
      },
    ],
  },
  encode: { x: 'category', y: 'value' },
});

chart.render();
```

## Ascending Order

```javascript
chart.options({
  type: 'interval',
  {
    type: 'inline',
    value: data,
    transform: [
      {
        type: 'sort',
        callback: (a, b) => a.value - b.value,  // Ascending
      },
    ],
  },
  encode: { x: 'category', y: 'value' },
});
```

## Pie Chart Sorted by Size

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: [
      { item: 'A', count: 40 },
      { item: 'B', count: 20 },
      { item: 'C', count: 30 },
    ],
    transform: [
      {
        type: 'sort',
        callback: (a, b) => b.count - a.count,  // Descending order
      },
    ],
  },
  encode: { y: 'count', color: 'item' },
  coordinate: { type: 'theta' },
  transform: [{ type: 'stackY' }],
});
```

## Combine with Other Data Transformations

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: rawData,
    transform: [
      { type: 'filter', callback: (d) => d.value > 0 },  // Filter first
      { type: 'sort', callback: (a, b) => b.value - a.value },  // Then sort
      { type: 'slice', start: 0, end: 10 },  // Take the first 10 items
    ],
  },
  encode: { x: 'category', y: 'value' },
});
```

## Sort by String

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [
      {
        type: 'sort',
        callback: (a, b) => a.name.localeCompare(b.name),  // Sort alphabetically by name
      },
    ],
  },
  encode: { x: 'name', y: 'value' },
});
```

## Configuration Options

| Property | Description                                               | Type                         | Default Value        |
| -------- | -------------------------------------------------- | ---------------------------- | ------------- |
| callback | Comparator for Array.sort, returns 1, 0, -1 representing > = < | `(a: any, b: any) => number` | `(a, b) => 0` |

## Comparison with Mark Transform sortX/sortY

| Feature | Data sort | Mark sortX/sortY |
|------|----------|------------------|
| Configuration Location | `data.transform` | `transform` (mark level) |
| Sorting Basis | Original data field | Visual channel value |
| Aggregation Support | Not supported | Supports sorting by aggregated value |
| Slice Support | Requires slice | Built-in slice parameter |

```javascript
// Data sort: Directly sorts the data
data: {
  transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],
}

// Mark sortX: Sorts by Y channel aggregated value
transform: [{ type: 'sortX', by: 'y', reducer: 'sum' }]
```

## Common Errors and Fixes

### Error 1: Placing `sort` in `mark` transform

```javascript
// ❌ Incorrect: Data `sort` should not be placed in `mark`'s transform
chart.options({
  data: myData,
  transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],  // ❌ Incorrect location
});

// ✅ Correct: `sort` should be placed in `data.transform`
chart.options({
  {
    type: 'inline',
    value: myData,
    transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],  // ✅ Correct
  },
});
```

### Error 2: Confusing Data Sort and Mark SortX

```javascript
// ❌ Incorrect: Data sort does not support channel/by/reducer parameters
data: {
  transform: [{ type: 'sort', channel: 'x', by: 'value' }],  // ❌ This is mark transform syntax
}

// ✅ Correct: Data sort uses a callback
 {
  transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],
}

// If sorting by aggregated values is needed, use mark transform
transform: [{ type: 'sortX', by: 'y', reducer: 'sum' }]
```

### Error 3: Incorrect Callback Return Value

```javascript
// ❌ Incorrect: Returns a boolean
callback: (a, b) => a.value > b.value  // ❌ Returns a boolean

// ✅ Correct: Returns a number (positive, negative, or zero)
callback: (a, b) => a.value - b.value  // ✅ Ascending order
callback: (a, b) => b.value - a.value  // ✅ Descending order
```

### Error 4: Shorthand data Cannot Configure transform

```javascript
// ❌ Error: Shorthand data cannot configure transform
chart.options({
  data: myData,  // Shorthand form
  // Unable to add sort transform
});

// ✅ Correct: Use full data configuration
chart.options({
  {
    type: 'inline',
    value: myData,
    transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],
  },
});
```