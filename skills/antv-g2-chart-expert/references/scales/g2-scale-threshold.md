---
id: "g2-scale-threshold"
title: "G2 Threshold Scale"
description: |
  The threshold scale divides continuous numerical values into several intervals based on specified thresholds, with each interval mapped to a discrete output (such as a color).
  Commonly used in heatmaps, choropleth maps, and other scenarios where data is categorized into levels using a few key thresholds.
  Unlike the quantize scale, the threshold scale supports custom, non-uniform division points.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "threshold"
  - "scale"
  - "categorization"
  - "choropleth"
  - "heatmap"

related:
  - "g2-scale-linear"
  - "g2-scale-ordinal"
  - "g2-mark-cell-heatmap"

use_cases:
  - "Choropleth map coloring"
  - "Heatmap data categorization (Low/Medium/High/Very High)"
  - "Custom interval color mapping"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/threshold"
---

## Minimum Viable Example (Heatmap Graded Coloring)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { week: 'Mon', hour: '08:00', count: 5 },
  { week: 'Mon', hour: '09:00', count: 45 },
  { week: 'Mon', hour: '12:00', count: 120 },
  { week: 'Tue', hour: '09:00', count: 85 },
  { week: 'Wed', hour: '12:00', count: 200 },
  // ...
];

const chart = new Chart({ container: 'container', width: 640, height: 300 });

chart.options({
  type: 'cell',
  data,
  encode: {
    x: 'hour',
    y: 'week',
    color: 'count',
  },
  scale: {
    color: {
      type: 'threshold',
      domain: [30, 80, 150],          // 3 thresholds, dividing into 4 intervals
      range: ['#ebedf0', '#c6e48b', '#7bc96f', '#196127'],  // corresponding 4 colors
    },
  },
  style: { lineWidth: 2, stroke: '#fff' },
});

chart.render();
```

## Configuration Options

```javascript
scale: {
  color: {
    type: 'threshold',
    domain: [30, 80, 150],    // N thresholds, generating N+1 intervals
    range: ['#low', '#mid-low', '#mid-high', '#high'],  // N+1 output values
  },
}
```

## Risk Level Coloring Example

```javascript
// Map continuous risk scores to 4 risk level colors
chart.options({
  scale: {
    color: {
      type: 'threshold',
      domain: [25, 50, 75],     // Low/Medium/High/Extreme boundaries
      range: [
        '#52c41a',  // 0~25: Low Risk (Green)
        '#faad14',  // 25~50: Medium Risk (Yellow)
        '#ff7a45',  // 50~75: High Risk (Orange)
        '#ff4d4f',  // 75+: Extreme Risk (Red)
      ],
    },
  },
});
```

## Common Errors and Fixes

### Error: Mismatch in the Number of Domain and Range
```javascript
// ❌ Error: 2 domain thresholds generate 3 intervals, but only 2 range colors are provided
chart.options({
  scale: {
    color: {
      type: 'threshold',
      domain: [50, 100],     // 2 thresholds → 3 intervals
      range: ['#green', '#red'],  // ❌ Only 2 colors, should be 3
    },
  },
});

// ✅ Correct: N domain thresholds → range requires N+1 colors
chart.options({
  scale: {
    color: {
      type: 'threshold',
      domain: [50, 100],
      range: ['#52c41a', '#faad14', '#ff4d4f'],  // ✅ 3 colors
    },
  },
});
```