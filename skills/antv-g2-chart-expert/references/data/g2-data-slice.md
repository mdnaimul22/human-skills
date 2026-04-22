---
id: "g2-data-slice"
title: "G2 Slice Data Slice"
description: |
  The Slice data transform slices the data to obtain a subset.
  Similar to Array.prototype.slice, it is configured in data.transform.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "slice"
  - "data slice"
  - "pagination"
  - "data transform"

related:
  - "g2-data-filter"
  - "g2-data-sort"

use_cases:
  - "Data pagination display"
  - "Retrieve only the first N data items"
  - "Extract data within a specific range"

difficulty: "beginner"
completeness: "full"
created: "2025-03-27"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/slice"
---

## Core Concepts

**Slice is a Data Transform, not a Mark Transform**

- Data transform configurations are set in `data.transform`
- Similar to [Array.prototype.slice](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/slice)

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

const data = [
  { month: 'Jan', value: 100 },
  { month: 'Feb', value: 120 },
  { month: 'Mar', value: 150 },
  { month: 'Apr', value: 180 },
  { month: 'May', value: 200 },
];

chart.options({
  type: 'line',
  data: [
    {
      type: 'inline',
      value: data,
      transform: [
        {
          type: 'slice',
          start: 0,
          end: 3,  // Only take the first 3 data points
        },
      ],
    },
  ],
  encode: { x: 'month', y: 'value' },
});

chart.render();
```

## Configuration Options

| Property | Description          | Type     | Default Value       |
| -------- | -------------------- | -------- | ------------------- |
| start    | Start index of slice | `number` | `0`                 |
| end      | End index of slice   | `number` | `arr.length - 1`    |

## Take the Top N Data Points

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: largeData,
    transform: [
      { type: 'sort', callback: (a, b) => b.value - a.value },  // Sort first
      { type: 'slice', end: 10 },  // Take the top 10
    ],
  },
  encode: { x: 'category', y: 'value' },
});
```

## Pagination Effect

```javascript
// Page 2, 10 items per page
const page = 2;
const pageSize = 10;

chart.options({
  data: {
    transform: [
      { type: 'slice', start: (page - 1) * pageSize, end: page * pageSize },
    ],
  },
});
```

## Common Errors and Fixes

### Error 1: slice placed in mark transform

```javascript
// ❌ Incorrect: slice is a data transformation and cannot be placed in the mark's transform
chart.options({
  type: 'interval',
  data,
  transform: [{ type: 'slice', end: 10 }],  // ❌ Incorrect location
});

// ✅ Correct: slice placed in data.transform
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [{ type: 'slice', end: 10 }],  // ✅ Correct
  },
});
```

### Error 2: Index Out of Range

```javascript
// ⚠️ Note: If the index is out of range, G2 will handle it automatically and will not throw an error
data: {
  transform: [{ type: 'slice', start: 100, end: 200 }],  // There are only 50 data entries
}
// Result: Returns an empty array
```