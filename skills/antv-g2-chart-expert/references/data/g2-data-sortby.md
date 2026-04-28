---
id: "g2-data-sortby"
title: "G2 SortBy Field Sorting"
description: |
  The SortBy data transform sorts data according to the specified field.
  Unlike sort, sortBy specifies sorting by field name, making it more concise and intuitive.
  It is configured in data.transform.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "sortBy"
  - "field sorting"
  - "sorting"
  - "data transform"
  - "data transform"

related:
  - "g2-data-sort"
  - "g2-transform-sortx"

use_cases:
  - "Sort by field value"
  - "Multi-field combined sorting"
  - "Ascending/Descending order"

difficulty: "beginner"
completeness: "full"
created: "2025-03-27"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/sortBy"
---

## Core Concepts

**SortBy is a Data Transform, not a Mark Transform**

- Data transforms are configured in `data.transform`
- Specify sorting by field name, more concise than sort

**Differences from sort:**
- `sort`: Uses a callback comparison function
- `sortBy`: Specifies by field name, more concise

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

const data = [
  { genre: 'Sports', sold: 275 },
  { genre: 'Strategy', sold: 115 },
  { genre: 'Action', sold: 120 },
  { genre: 'Shooter', sold: 350 },
  { genre: 'Other', sold: 150 },
];

chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [
      {
        type: 'sortBy',
        fields: ['sold'],  // Sort in ascending order by the 'sold' field
      },
    ],
  },
  encode: { x: 'genre', y: 'sold' },
});

chart.render();
```

## Configuration Options

| Property | Description          | Type                              | Default Value |
| -------- | -------------------- | --------------------------------- | ------------- |
| fields   | Fields to be sorted  | `(string \| [string, boolean])[]` | `[]`          |

## Descending Order

```javascript
chart.options({
  data: {
    type: 'inline',
    value: data,
    transform: [
      {
        type: 'sortBy',
        fields: [['sold', false]],  // false indicates descending order
      },
    ],
  },
});
```

## Multi-field Sorting

```javascript
// First sort by name in ascending order, then by age in descending order when names are the same
chart.options({
  data: {
    type: 'inline',
    value: data,
    transform: [
      {
        type: 'sortBy',
        fields: [
          ['name', true],   // name ascending
          ['age', false],   // age descending
        ],
      },
    ],
  },
});
```

## Comparison with sort

```javascript
// Using sortBy (recommended, more concise)
data: {
  transform: [{ type: 'sortBy', fields: ['value'] }],
}

// Using sort (more flexible)
data: {
  transform: [{ type: 'sort', callback: (a, b) => a.value - b.value }],
}

// sortBy in descending order
data: {
  transform: [{ type: 'sortBy', fields: [['value', false]] }],
}

// sort in descending order
data: {
  transform: [{ type: 'sort', callback: (a, b) => b.value - a.value }],
}
```

## Common Errors and Fixes

### Error 1: sortBy Placed in Mark Transform

```javascript
// ❌ Incorrect: sortBy is a data transformation and cannot be placed in the mark's transform
chart.options({
  type: 'interval',
  data,
  transform: [{ type: 'sortBy', fields: ['value'] }],  // ❌ Incorrect location
});

// ✅ Correct: sortBy should be placed in data.transform
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [{ type: 'sortBy', fields: ['value'] }],  // ✅ Correct
  },
});
```

### Error 2: Non-existent Field Name

```javascript
// ❌ Error: Non-existent field name, sorting is invalid
data: {
  transform: [{ type: 'sortBy', fields: ['nonexistent'] }],
}

// ✅ Correct: Ensure the field name exists
data: {
  transform: [{ type: 'sortBy', fields: ['value'] }],
}
```