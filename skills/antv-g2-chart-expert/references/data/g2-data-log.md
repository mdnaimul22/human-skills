---
id: "g2-data-log"
title: "G2 Log Data"
description: |
  The Log data transform prints the current data in the data transform stream to the console for debugging purposes.
  It is configured in `data.transform` and does not affect the data flow.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "log"
  - "debugging"
  - "logging"
  - "data transform"
  - "data transform"

related:
  - "g2-data-filter"

use_cases:
  - "Debugging data processing flow"
  - "Inspecting intermediate data states"

difficulty: "beginner"
completeness: "full"
created: "2025-03-27"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/log"
---

## Core Concepts

**Log is a Data Transform, not a Mark Transform**

- Data transform configuration is in `data.transform`
- Used for debugging, prints data to the console
- Does not affect the data flow, data is passed as is to the next transform

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

const data = [
  { a: 1, b: 2, c: 3 },
  { a: 4, b: 5, c: 6 },
  { a: 7, b: 8, c: 9 },
];

chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [
      { type: 'slice', start: 1 },  // Slice first
      { type: 'log' },               // Log intermediate result (for debugging)
      { type: 'filter', callback: (d) => d.a < 5 },  // Filter next
    ],
  },
  encode: { x: 'a', y: 'b' },
});

chart.render();
// The console will output the data after slicing
```

## Debugging Data Processing Flow

```javascript
chart.options({
   {
    type: 'fetch',
    value: 'https://example.com/data.json',
    transform: [
      { type: 'filter', callback: (d) => d.value > 100 },
      { type: 'log' },  // Check filtered data
      { type: 'sort', callback: (a, b) => b.value - a.value },
      { type: 'log' },  // Check sorted data
      { type: 'slice', end: 10 },
    ],
  },
});
```

## Configuration Options

The Log transformation has no configuration options and can be used directly.

```javascript
{ type: 'log' }
```

## Common Errors and Fixes

### Error 1: Placing `log` in `mark transform`

```javascript
// ❌ Incorrect: `log` is a data transformation and cannot be placed in `mark`'s `transform`
chart.options({
  type: 'interval',
  data,
  transform: [{ type: 'log' }],  // ❌ Incorrect location
});

// ✅ Correct: Place `log` in `data.transform`
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [{ type: 'log' }],  // ✅ Correct
  },
});
```

### Notes

```javascript
// ⚠️ Note: Remove log transformation in production environment to avoid unnecessary console output
// Development environment
 {
  transform: [
    { type: 'filter', callback: (d) => d.value > 0 },
    { type: 'log' },  // For debugging
  ],
}

// Production environment
 {
  transform: [
    { type: 'filter', callback: (d) => d.value > 0 },
    // Remove log
  ],
}
```