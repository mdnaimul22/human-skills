---
id: "g2-palette-category10"
title: "G2 Category10 Palette"
description: |
  AntV's classic 10-color palette, used for color mapping in categorical data.
  Includes 10 carefully designed colors, suitable for most categorical visualization scenarios.

library: "g2"
version: "5.x"
category: "palette"
tags:
  - "palette"
  - "color"
  - "category"
  - "10-color"

related:
  - "g2-palette-category20"
  - "g2-scale-ordinal"
  - "g2-theme-builtin"

use_cases:
  - "Default colors for categorical data"
  - "Color mapping for bar charts and line charts"
  - "Scenarios requiring 10 or fewer colors"

anti_patterns:
  - "For more than 10 categories, consider Category20 or custom palettes"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/palette"
---
## Core Concepts

Category10 is the default categorical color palette of AntV:
- Contains 10 colors
- Colors are carefully designed for easy distinction
- Suitable for most categorical visualization scenarios

**Color List:**
```
#5B8FF9  - Blue
#5AD8A6  - Green
#5D7092  - Grayish Blue
#F6BD16  - Yellow
#6F5EF9  - Purple
#6DC8EC  - Cyan
#945FB9  - Dark Purple
#FF9845  - Orange
#1E9493  - Dark Cyan
#FF99C3  - Pink
```

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { category: 'A', value: 100 },
    { category: 'B', value: 150 },
    { category: 'C', value: 80 },
  ],
  encode: {
    x: 'category',
    y: 'value',
    color: 'category',
  },
  // Category10 is the default palette, no need to explicitly specify
});

chart.render();
```

## Common Variants

### Explicitly Specify the Palette

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scale: {
    color: {
      type: 'ordinal',
      range: 'category10',  // Explicitly specified
    },
  },
});
```

### Custom Color Range

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scale: {
    color: {
      type: 'ordinal',
      range: [
        '#5B8FF9',
        '#5AD8A6',
        '#5D7092',
        '#F6BD16',
        '#6F5EF9',
      ],
    },
  },
});
```

### Using Theme Configuration

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  theme: {
    defaultCategory10: 'category10',
  },
});
```

## Complete Color Reference

| Index | Color Value | Color Name |
|------|--------|--------|
| 0 | #5B8FF9 | Blue |
| 1 | #5AD8A6 | Green |
| 2 | #5D7092 | Grayish Blue |
| 3 | #F6BD16 | Yellow |
| 4 | #6F5EF9 | Purple |
| 5 | #6DC8EC | Cyan |
| 6 | #945FB9 | Dark Purple |
| 7 | #FF9845 | Orange |
| 8 | #1E9493 | Dark Cyan |
| 9 | #FF99C3 | Pink |

## Comparison with Category20

| Feature | Category10 | Category20 |
|------|------------|------------|
| Number of Colors | 10 | 20 |
| Color Style | Consistent Saturation | Alternating Saturation |
| Applicable Scenarios | ≤10 Categories | 10-20 Categories |
| Default Usage | Yes | No |

## Common Errors and Fixes

### Error 1: More Than 10 Categories

```javascript
// ⚠️ Note: More than 10 categories will reuse colors in a loop
// Category 11 will use the same color as Category 1

// ✅ Solution 1: Use Category20
scale: {
  color: { type: 'ordinal', range: 'category20' }
}

// ✅ Solution 2: Customize More Colors
scale: {
  color: {
    type: 'ordinal',
    range: [...customColors]
  }
}
```

### Error 2: Incorrect Color Value Format

```javascript
// ❌ Incorrect: Color value format is wrong
range: ['rgb(91, 143, 249)', ...]

// ✅ Correct: Use standard HEX format
range: ['#5B8FF9', ...]
```