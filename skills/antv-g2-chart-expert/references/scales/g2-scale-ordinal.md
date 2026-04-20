---
id: "g2-scale-ordinal"
title: "G2 Ordinal Scale"
description: |
  The ordinal scale maps discrete categorical values to discrete output values (such as colors).
  It is primarily used in the color channel to map string categories to a color array.
  Customize the color list via `range` or use built-in palettes with `palette`.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "ordinal"
  - "序数"
  - "比例尺"
  - "颜色"
  - "分类色"
  - "scale"
  - "palette"

related:
  - "g2-scale-linear"
  - "g2-theme-builtin"

use_cases:
  - "Custom categorical color mapping"
  - "Assign specific colors to specific categories"
  - "Use built-in or custom color palettes"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/ordinal"
---
## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports', sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action', sold: 120 },
    { genre: 'RPG',  sold: 98 },
  ],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  scale: {
    color: {
      type: 'ordinal',
      // Custom color list (order corresponds to categories in domain)
      range: ['#F4664A', '#FAAD14', '#5B8FF9', '#30BF78'],
    },
  },
});

chart.render();
```

## Specify Category-to-Color Mapping (domain + range)

```javascript
chart.options({
  scale: {
    color: {
      type: 'ordinal',
      domain: ['Pass', 'Fail', 'Skip'],   // Specify category order
      range: ['#52c41a', '#ff4d4f', '#faad14'],  // Corresponding colors
    },
  },
});
```

## Using Built-in Palettes

```javascript
// G2 built-in palette names: 'tableau10', 'category10', 'set2', 'pastel', 'blues', etc.
chart.options({
  scale: {
    color: {
      type: 'ordinal',
      palette: 'tableau10',   // Use Tableau 10 color palette
    },
  },
});
```

## Common Errors and Fixes

### Error 1: Number of range colors is less than the number of categories—later categories reuse colors in a loop
```javascript
// ⚠️  5 categories but only 3 colors, the 4th/5th categories reuse the colors of the first two
chart.options({
  scale: {
    color: {
      type: 'ordinal',
      domain: ['A', 'B', 'C', 'D', 'E'],
      range: ['red', 'blue', 'green'],  // ⚠️  Only 3 colors, D/E will loop
    },
  },
});

// ✅ The number of range colors should be ≥ the number of categories
chart.options({
  scale: {
    color: {
      type: 'ordinal',
      range: ['#F4664A', '#FAAD14', '#5B8FF9', '#30BF78', '#9254DE'],  // ✅ 5 colors
    },
  },
});
```

### Error 2: Misusing ordinal for continuous numerical channels—Use linear or sequential instead
```javascript
// ❌ Using ordinal for numerical y-axis (Y-axis becomes discrete)
chart.options({
  scale: {
    y: { type: 'ordinal' },  // ❌ y is numerical, use linear instead
  },
});

// ✅ Use linear for numerical scales
chart.options({
  scale: {
    y: { type: 'linear' },  // ✅
  },
});
```