---
id: "g2-mark-k-chart"
title: "G2 K-Chart (Candlestick) Mark"
description: |
  Candlestick Mark. Uses a combination of link and interval to display price trends for financial data such as stocks.
  Suitable for stock analysis, futures trading, digital currency analysis, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "K-Chart"
  - "Candlestick"
  - "candlestick"
  - "stocks"

related:
  - "g2-mark-line-basic"
  - "g2-mark-boxplot"

use_cases:
  - "Stock price analysis"
  - "Futures trading"
  - "Digital currency analysis"

anti_patterns:
  - "Not suitable for non-time series data"
  - "Single value display should use line charts"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/candlestick"
---

## Core Concepts

K-line charts display price trends of financial data:
- Use `link` markers to represent shadows (high/low prices)
- Use `interval` markers to represent entities (open/close prices)
- Colors distinguish between rises and falls

**Four Price Data:**
- Open price (start)
- Close price (end)
- High price (max)
- Low price (min)

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

const data = [
  { time: '2015-11-19', start: 8.18, max: 8.33, min: 7.98, end: 8.32 },
  { time: '2015-11-18', start: 8.37, max: 8.6, min: 8.03, end: 8.09 },
  { time: '2015-11-17', start: 8.7, max: 8.78, min: 8.32, end: 8.37 },
  { time: '2015-11-16', start: 8.48, max: 8.85, min: 8.43, end: 8.7 },
];

chart.options({
  type: 'view',
  data,
  encode: {
    x: 'time',
    color: (d) => (d.start > d.end ? 'Decline' : 'Rise'),
  },
  scale: {
    color: { domain: ['Decline', 'Rise'], range: ['#4daf4a', '#e41a1c'] },
  },
  children: [
    // Shadow line (highest/lowest price)
    {
      type: 'link',
      encode: { y: ['min', 'max'] },
    },
    // Entity (opening/closing price)
    {
      type: 'interval',
      encode: { y: ['start', 'end'] },
      style: { fillOpacity: 1 },
    },
  ],
});

chart.render();
```

## Common Variants

### With Trading Volume

```javascript
// Candlestick Chart
const kChart = new Chart({ container: 'kChart' });
kChart.options({
  type: 'view',
  data,
  encode: { x: 'time', color: (d) => d.start > d.end ? 'Decline' : 'Rise' },
  children: [
    { type: 'link', encode: { y: ['min', 'max'] } },
    { type: 'interval', encode: { y: ['start', 'end'] } },
  ],
});

// Volume Chart
const volumeChart = new Chart({ container: 'volumeChart' });
volumeChart.options({
  type: 'interval',
  data,
  encode: {
    x: 'time',
    y: 'volume',
    color: (d) => d.start > d.end ? 'Decline' : 'Rise',
  },
});
```

### Spec Mode

```javascript
chart.options({
  type: 'view',
  data,
  encode: {
    x: 'time',
    color: (d) => d.start > d.end ? 'Decline' : 'Rise',
  },
  scale: {
    color: { domain: ['Decline', 'Rise'], range: ['#4daf4a', '#e41a1c'] },
  },
  children: [
    {
      type: 'link',
      encode: { y: ['min', 'max'] },
    },
    {
      type: 'interval',
      encode: { y: ['start', 'end'] },
      style: { fillOpacity: 1 },
    },
  ],
});
```

### With Axis Title

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'link', encode: { y: ['min', 'max'] } },
    {
      type: 'interval',
      encode: { y: ['start', 'end'] },
      axis: {
        y: { title: 'Price' },
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface KChartData {
  time: string;      // Time
  start: number;     // Open price
  end: number;       // Close price
  max: number;       // Highest price
  min: number;       // Lowest price
  volume?: number;   // Trading volume (optional)
}

// K-line chart consists of two layers:
// 1. link - Shadow line (highest/lowest price)
// 2. interval - Entity (open/close price)
```

## K-Line Chart vs Line Chart

| Feature | K-Line Chart | Line Chart |
|---------|-------|--------|
| Data Volume | Four Price Data | Single Price |
| Use Case | Technical Analysis | Trend Display |
| Complexity | Higher | Simple |

## Common Errors and Fixes

### Error 1: Missing link Mark

```javascript
// ❌ Issue: Only entities, no shadow lines
chart.options({
  type: 'interval',
  encode: { y: ['start', 'end'] },
});

// ✅ Correct: Use view to combine link and interval
chart.options({
  type: 'view',
  children: [
    { type: 'link', encode: { y: ['min', 'max'] } },
    { type: 'interval', encode: { y: ['start', 'end'] } },
  ],
});
```

### Error 2: Incorrect Color Encoding

```javascript
// ❌ Issue: Incorrect color field
encode: { color: 'time' }

// ✅ Correct: Set color based on increase or decrease
encode: { color: (d) => d.start > d.end ? 'Decline' : 'Increase' }
```

### Error 3: Incorrect Data Order

```javascript
// ⚠️ Note: Time data needs to be correctly sorted
scale: {
  x: {
    compare: (a, b) => new Date(a).getTime() - new Date(b).getTime(),
  },
}
```