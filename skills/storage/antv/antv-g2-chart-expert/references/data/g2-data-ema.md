---
id: "g2-data-ema"
title: "G2 EMA Exponential Moving Average"
description: |
  EMA (Exponential Moving Average) data transformation applies exponential moving average smoothing to the data.
  By assigning higher weights to more recent data points, it reduces data volatility and allows for clearer trend observation.
  Configured in data.transform.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "ema"
  - "exponential moving average"
  - "smoothing"
  - "trend"
  - "data transformation"
  - "data transform"

related:
  - "g2-mark-line"

use_cases:
  - "Time series data smoothing"
  - "Financial data technical analysis"
  - "Training metric smoothing display"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-27"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/ema"
---

## Core Concepts

**EMA is a Data Transform, not a Mark Transform**

- Data transform configurations are set in `data.transform`
- Exponential Moving Average (EMA) is a data smoothing algorithm

**Formula**: EMA_t = α × P_t + (1 - α) × EMA_{t-1}

**Notes**:
- In G2, the closer `alpha` is to 1, the more pronounced the smoothing effect
- The closer `alpha` is to 0, the closer EMA is to the original data
- The `field` must be of numeric type

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

const data = [
  { t: 0, y: 100 },
  { t: 1, y: 180 },
  { t: 2, y: 120 },
  { t: 3, y: 200 },
  { t: 4, y: 150 },
  { t: 5, y: 250 },
];

chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data: {
        type: 'inline',
        value: data,
        transform: [
          {
            type: 'ema',
            field: 'y',      // Field to smooth
            alpha: 0.6,      // Smoothing factor
            as: 'emaY',      // Output field name
          },
        ],
      },
      encode: { x: 't', y: 'emaY' },
      style: { stroke: '#f90' },
    },
    {
      type: 'line',
      data: { type: 'inline', value: data },
      encode: { x: 't', y: 'y' },
      style: { stroke: '#ccc', lineDash: [4, 2] },
    },
  ],
});

chart.render();
```

## Configuration Options

| Property | Description                                      | Type     | Default Value | Required |
| -------- | ------------------------------------------------ | -------- | ------------- | -------- |
| field    | The field name that needs to be smoothed         | `string` | `'y'`         | ✓        |
| alpha    | Smoothing factor, controls the degree of smoothing (larger values result in smoother curves) | `number` | `0.6`         |          |
| as       | The name of the new generated field, if not specified, it will overwrite the original field | `string` | Same as `field` |          |

## Financial Market Smoothing

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
       {
        type: 'fetch',
        value: 'https://example.com/stock.csv',
        transform: [
          {
            type: 'ema',
            field: 'close',
            alpha: 0.7,
            as: 'emaClose',
          },
        ],
      },
      encode: { x: 'date', y: 'emaClose' },
      style: { stroke: '#007aff', lineWidth: 2 },
    },
    {
      type: 'line',
       { type: 'fetch', value: 'https://example.com/stock.csv' },
      encode: { x: 'date', y: 'close' },
      style: { stroke: '#bbb', lineDash: [4, 2] },
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Placing EMA in Mark Transform

```javascript
// ❌ Incorrect: EMA is a data transformation and cannot be placed in the mark's transform
chart.options({
  type: 'line',
  data,
  transform: [{ type: 'ema', field: 'y' }],  // ❌ Incorrect location
});

// ✅ Correct: EMA should be placed in data.transform
chart.options({
  type: 'line',
  data: {
    type: 'inline',
    value: data,
    transform: [{ type: 'ema', field: 'y', as: 'emaY' }],  // ✅ Correct
  },
});
```

### Error 2: Field is not numeric

```javascript
// ❌ Error: The field must be numeric
 {
  transform: [{ type: 'ema', field: 'name' }],  // ❌ name is a string
}

// ✅ Correct: Use a numeric field
 {
  transform: [{ type: 'ema', field: 'value' }],
}
```

### Error 3: Forgetting to Set the `as` Field

```javascript
// ⚠️ Caution: Not setting `as` will overwrite the original field
data: {
  transform: [{ type: 'ema', field: 'y' }],  // The `y` field will be overwritten
}
encode: { y: 'y' },  // Uses the smoothed data

// ✅ Recommended: Set `as` to preserve the original field
 {
  transform: [{ type: 'ema', field: 'y', as: 'emaY' }],
}
// Can display both original and smoothed data simultaneously
```