---
id: "g2-data-fold"
title: "G2 Fold Wide to Long Table Transformation"
description: |
  The Fold data transformation converts wide-format data (multiple columns) into long-format data (single column + category column),
  allowing multiple fields to be mapped to the same color/series channel.
  Configured in data.transform, it is a common data preprocessing method for implementing multi-series charts in G2.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "fold"
  - "wide to long table"
  - "pivot"
  - "multi-series"
  - "data transformation"
  - "data transform"

related:
  - "g2-data-filter"
  - "g2-data-sort"
  - "g2-mark-line-basic"
  - "g2-mark-area-stacked"

use_cases:
  - "Convert wide table multi-column data into a multi-series line chart"
  - "Merge multiple fields of the same metric into a single series field"
  - "Reduce manual flatMap data preprocessing code"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/fold"
---

## Core Concepts

**Fold is a Data Transform, not a Mark Transform**

- Data transform configurations are set in `data.transform`
- Executed during the data loading phase, affecting all marks using that data

**Wide Table (Wide)**: Each metric occupies one column
```
month | revenue | cost | profit
Jan   | 320     | 200  | 120
Feb   | 450     | 230  | 220
```

**Long Table (Long/Tidy)**: All metric values merged into one column, with an added category column
```
month | key     | value
Jan   | revenue | 320
Jan   | cost    | 200
Jan   | profit  | 120
Feb   | revenue | 450
...
```

G2's `fold` data transform automatically completes this conversion, eliminating the need for manual `flatMap`.

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

// Wide table data (each metric is an independent column)
const wideData = [
  { month: 'Jan', revenue: 320, cost: 200, profit: 120 },
  { month: 'Feb', revenue: 450, cost: 230, profit: 220 },
  { month: 'Mar', revenue: 380, cost: 210, profit: 170 },
  { month: 'Apr', revenue: 510, cost: 260, profit: 250 },
];

chart.options({
  type: 'line',
  data: {
    type: 'inline',
    value: wideData,
    transform: [
      {
        type: 'fold',
        fields: ['revenue', 'cost', 'profit'],  // Columns to fold
        key: 'key',      // Generated key column name (default 'key')
        value: 'value',  // Generated value column name (default 'value')
      },
    ],
  },
  encode: {
    x: 'month',
    y: 'value',     // Value column after fold
    color: 'key',   // Key column after fold
  },
});

chart.render();
```

## Using fold in Stacked Area Charts

```javascript
chart.options({
  type: 'area',
  data: {
    type: 'inline',
    value: wideData,
    transform: [
      { type: 'fold', fields: ['revenue', 'cost', 'profit'] },
    ],
  },
  encode: { x: 'month', y: 'value', color: 'key' },
  transform: [{ type: 'stackY' }],  // mark transform
});
```

## Equivalent Manual Approach (For Comparison)

```javascript
// Without fold, manually flatMap (more verbose code)
const longData = wideData.flatMap((d) => [
  { month: d.month, metric: 'revenue', value: d.revenue },
  { month: d.month, metric: 'cost',    value: d.cost    },
  { month: d.month, metric: 'profit',  value: d.profit  },
]);

chart.options({
  type: 'line',
  data: longData,
  encode: { x: 'month', y: 'value', color: 'metric' },
});
```

## Configuration Options

| Property | Description                          | Type       | Default Value |
| -------- | ------------------------------------ | ---------- | ------------- |
| fields   | List of fields that need to be expanded | `string[]` |               |
| key      | Field name corresponding to the enumeration value after expansion | `string`   | `key`         |
| value    | Field name corresponding to the data value after expansion | `string`   | `value`       |

## Common Errors and Fixes

### Error 1: Placing `fold` in `mark` transform

```javascript
// ❌ Incorrect: `fold` is a data transformation and cannot be placed in `mark`'s transform
chart.options({
  type: 'line',
  wideData,
  transform: [{ type: 'fold', fields: ['a', 'b'] }],  // ❌ Incorrect location
});

// ✅ Correct: `fold` should be placed in `data.transform`
chart.options({
  type: 'line',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['a', 'b'] }],  // ✅ Correct
  },
});
```

### Error 2: Incorrect Spelling of Field Names in `fields`

```javascript
// ❌ Incorrect: Field names do not match the data, resulting in undefined values after folding
data: {
  transform: [{ type: 'fold', fields: ['Revenue', 'Cost'] }],  // Capitalized, but data is in lowercase
}

// ✅ Correct: Field names must exactly match the keys in the data object (case-sensitive)
data: {
  transform: [{ type: 'fold', fields: ['revenue', 'cost'] }],
}
```

### Error 3: Mismatch between y/color field names in encode and as configuration

```javascript
// ❌ Error: fold generates 'key'/'value' columns by default, but encode uses different names
chart.options({
  data: {
    transform: [{ type: 'fold', fields: ['a', 'b'] }],  // Generates key/value by default
  },
  encode: { y: 'metric', color: 'series' },  // Error: Field names do not exist
});

// ✅ Correct: encode names match the key/value configuration of fold
chart.options({
  data: {
    transform: [{ type: 'fold', fields: ['a', 'b'], key: 'metric', value: 'amount' }],
  },
  encode: { y: 'amount', color: 'metric' },
});
```

### Error 4: Shorthand data cannot configure transform

```javascript
// ❌ Error: Shorthand data cannot configure transform
chart.options({
   wideData,  // Shorthand form
  // Unable to add fold transform
});

// ✅ Correct: Use complete data configuration
chart.options({
   {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['revenue', 'cost'] }],
  },
});
```

### Error 5: Missing `` Keyword——SyntaxError

This is a very common error during code generation: the `data` property value is a multi-line nested object, and it's easy to forget to write the `data:` key, resulting in a JavaScript syntax error (`Unexpected token '{'`), causing the chart to fail completely.

```javascript
// ❌ Error: Missing key name, { type: 'inline', ... } is an isolated object literal → SyntaxError
chart.options({
  type: 'interval',
  {                          // ❌ Syntax error! Missing data: prefix
    type: 'inline',
    value: populationData,
    transform: [{
      type: 'fold',
      fields: ['Under 5 Years', '5 to 13 Years'],
      key: 'AgeGroup',
      value: 'Population',
    }]
  },
  encode: { x: 'State', y: 'Population', color: 'AgeGroup' },
});

// ✅ Correct: Must include data: key name
chart.options({
  type: 'interval',
  data: {                    // ✅ Cannot omit
    type: 'inline',
    value: populationData,
    transform: [{
      type: 'fold',
      fields: ['Under 5 Years', '5 to 13 Years'],
      key: 'AgeGroup',
      value: 'Population',
    }]
  },
  encode: { x: 'State', y: 'Population', color: 'AgeGroup' },
});
```

**Why it's easy to omit**: The `data` value is a multi-line nested object, and during generation, it's easy to treat it as an independent "block" rather than a property of `chart.options({})`, leading to the omission of the `data:` prefix. The same issue occurs with `coordinate:`, `children:`, and other multi-line object properties - whenever the value is a complex object, ensure the key name is complete.