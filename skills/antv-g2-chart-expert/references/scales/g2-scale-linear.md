---
id: "g2-scale-linear"
title: "G2 Linear Scale"
description: |
  G2 v5 linear scale is used for mapping continuous numerical fields. It can be configured via scale.y or scale.color,
  supporting custom domain (data range) and range (visual range).
  nice/clamp/tickCount controls the display of axis ticks.
library: "g2"
version: "5.x"
category: "scales"
tags:
  - "linear scale"
  - "linear"
  - "continuous"
  - "numerical"
  - "domain"
  - "range"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-mark-line-basic"
  - "g2-comp-annotation"

use_cases:
  - "Control the display range of the Y-axis (not starting from 0)"
  - "Set color mapping to a continuous color palette"
  - "Clamp to truncate data exceeding the range"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale"
---

## Basic Usage (Custom Y-axis Domain)

By default, the y-axis of a line chart starts from 0. Use `scale.y.domain` to specify an exact range, making the line details clearer:

> **Note**: `linear` is the default scale type for numerical fields, so **there is no need to manually specify `type: 'linear'`**.

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'line',
  data: [
    { month: 'Jan', value: 4200 },
    { month: 'Feb', value: 4500 },
    { month: 'Mar', value: 4100 },
    { month: 'Apr', value: 4800 },
    { month: 'May', value: 5200 },
    { month: 'Jun', value: 4900 },
  ],
  encode: { x: 'month', y: 'value' },
  scale: {
    y: {
      domain: [3800, 5500],   // Explicitly specify the y-axis range, not starting from 0
      nice: true,             // Automatically extend to "nice" integer ticks
    },
  },
});

chart.render();
```

## Log Scale

When data spans multiple orders of magnitude, use `type: 'log'` to compress the y-axis into a logarithmic scale:

```javascript
chart.options({
  type: 'line',
  data: [
    { year: '2018', revenue: 1200 },
    { year: '2019', revenue: 8500 },
    { year: '2020', revenue: 32000 },
    { year: '2021', revenue: 210000 },
    { year: '2022', revenue: 1500000 },
  ],
  encode: { x: 'year', y: 'revenue' },
  scale: {
    y: {
      type: 'log',      // Logarithmic scale, suitable for cross-order-of-magnitude data
      base: 10,         // Logarithmic base, default is 10
      nice: true,
    },
  },
});
```

> Note: Log scale cannot contain 0 or negative numbers, as it will result in rendering anomalies.

## Color Mapping: Sequential Color Scale

Map numerical fields to a continuous color scale, suitable for heatmaps or bubble chart coloring:

```javascript
chart.options({
  type: 'point',
  data: [
    { x: 10, y: 20, density: 0.1 },
    { x: 30, y: 50, density: 0.5 },
    { x: 60, y: 80, density: 0.9 },
    { x: 45, y: 35, density: 0.3 },
    { x: 75, y: 60, density: 0.7 },
  ],
  encode: { x: 'x', y: 'y', color: 'density', size: 12 },
  scale: {
    color: {
      type: 'linear',
      domain: [0, 1],                           // Data range
      range: ['#d0e8ff', '#0050b3'],            // From light blue to dark blue
    },
  },
});
```

## Configuration Reference

| Property | Type | Default Value | Description |
|------|------|--------|------|
| `type` | `'linear'` \| `'log'` \| `'pow'` \| `'sqrt'` | `'linear'` | Scale type |
| `domain` | `[number, number]` | Data's min/max | Data mapping range (input domain) |
| `range` | `[number, number]` \| `string[]` | Depends on channel | Visual mapping range (output domain) |
| `nice` | `boolean` | `false` | Automatically extend domain to integer ticks |
| `clamp` | `boolean` | `false` | Clamp values outside domain to boundaries |
| `tickCount` | `number` | Auto | Desired number of ticks (approximate) |
| `tickInterval` | `number` | Auto | Fixed interval between adjacent ticks |
| `tickMethod` | `function` | Built-in method | Custom tick generation method |
| `base` | `number` | `10` | Only valid for `type: 'log'`, logarithmic base |
| `exponent` | `number` | `2` | Only valid for `type: 'pow'`, exponent |
| `zero` | `boolean` | `true` | Whether to force domain to include 0 |

```javascript
// Complete configuration example
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  scale: {
    y: {
      // type: 'linear',  // Can be omitted, numeric fields default to linear
      domain: [0, 1000],
      nice: true,
      clamp: true,
      tickCount: 5,
      // tickInterval: 200,  // Either tickCount or tickInterval
      zero: false,           // Do not force starting from 0
    },
  },
});
```

## tickMethod Custom Tick

`tickMethod` is used for custom tick generation, with the signature `(min, max, count) => number[]`:

```javascript
scale: {
  y: {
    tickCount: 5,
    tickMethod: (min, max, count) => {
      // Parameter description:
      // min - Minimum data value
      // max - Maximum data value
      // count - Recommended number of ticks

      // Custom tick generation logic
      const step = (max - min) / (count - 1);
      const ticks = [];
      for (let i = 0; i < count; i++) {
        ticks.push(min + i * step);
      }
      return ticks;  // Return a numeric array
    },
  },
}
```

**Note**: If you only need to format the tick label text, use `axis.labelFormatter`:

```javascript
axis: {
  y: {
    labelFormatter: (v) => `${v}万`,  // Format label
  },
}
```
## Common Errors and Fixes

### Error: Forgetting to Set `nice: true` Causes Uneven Ticks

```javascript
// ❌ Ticks may appear as non-integers like 3827, 4183
chart.options({
  scale: { y: { domain: [3827, 5243] } },
});

// ✅ nice: true automatically extends to integer ticks like 3800, 5400
chart.options({
  scale: { y: { domain: [3827, 5243], nice: true } },
});
```

### Error: Minimum value of domain is greater than the maximum value (reversed axis)

```javascript
// ❌ Reversing the domain will cause the axis direction to flip (usually not the expected effect)
chart.options({
  scale: { y: { domain: [1000, 0] } },
});

// ✅ Correct: Minimum value first, maximum value last
chart.options({
  scale: { y: { domain: [0, 1000] } },
});
```

### Error: Using log scale with 0 or negative values

```javascript
// ❌ log(0) = -Infinity, causing rendering anomalies or blank charts
chart.options({
  data: [{ x: 'A', y: 0 }, { x: 'B', y: 100 }],
  scale: { y: { type: 'log' } },
});

// ✅ Ensure all y values > 0, or preprocess data for filtering
chart.options({
  data: data.filter(d => d.y > 0),
  scale: { y: { type: 'log', domain: [1, 1000000] } },
});
```

### Error: Both `tickCount` and `tickInterval` are set simultaneously

```javascript
// ❌ When both are set, `tickInterval` takes precedence, and `tickCount` is ignored
chart.options({
  scale: { y: { tickCount: 5, tickInterval: 200 } },
});

// ✅ Choose one based on requirements
chart.options({
  scale: { y: { tickCount: 5 } },      // Approximately 5 ticks
  // or
  // scale: { y: { tickInterval: 200 } },  // One tick every 200 units
});
```