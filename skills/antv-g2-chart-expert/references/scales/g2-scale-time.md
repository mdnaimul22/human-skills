---
id: "g2-scale-time"
title: "G2 Time Scale"
description: |
  The Time scale maps time data (Date objects or timestamps) to a continuous axis,
  automatically handling time tick intervals, formatting, and sorting. It is automatically enabled when encode.x maps Date type data.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "time"
  - "time scale"
  - "time axis"
  - "Date"
  - "time series"
  - "scale"
  - "spec"

related:
  - "g2-mark-line-basic"
  - "g2-comp-axis-config"
  - "g2-scale-linear"

use_cases:
  - "Plotting time series line charts and area charts"
  - "Controlling the granularity and label format of the time axis"
  - "Setting the display range of the time axis"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/time"
---

## Automatic Recognition (Recommended)

When the data field is a `Date` object, G2 automatically uses the Time Scale without the need for explicit configuration:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 700, height: 400 });

chart.options({
  type: 'line',
  data: [
    { date: new Date('2024-01-01'), value: 100 },
    { date: new Date('2024-02-01'), value: 130 },
    { date: new Date('2024-03-01'), value: 110 },
    { date: new Date('2024-04-01'), value: 160 },
    { date: new Date('2024-05-01'), value: 145 },
  ],
  encode: { x: 'date', y: 'value' },   // Date objects automatically use Time Scale
});

chart.render();
```

## Explicitly Configure Time Scale

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  scale: {
    x: {
      type: 'time',               // Explicitly specify (required for string dates)
      domain: [                   // Limit display range
        new Date('2024-01-01'),
        new Date('2024-12-31'),
      ],
      nice: true,                  // Extend domain to neat time boundaries
    },
  },
});
```

## Formatting Time Axis Labels

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  axis: {
    x: {
      // Use dayjs format string
      labelFormatter: 'YYYY-MM',           // Year-Month: 2024-01
      // labelFormatter: 'MM/DD',          // Month/Day: 01/15
      // labelFormatter: 'YYYY年MM月',     // Chinese format
      // labelFormatter: (d) => `Q${Math.ceil((d.getMonth()+1)/3)}`,  // Custom
      tickCount: 6,
    },
  },
});
```
## String Dates (Recommended to Convert to Date Objects)

G2 v5 has some automatic recognition capability for string dates in the `YYYY-MM-DD` format, but the behavior relies on internal inference and is **unstable**.
It is recommended to uniformly convert to `Date` objects during the data preprocessing stage to avoid ambiguity:

```javascript
// ✅ Recommended: Convert to Date objects during preprocessing
const rawData = [
  { date: '2024-01-01', value: 100 },
  { date: '2024-02-01', value: 130 },
];
const data = rawData.map(d => ({ ...d, date: new Date(d.date) }));

chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  // No need for scale.x.type, G2 automatically recognizes Date objects as Time Scale
});
```

**Do not** explicitly write `scale: { x: { type: 'time' } }` on string dates, as this is redundant configuration and can cause rendering anomalies in certain scenarios (such as data type changes after fold).

## Common Errors and Fixes

### Error 1: Explicitly Declaring `type: 'time'` (Unnecessary and Risky)
```javascript
// ❌ Not Recommended: Explicitly writing `type: 'time'` on string dates
chart.options({
  type: 'line',
  data: [{ date: '2024-01-01', value: 100 }],
  encode: { x: 'date', y: 'value' },
  scale: { x: { type: 'time' } },   // ❌ Redundant, may cause exceptions
});

// ✅ Correct: Convert to Date objects and let G2 handle it automatically
const data = rawData.map(d => ({ ...d, date: new Date(d.date) }));
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
});
```

### Error 2: Data Disorder Causes Line Chart Confusion
```javascript
// ❌ Incorrect: Data order is chaotic, leading to incorrect line connections
const data = [
  { date: new Date('2024-03-01'), value: 110 },
  { date: new Date('2024-01-01'), value: 100 },  // Reverse chronological order
];

// ✅ Correct: Sort data by date before passing it in
const data = rawData
  .map(d => ({ ...d, date: new Date(d.date) }))
  .sort((a, b) => a.date - b.date);
```