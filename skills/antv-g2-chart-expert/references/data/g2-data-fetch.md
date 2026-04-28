---
id: "g2-data-fetch"
title: "G2 Fetch Remote Data Acquisition"
description: |
  The Fetch data connector retrieves data from remote interfaces, supporting parsing of formats such as JSON and CSV.
  Enable it by setting data.type to 'fetch', making the data source dynamic.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "fetch"
  - "remote data"
  - "JSON"
  - "CSV"
  - "data connector"
  - "connector"

related:
  - "g2-data-filter"
  - "g2-data-fold"

use_cases:
  - "Fetching dynamic data from APIs"
  - "Loading remote CSV files"
  - "Large screen monitoring data display"

difficulty: "beginner"
completeness: "full"
created: "2025-03-27"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/data/fetch"
---

## Core Concepts

**Fetch is a Data Connector, not a Data Transformer**

- Enabled by setting `data.type: 'fetch'`
- Supports automatic parsing of JSON and CSV formats
- Remote URLs cannot be configured with authentication

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

chart.options({
  type: 'point',
  data: {
    type: 'fetch',
    value: 'https://gw.alipayobjects.com/os/antvdemo/assets/data/scatter.json',
  },
  encode: {
    x: 'weight',
    y: 'height',
    color: 'gender',
  },
});

chart.render();
```

## Configuration Options

| Property | Description                                              | Type               | Default Value                         |
| -------- | -------------------------------------------------------- | ------------------ | ------------------------------------- |
| value    | Network address for the fetch request                    | `string`           | -                                     |
| format   | Data format type of the remote file, determines parsing method | `'json' \| 'csv'`  | Default is the suffix after the last `.` in `value` |
| delimiter | If it's a CSV file, the delimiter used during parsing    | `string`           | `,`                                   |
| autoType | If it's a CSV file, whether to automatically determine column data types during parsing | `boolean`          | `true`                                |
| transform | Transformation operations applied to the loaded data     | `DataTransform[]`  | `[]`                                  |

## Load CSV File

```javascript
chart.options({
  type: 'line',
  {
    type: 'fetch',
    value: 'https://example.com/data.csv',
    format: 'csv',           // Specify format
    delimiter: ',',          // Delimiter
    autoType: true,          // Automatically infer type
    transform: [
      { type: 'filter', callback: (d) => d.value > 0 },
    ],
  },
  encode: { x: 'date', y: 'value' },
});
```

## Using with transform

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'fetch',
    value: 'https://example.com/sales.json',
    transform: [
      { type: 'filter', callback: (d) => d.year === 2024 },
      { type: 'sortBy', fields: [['amount', false]] },
      { type: 'slice', end: 10 },
    ],
  },
  encode: { x: 'product', y: 'amount' },
});
```

## Common Errors and Fixes

### Error 1: Remote Address Requires Authentication

```javascript
// ❌ Error: G2 fetch does not support authentication
data: {
  type: 'fetch',
  value: 'https://api.example.com/private-data',  // Requires token
}

// ✅ Correct: Use a public API or server-side proxy
 {
  type: 'fetch',
  value: 'https://public-api.example.com/data',  // No authentication required
}
```

### Error 2: Mismatch Between `format` and File Format

```javascript
// ❌ Error: `format` does not match the actual file format
data: {
  type: 'fetch',
  value: 'https://example.com/data.json',
  format: 'csv',  // ❌ Actual format is JSON
}

// ✅ Correct: Let G2 infer or specify the correct format
{
  type: 'fetch',
  value: 'https://example.com/data.json',
  // format defaults to 'json' based on the file extension
}

// Or explicitly specify
{
  type: 'fetch',
  value: 'https://example.com/api/data',  // No file extension
  format: 'json',  // Explicitly specified
}
```

### Error 3: CORS Issue

```javascript
// ❌ Error: Cross-origin request blocked
// The browser console will display a CORS error

// ✅ Solution:
// 1. Configure CORS headers on the server
// 2. Use same-origin requests
// 3. Use a proxy server
```