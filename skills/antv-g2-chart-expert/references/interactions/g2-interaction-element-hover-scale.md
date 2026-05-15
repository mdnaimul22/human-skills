---
id: "g2-interaction-element-hover-scale"
title: "G2 Element Hover Scale Interaction (elementHoverScale)"
description: |
  elementHoverScale scales up elements when the mouse hovers over them, providing a three-dimensional effect and visual feedback.
  It is suitable for enhancing interactions in charts with discrete elements like pie charts and scatter plots, offering a more visually striking effect than regular highlighting.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "elementHoverScale"
  - "hover scale"
  - "hover"
  - "scale"
  - "interaction"

related:
  - "g2-interaction-element-highlight"
  - "g2-mark-arc-pie"

use_cases:
  - "Pie/Donut chart sector pop-out on hover"
  - "Scatter plot data point enlargement on hover"
  - "Dashboard card scale-up effect on hover"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/element-hover-scale"
---

## Minimum Viable Example (Pie Chart Hover Zoom)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 480, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { type: 'Electronics', value: 40 },
    { type: 'Clothing', value: 25 },
    { type: 'Food', value: 20 },
    { type: 'Others', value: 15 },
  ],
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.85 },
  interaction: {
    elementHoverScale: true,   // Sector pops out when hovered
  },
});

chart.render();
```

## Configure Zoom Scale

```javascript
chart.options({
  interaction: {
    elementHoverScale: {
      scale: 1.1,    // Zoom factor, default is approximately 1.1 (10% enlargement),
    },
  },
});
```

## Combination with Other Interactions

```javascript
// Pie Chart: Hover to Zoom + Tooltip
chart.options({
  type: 'interval',
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta' },
  interaction: {
    elementHoverScale: true,   // Zoom
    tooltip: true,             // Display tooltip simultaneously
  },
});
```

## Common Errors and Fixes

### Error: Using elementHighlight Simultaneously—Visual Effect Conflict
```javascript
// ❌ Both enabled, hovered element both scales and changes opacity, resulting in a chaotic effect
chart.options({
  interaction: {
    elementHoverScale: true,
    elementHighlight: true,   // ❌ Conflicts with hoverScale
  },
});

// ✅ Choose only one hover interaction
chart.options({
  interaction: {
    elementHoverScale: true,  // ✅ Scaling effect
    // or
    // elementHighlight: true,  // ✅ Fading effect
  },
});
```