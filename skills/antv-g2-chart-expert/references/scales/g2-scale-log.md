---
id: "g2-scale-log"
title: "G2 Logarithmic Scale (log)"
description: |
  The logarithmic scale maps numerical values to a logarithmic scale, suitable for scenarios where data spans multiple orders of magnitude (e.g., 1 to 1,000,000).
  Use the base parameter to set the logarithmic base (default 10), effectively displaying data with exponential growth or significant magnitude differences.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "log"
  - "logarithmic"
  - "scale"
  - "order of magnitude"
  - "exponential growth"

related:
  - "g2-scale-linear"
  - "g2-scale-pow"

use_cases:
  - "Displaying data with significant magnitude differences (e.g., GDP comparison: 1 million to 1 trillion)"
  - "Exponential growth data such as virus transmission"
  - "Power-law characteristics in frequency distributions"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/log"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Data with significant differences in magnitude
const data = [
  { country: 'Luxembourg', gdp: 135000 },
  { country: 'United States', gdp: 65000 },
  { country: 'China', gdp: 12000 },
  { country: 'Brazil', gdp: 7500 },
  { country: 'India', gdp: 2100 },
  { country: 'Ethiopia', gdp: 900 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'country', y: 'gdp', color: 'country' },
  scale: {
    y: {
      type: 'log',    // Logarithmic scale
      base: 10,       // Base, default is 10
      domain: [100, 200000],
    },
  },
  axis: {
    y: {
      title: 'GDP per capita (USD, log scale)',
      tickCount: 5,
    },
  },
});

chart.render();
```

## Configuration Options

```javascript
scale: {
  y: {
    type: 'log',
    base: 10,          // Logarithmic base, commonly 2 or 10, default is 10
    domain: [1, 1e6],  // Value range (Note: cannot include 0 or negative numbers!)
    nice: true,        // Extend ticks to integer powers
    tickCount: 5,      // Recommended number of ticks
    tickMethod: (min, max, count, base) => {
      // Custom tick generation method
      // Return an array of tick values
      return [1, 10, 100, 1000, 10000];
    },
  },
}
```

## Scale Control: tickMethod vs labelFormatter vs tickFormatter

The three have completely different responsibilities and cannot be mixed:

| Configuration | Location | Signature | Responsibility |
|---------------|----------|------------|---------------|
| `tickMethod`  | `scale.y` or `axis.y` | `(min, max, count, base?) => number[]` | Determines **which values** are displayed as ticks |
| `labelFormatter` | `axis.y` | `(value, index, array) => string` | Determines the **display text** of ticks ⭐ Most commonly used |
| `tickFormatter` | `axis.y` | `(datum, index, array, vector) => DisplayObject` | Customizes the **graphic object** of tick lines (rarely used) |

### Format Only the Scale Label Text (Most Common)

```javascript
// ✅ Modify only the displayed text → Use axis.labelFormatter, no need for tickMethod
chart.options({
  scale: { y: { type: 'log', base: 10 } },
  axis: {
    y: {
      labelFormatter: (v) => v >= 1e6 ? `${v/1e6}M` : v >= 1e3 ? `${v/1e3}K` : String(v),
    },
  },
});
```

### Customize Tick Positions and Label Text Simultaneously

```javascript
// ✅ tickMethod controls "which ticks to draw", labelFormatter controls "what text to display"
chart.options({
  scale: {
    y: {
      type: 'log',
      base: 10,
      domain: [0.1, 1000],
      // Signature: (min, max, count, base) => number[], must return a numeric array
      tickMethod: (min, max, count, base) => [0.1, 1, 10, 100, 1000],
    },
  },
  axis: {
    y: {
      labelFormatter: (v) => `10^${Math.log10(v)}`,
    },
  },
});
```

## Line Chart with Logarithmic Axis (Exponential Growth Data)

```javascript
chart.options({
  type: 'line',
  data: covidData,
  encode: { x: 'date', y: 'cases', color: 'country' },
  scale: {
    y: { type: 'log', base: 10, nice: true },
  },
  axis: {
    y: {
      title: 'Cumulative Cases (Logarithmic Axis)',
      labelFormatter: (v) => v >= 1e6 ? `${v / 1e6}M` : v >= 1e3 ? `${v / 1e3}K` : String(v),
    },
  },
});
```

## Common Errors and Fixes

### Error 1: Incorrect `tickMethod` Signature and Confusion Between Tick Position and Label Formatting

`tickMethod` has two configurable locations, with **different signatures and responsibilities**:

| Location       | Signature                          | Responsibility                     |
|----------------|------------------------------------|------------------------------------|
| `scale.y.tickMethod` | `(min, max, n?, base?) => number[]` | Controls the **numeric position** of ticks |
| `axis.y.tickMethod`  | `(start, end, tickCount) => number[]` | Same as above, also returns a numeric array |
| `axis.y.labelFormatter` | `(value) => string`               | Controls the **display text** of ticks |

```javascript
// ❌ Three errors:
// 1. Parameters are written as a scale object (should be four numeric values: min/max/count/base)
// 2. Calls a non-existent scale.ticks() method
// 3. Returns an array of {value, text} objects (should return number[])
scale: {
  y: {
    type: 'log',
    tickMethod: (scale) => {
      const ticks = scale.ticks();
      return ticks.map(tick => ({ value: tick, text: `log10(${tick}) + 1` }));
    },
  },
}

// ✅ Correct separation: tickMethod controls position, labelFormatter controls text
scale: {
  y: {
    type: 'log',
    base: 10,
    domain: [0.1, 1000],
    tickMethod: (min, max, count, base) => [0.1, 1, 10, 100, 1000],  // ✅ Returns number[]
  },
},
axis: {
  y: {
    labelFormatter: (v) => `${Math.log10(v) + 1}`,  // ✅ Formats text
  },
}
```

### Error 2: Data Contains 0 or Negative Numbers—Logarithmic Scales Cannot Handle
```javascript
// ❌ Logarithm log(0) = -∞, data with 0 will cause rendering anomalies
const data = [{ x: 'A', y: 0 }, { x: 'B', y: 100 }];
chart.options({
  scale: { y: { type: 'log' } },  // ❌ y=0 cannot be displayed on a logarithmic axis
});

// ✅ Logarithmic axes require all values > 0, filter out 0 or add a small offset
const data = [{ x: 'B', y: 100 }];  // ✅ Filter out 0
// Or use domain to force the starting point > 0
chart.options({
  scale: { y: { type: 'log', domain: [0.1, 1000] } },
});
```

### Error 3: Using Logarithmic Axis for Linear Data—Visual Distortion
```javascript
// ❌ Data range is 50~200, with no order of magnitude difference, logarithmic axis is meaningless and misleading
const data = [/* uniformly distributed between 50~200 */];
chart.options({ scale: { y: { type: 'log' } } });  // ❌ Unnecessary

// ✅ Use default linear scale for linear data
chart.options({ scale: { y: { type: 'linear' } } });  // ✅ Or omit directly (default)
```