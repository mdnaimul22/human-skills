---
id: "g2-mark-gauge"
title: "G2 Gauge"
description: |
  G2 v5 has a built-in gauge Mark, which can be created using `type: 'gauge'`.
  The data includes `target` (current value) and `total` (maximum value),
  and supports segmented coloring (thresholds), center text, and custom styles.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "gauge"
  - "dial"
  - "KPI"
  - "progress"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-mark-arc-pie"

use_cases:
  - "Display KPI completion rate/achievement"
  - "Real-time monitoring of metrics (e.g., CPU usage)"
  - "Progress display (scores, ratings)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/gauge"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 400,
  height: 300,
});

chart.options({
  type: 'gauge',
  data: {
    value: {
      target: 120,   // Current value
      total: 400,    // Full score/Maximum value
      name: 'Score', // Center label
    },
  },
  legend: false,
});

chart.render();
```

## Segmented Color Gauge (Threshold Coloring)

```javascript
chart.options({
  type: 'gauge',
  data: {
    value: {
      target: 159,
      total: 280,
      name: 'Speed',
      // thresholds: Segmented by percentage (0-1), each segment with a different color
      thresholds: [100, 200, 280],   // Corresponding value segments
    },
  },
  scale: {
    color: {
      // Colors corresponding to each segment
      range: ['#F4664A', '#FAAD14', '#30BF78'],
    },
  },
  style: {
    // Center text
    textContent: (target, total) =>
      `Progress\n${((target / total) * 100).toFixed(0)}%`,
  },
  legend: false,
});
```

## Complete Configuration Description

```javascript
chart.options({
  type: 'gauge',
  data: {
    value: {
      target: 75,       // Current value (required)
      total: 100,       // Maximum value (required)
      name: 'score',    // Label name (optional)
      thresholds: [40, 70, 100],  // Segment thresholds (optional)
    },
  },

  // Color scale (used with thresholds)
  scale: {
    color: {
      range: ['#F4664A', '#FAAD14', '#30BF78'],
    },
  },

  // Gauge style
  style: {
    // Arc endpoint shape: 'round' (rounded end) | 'butt' (square end)
    arcShape: 'round',
    arcLineWidth: 1,
    arcStroke: '#fff',

    // Center text: signature fixed as (target, total), no third datum parameter
    textContent: (target, total) => `${target}/${total}`,
    textX: '50%',
    textY: '70%',
    textFontSize: 24,
    textFill: '#262626',

    // Pointer (false to hide)
    pointerShape: false,
    pinShape: false,
  },

  legend: false,
});
```

## Custom Start and End Angles

```javascript
chart.options({
  type: 'gauge',
  data: { value: { target: 60, total: 100, name: 'Completion Rate' } },
  // gauge internally uses radial coordinates, which can be adjusted via coordinate
  coordinate: {
    type: 'radial',
    innerRadius: 0.8,
    startAngle: (-10 / 12) * Math.PI,   // approximately -150°
    endAngle: (2 / 12) * Math.PI,        // approximately 30°
  },
  legend: false,
});
```

## Multi-Metric Gauge Dashboard Combination

```javascript
// Use facetRect or spaceFlex to arrange multiple gauges side by side
chart.options({
  type: 'spaceFlex',
  children: [
    {
      type: 'gauge',
      data: { value: { target: 75, total: 100, name: 'CPU' } },
      legend: false,
    },
    {
      type: 'gauge',
      data: { value: { target: 60, total: 100, name: 'Memory' } },
      legend: false,
    },
    {
      type: 'gauge',
      data: { value: { target: 45, total: 100, name: 'Disk' } },
      legend: false,
    },
  ],
});
```

## Common Errors and Fixes

### Error 0: Incorrect `textContent` Function Signature — Passing an Unnecessary Third `datum` Parameter

The signature for `textContent` is `(target, total) => string`. Internally, G2 **only passes two values**, and there is no third parameter.

```javascript
// ❌ Error: `datum` is undefined, accessing `datum.unit` will throw a TypeError
style: {
  textContent: (target, total, datum) => `${target}${datum.unit}\n${datum.name}`,
  //                            ^^^^^ Always undefined!
}

// ✅ Correct: Use closure to capture additional fields from `data`
const gaugeData = {
  target: 48,
  total: 60,
  name: 'Response Time',
  unit: 'min',
  thresholds: [15, 30, 45, 60],
};

chart.options({
  type: 'gauge',
  data: { value: gaugeData },
  style: {
    // Reference external variables via closure
    textContent: (target, total) => `${target}${gaugeData.unit}\n${gaugeData.name}`,
  },
});
```

### Error 1: Incorrect Data Format

```javascript
// ❌ Incorrect: Gauge data must be nested within a value object
chart.options({
  type: 'gauge',
  data: { target: 75, total: 100 },   // ❌ Top-level object
});

// ✅ Correct: Requires { value: { target, total } } structure
chart.options({
  type: 'gauge',
  data: {
    value: { target: 75, total: 100 },   // ✅
  },
});
```

### Error 2: Mismatch Between Thresholds and Color Range Count

```javascript
// ❌ Error: 3 thresholds correspond to 3 segments, but only 2 colors are provided
chart.options({
  type: 'gauge',
  data: { value: { target: 60, total: 100, thresholds: [40, 70, 100] } },
  scale: {
    color: { range: ['#F4664A', '#30BF78'] },   // ❌ Should have 3 colors
  },
});

// ✅ Correct: Number of colors = Number of threshold segments (thresholds.length segments)
chart.options({
  scale: {
    color: { range: ['#F4664A', '#FAAD14', '#30BF78'] },   // ✅ 3 segments, 3 colors
  },
});
```