---
id: "g2-mark-liquid"
title: "G2 Liquid Chart"
description: |
  The liquid mark displays a single percentage value using a wave-filled circle,
  commonly used to show completion rates, health metrics, KPI achievement rates, etc.
  The data is a decimal between 0 and 1 (percentage), with a built-in wave animation effect.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "liquid"
  - "liquid chart"
  - "progress"
  - "percentage"
  - "KPI"
  - "completion rate"

related:
  - "g2-mark-gauge"
  - "g2-core-chart-init"

use_cases:
  - "Displaying target completion rate / KPI achievement rate"
  - "Showing proportion metrics (e.g., memory usage)"
  - "Core metric visualization in dashboards"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/other/#liquid"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 300, height: 300 });

chart.options({
  type: 'liquid',
  data: 0.72,    // Percentage value between 0 and 1
  style: {
    outlineBorder: 4,       // Outline border width
    outlineDistance: 8,     // Distance between outline and inner circle
    waveLength: 128,        // Wave length
  },
});

chart.render();
```

## Custom Styles

```javascript
chart.options({
  type: 'liquid',
  data: 0.6,
  style: {
    outlineBorder: 4,
    outlineDistance: 8,
    waveLength: 128,
    // Wave color
    fill: '#5B8FF9',
    fillOpacity: 0.85,
    // Background circle color
    background: {
      fill: '#E8F0FE',
    },
    // Center text style
    text: {
      style: {
        fontSize: 28,
        fontWeight: 'bold',
        fill: '#fff',
        // Custom text content (default displays percentage)
        formatter: (v) => `${(v * 100).toFixed(1)}%`,
      },
    },
  },
  // Do not display axes and legend
  axis: false,
  legend: false,
  tooltip: false,
});
```

## Common Errors and Fixes

### Error 1: Value Exceeds 0~1 Range—Abnormal Wave Position
```javascript
// ❌ Error: Liquid value is 72 (should be 0.72)
chart.options({
  type: 'liquid',
  data: 72,   // ❌ Should be 0.72
});

// ✅ Correct: Decimal between 0~1
chart.options({
  data: 0.72,  // ✅
});
```

### Error 2: Axis is set—Axis is meaningless in liquid charts
```javascript
// ❌ Liquid charts display axes by default, which usually need to be turned off
chart.options({
  type: 'liquid',
  data: 0.7,
  // ❌ Axis/legend/tooltip not disabled
});

// ✅ Recommended to disable unnecessary components
chart.options({
  type: 'liquid',
  data: 0.7,
  axis: false,     // ✅ Disable axis
  legend: false,   // ✅ Disable legend
  tooltip: false,  // ✅ Disable tooltip
});
```