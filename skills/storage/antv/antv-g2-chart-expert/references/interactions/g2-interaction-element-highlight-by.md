---
id: "g2-interaction-element-highlight-by"
title: "G2 Element Highlight by Color/X-axis (elementHighlightByColor / elementHighlightByX)"
description: |
  elementHighlightByColor: Highlights all elements with the same color channel value as the hovered element.
  elementHighlightByX: Highlights all elements with the same x-axis value as the hovered element.
  Both are variants of elementHighlight, differing in the grouping basis for highlighting,
  commonly used for linked highlighting of the same category or time point in multi-series charts.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "elementHighlightByColor"
  - "elementHighlightByX"
  - "linked highlighting"
  - "grouped highlighting"
  - "interaction"

related:
  - "g2-interaction-element-highlight"
  - "g2-interaction-element-select"

use_cases:
  - "Hover over a bar in a multi-series chart to highlight all bars of the same color (same category)"
  - "Hover over a time point to highlight all series at the same time point"
  - "Linked highlighting by row/column in a heatmap"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/element-highlight"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', city: 'Beijing', value: 83 },
  { month: 'Feb', city: 'Beijing', value: 60 },
  { month: 'Jan', city: 'Shanghai', value: 71 },
  { month: 'Feb', city: 'Shanghai', value: 55 },
  { month: 'Jan', city: 'Guangzhou', value: 95 },
  { month: 'Feb', city: 'Guangzhou', value: 88 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

// ── Linked Highlight by Color (City) ──
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'city' },
  transform: [{ type: 'dodgeX' }],
  interaction: {
    elementHighlightByColor: true,   // Hover over a bar → Highlight all bars of the same city
  },
});

chart.render();
```

## elementHighlightByX (Highlight elements with the same X-axis value)

```javascript
// Hover over any bar in a month → Highlight all bars in the same month across all cities
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'city' },
  transform: [{ type: 'dodgeX' }],
  interaction: {
    elementHighlightByX: true,   // Highlight all elements with the same x value
  },
});
```

## Comparison of Three Highlight Modes

```javascript
// 1. elementHighlight (default): Highlights only the single element the mouse hovers over
interaction: { elementHighlight: true }

// 2. elementHighlightByColor: Highlights all elements in the same color group (same category)
interaction: { elementHighlightByColor: true }

// 3. elementHighlightByX: Highlights all elements with the same x value (same time point/category)
interaction: { elementHighlightByX: true }
```

## Custom Highlight Style

```javascript
chart.options({
  interaction: {
    elementHighlightByColor: {
      background: true,         // Show background when highlighted (false to only change opacity)
      link: false,              // Whether to show connecting lines (only effective for line charts, etc.)
      offset: 0,                // Offset when highlighted
    },
  },
});
```

## Common Errors and Fixes

### Error: Using elementHighlightByColor on a chart without a color channel—all elements are highlighted
```javascript
// ❌ Without a color channel, all elements are treated as the same color group and highlighted on hover
chart.options({
  type: 'interval',
  encode: { x: 'month', y: 'value' },  // ❌ No color
  interaction: { elementHighlightByColor: true },
});

// ✅ A color channel is required for grouping and highlighting by color
chart.options({
  encode: { x: 'month', y: 'value', color: 'city' },  // ✅ With color grouping
  interaction: { elementHighlightByColor: true },
});
```