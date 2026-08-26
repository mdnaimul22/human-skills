---
id: "g2-scale-pow-sqrt"
title: "G2 Power Scale (pow) and Square Root Scale (sqrt)"
description: |
  The pow scale maps numerical values according to a power function (y = x^exponent), where exponent=0.5 is equivalent to the sqrt scale.
  sqrt is a special case of pow (exponent=0.5), mapping values to their square roots,
  commonly used in area encoding (e.g., bubble sizes) to ensure visual area is linearly proportional to the value.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "pow"
  - "sqrt"
  - "power"
  - "square root"
  - "scale"
  - "bubble chart"

related:
  - "g2-scale-log"
  - "g2-scale-linear"
  - "g2-mark-point-bubble"

use_cases:
  - "Using sqrt scale for the size channel in bubble charts (ensuring linear area)"
  - "Using pow to stretch/compress value ranges when data is slightly skewed"
  - "Linear mapping of area to value in visual encoding"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/pow"
---

## Minimum Viable Example (Bubble Chart with Sqrt Scale)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { country: 'China', gdp: 17.7, population: 141 },
  { country: 'United States', gdp: 25.5, population: 33 },
  { country: 'India', gdp: 3.4,  population: 142 },
  { country: 'Japan', gdp: 4.2,  population: 13 },
  { country: 'Brazil', gdp: 1.8,  population: 22 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: {
    x: 'gdp',
    y: 'country',
    size: 'population',
    color: 'country',
  },
  scale: {
    size: {
      type: 'sqrt',        // Sqrt scale: area is linearly proportional to population
      range: [8, 60],      // Radius range
    },
  },
  style: { fillOpacity: 0.7 },
});

chart.render();
```

## pow Scale (Custom Exponent)

```javascript
// exponent = 2: Larger values amplify differences (suitable for displaying small differences)
scale: {
  y: {
    type: 'pow',
    exponent: 2,    // y = x^2, amplifies differences between large values
  },
}

// exponent = 0.5: Equivalent to sqrt (compresses large values)
scale: {
  y: {
    type: 'pow',
    exponent: 0.5,  // Equivalent to type: 'sqrt'
  },
}
```

## Why Use Sqrt for Bubble Size

```javascript
// ❌ Wrong: Using linear scale to map radius
// Radius r is linearly proportional to the value, so area = πr², area is quadratically related to the value
// Population 100 and 400, visual area ratio is 1:16, misleading the reader
scale: { size: { type: 'linear', range: [8, 60] } }  // ❌

// ✅ Correct: Using sqrt scale to map radius
// Radius r = sqrt(value), area = πr² = π×value, area is linearly related to the value
// Population 100 and 400, visual area ratio is 1:4, consistent with actual proportions
scale: { size: { type: 'sqrt', range: [8, 60] } }  // ✅
```

## Common Errors and Fixes

### Error: Data contains 0 or negative numbers and exponent < 1——sqrt(0) = 0 is normal, but negative numbers will result in NaN
```javascript
// ❌ sqrt(-1) = NaN, an error will occur if there are negative numbers in the data
chart.options({
  scale: { y: { type: 'sqrt' } },
   [{ y: -10 }],  // ❌ Negative number
});

// ✅ The sqrt scale is only applicable to non-negative numbers
// If there are negative numbers, process them with Math.abs first, or switch to linear
chart.options({
  scale: { y: { type: 'sqrt', domain: [0, 200] } },  // ✅ Ensure domain is non-negative
});
```