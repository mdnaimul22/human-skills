---
id: "g2-data-filter"
title: "G2 Filter Data Filtering"
description: |
  The filter data transformation filters data during the data loading phase based on conditions, retaining only rows that meet the criteria.
  Similar to JavaScript's Array.filter, it accepts a predicate function.
  Configured in data.transform, it preprocesses data before rendering.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "filter"
  - "filtering"
  - "data filtering"
  - "conditional filtering"
  - "data transform"

related:
  - "g2-data-fold"
  - "g2-data-sort"
  - "g2-interaction-brush"

use_cases:
  - "Display only data subsets that meet conditions (e.g., values greater than a threshold)"
  - "Exclude outliers or null values"
  - "Perform categorical filtering during the data loading phase"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/filter"
---

## Core Concepts

**filter is a Data Transform, not a Mark Transform**

- Data transforms are configured in `data.transform`
- Executed during the data loading phase, affecting all marks using that data
- Unlike mark transforms, data transforms are data preprocessing and do not involve visual channels

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: [
      { genre: 'Sports', sold: 275 },
      { genre: 'Strategy', sold: 115 },
      { genre: 'Action', sold: 120 },
      { genre: 'RPG', sold: 98 },
      { genre: 'Shooter', sold: 35 },
    ],
    transform: [
      {
        type: 'filter',
        callback: (d) => d.sold >= 100,  // Retain only data with sales ≥ 100
      },
    ],
  },
  encode: { x: 'genre', y: 'sold', color: 'genre' },
});

chart.render();
```

## Exclude Null Values / Outliers

```javascript
chart.options({
  type: 'line',
  {
    type: 'inline',
    value: rawData,
    transform: [
      {
        type: 'filter',
        // Filter out null, undefined, NaN
        callback: (d) => d.value != null && !isNaN(d.value) && d.value > 0,
      },
    ],
  },
  encode: { x: 'date', y: 'value' },
});
```

## Multi-Condition Filtering

```javascript
chart.options({
  type: 'point',
  data: {
    type: 'inline',
    value: allData,
    transform: [
      {
        type: 'filter',
        callback: (d) => d.category === 'A' && d.y > 50,
      },
    ],
  },
  encode: { x: 'x', y: 'y', color: 'category' },
});
```

## Used with fetch

```javascript
chart.options({
  type: 'point',
  data: {
    type: 'fetch',
    value: 'https://example.com/data.json',
    transform: [
      {
        type: 'filter',
        callback: (d) => d.value > 100,
      },
    ],
  },
  encode: { x: 'x', y: 'y' },
});
```

## Multiple Data Transformations Combination

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: rawData,
    transform: [
      { type: 'filter', callback: (d) => d.value != null },
      { type: 'sort', callback: (a, b) => b.value - a.value },
      { type: 'slice', start: 0, end: 10 },  // Take only the first 10 items
    ],
  },
  encode: { x: 'category', y: 'value' },
});
```

## Configuration Options

| Property | Description                              | Type                                           | Default Value                                               |
| -------- | ---------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| callback | Filter function, returns true to keep the row data | `(d: any, idx: number, arr: any[]) => boolean` | `(d) => d !== undefined && d !== null && !Number.isNaN(d)` |

## Common Errors and Fixes

### Error 1: Placing `filter` in `mark transform`

```javascript
// ❌ Incorrect: `filter` is a data transformation and cannot be placed in `mark`'s `transform`
chart.options({
  type: 'interval',
  data: myData,
  transform: [{ type: 'filter', callback: (d) => d.value > 100 }],  // ❌ Incorrect location
});

// ✅ Correct: Place `filter` in `data.transform`
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: myData,
    transform: [{ type: 'filter', callback: (d) => d.value > 100 }],  // ✅ Correct
  },
});
```

### Error 2: callback is not a function

```javascript
// ❌ Error: callback must be a function
data: {
  transform: [{ type: 'filter', callback: 'value > 100' }],  // ❌ string
}

// ✅ Correct: Use an arrow function
 {
  transform: [{ type: 'filter', callback: (d) => d.value > 100 }],  // ✅
}
```

### Error 3: Shorthand data Cannot Configure transform

```javascript
// ❌ Error: Shorthand data cannot configure transform
chart.options({
  data: myData,  // Shorthand form
  // Unable to add transform
});

// ✅ Correct: Use full data configuration
chart.options({
  data: {
    type: 'inline',
    value: myData,
    transform: [{ type: 'filter', callback: (d) => d.value > 100 }],
  },
});
```