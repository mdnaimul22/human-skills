---
id: "g2-palette-category20"
title: "G2 Category20 Palette"
description: |
  AntV's classic 20-color palette, used for color mapping of categorical data.
  It includes 20 colors with an alternating saturation design, suitable for visualization scenarios with more categories.

library: "g2"
version: "5.x"
category: "palette"
tags:
  - "palette"
  - "color"
  - "categorical"
  - "20-color"

related:
  - "g2-palette-category10"
  - "g2-scale-ordinal"
  - "g2-theme-builtin"

use_cases:
  - "Color mapping for more than 10 categories"
  - "Scenarios requiring more color distinctions"
  - "Complex categorical data visualization"

anti_patterns:
  - "For fewer categories, it is recommended to use Category10"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/palette"
---

## Core Concepts

Category20 is an extended categorical color palette from AntV:
- Contains 20 colors
- Uses an alternating saturation design pattern
- Suitable for scenarios with 10-20 categories

**Design Features:**
- First half consists of saturated colors (consistent with Category10)
- Second half consists of low-saturation colors
- Alternating usage enhances distinguishability

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
    // ... more categories
  ],
  encode: {
    x: 'category',
    y: 'value',
    color: 'category',
  },
  scale: {
    color: {
      type: 'ordinal',
      range: 'category20',
    },
  },
});

chart.render();
```

## Common Variants

### Explicitly Specify Color Range

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scale: {
    color: {
      type: 'ordinal',
      range: [
        '#5B8FF9', '#CDDDFD',
        '#5AD8A6', '#CDF3E4',
        '#5D7092', '#CED4DE',
        '#F6BD16', '#FCEBB9',
        '#6F5EF9', '#D3CEFD',
        '#6DC8EC', '#D3EEF9',
        '#945FB9', '#DECFEA',
        '#FF9845', '#FFE0C7',
        '#1E9493', '#BBDEDE',
        '#FF99C3', '#FFE0ED',
      ],
    },
  },
});
```

### Combine with Custom Colors

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scale: {
    color: {
      type: 'ordinal',
      range: [
        ...customColors.slice(0, 10),
        '#5B8FF9', '#CDDDFD', // Supplement Category20 colors
        // ...
      ],
    },
  },
});
```

## Complete Color Reference

| Index | Color Value | Saturation |
|-------|-------------|------------|
| 0     | #5B8FF9     | High       |
| 1     | #CDDDFD     | Low        |
| 2     | #5AD8A6     | High       |
| 3     | #CDF3E4     | Low        |
| 4     | #5D7092     | High       |
| 5     | #CED4DE     | Low        |
| 6     | #F6BD16     | High       |
| 7     | #FCEBB9     | Low        |
| 8     | #6F5EF9     | High       |
| 9     | #D3CEFD     | Low        |
| 10    | #6DC8EC     | High       |
| 11    | #D3EEF9     | Low        |
| 12    | #945FB9     | High       |
| 13    | #DECFEA     | Low        |
| 14    | #FF9845     | High       |
| 15    | #FFE0C7     | Low        |
| 16    | #1E9493     | High       |
| 17    | #BBDEDE     | Low        |
| 18    | #FF99C3     | High       |
| 19    | #FFE0ED     | Low        |

## Comparison with Category10

| Feature | Category10 | Category20 |
|------|------------|------------|
| Number of Colors | 10 | 20 |
| Color Style | Consistent Saturation | Alternating Saturation |
| Applicable Scenarios | ≤10 Categories | 10-20 Categories |
| Default Usage | Yes | No |
| Distinguishing Difficulty | Easier | Requires Attention to Adjacent Colors |

## Design Recommendations

### Category Quantity Recommendations

| Category Quantity | Recommended Palette |
|---------|-----------|
| 1-5 | Category10 |
| 6-10 | Category10 |
| 11-15 | Category20 |
| 16-20 | Category20 |
| >20 | Custom or Grouped |

### Usage Tips

```javascript
// Tip: Use alternating saturation to increase distinguishability
// Place important categories in high saturation positions (even indices)

// Example: Highlight important categories
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scale: {
    color: {
      type: 'ordinal',
      range: [
        '#5B8FF9',  // High saturation - Category A
        '#CDDDFD',  // Low saturation - Category B
        '#5AD8A6',  // High saturation - Category C (important)
        // ...
      ],
    },
  },
});
```

## Common Errors and Fixes

### Error 1: More than 20 Categories

```javascript
// ⚠️ Note: More than 20 categories will reuse colors in a loop

// ✅ Solution 1: Customize more colors
scale: {
  color: {
    type: 'ordinal',
    range: [...30colors]
  }
}

// ✅ Solution 2: Merge small categories
// Merge small categories into an "Other" category
```

### Error 2: Insufficient Distinction Between Adjacent Colors

```javascript
// ⚠️ Note: Adjacent low-saturation colors may be difficult to distinguish

// ✅ Solution: Adjust the domain order
scale: {
  color: {
    type: 'ordinal',
    domain: ['A', 'C', 'E', 'B', 'D'],  // Alternate high/low saturation
    range: 'category20'
  }
}
```