---
id: "g2-coord-helix"
title: "G2 Helix Coordinate System (helix)"
description: |
  The helix coordinate system arranges time/sequential data along a helix, suitable for displaying long time series with periodic patterns.
  Data is spirally wound, with data points at the same periodic positions aligned vertically, facilitating the discovery of periodic patterns.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "helix"
  - "spiral"
  - "spiral chart"
  - "periodic"
  - "time series"
  - "coordinate"

related:
  - "g2-mark-interval-basic"
  - "g2-scale-time"

use_cases:
  - "Displaying periodic patterns of multi-year daily average temperatures"
  - "Periodic analysis of long time series of stock prices"
  - "Visualization of weekly/monthly/yearly periodic patterns"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/helix"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Generate daily average temperature data for a year
const data = Array.from({ length: 365 }, (_, i) => ({
  day: i,
  temp: 15 + 12 * Math.sin((i / 365) * Math.PI * 2) + (Math.random() - 0.5) * 5,
}));

const chart = new Chart({ container: 'container', width: 600, height: 600 });

chart.options({
  type: 'interval',
  data,
  encode: {
    x: 'day',    // Order (arranged along the spiral)
    y: 'temp',   // Value (mapped to radius changes)
    color: 'temp',
  },
  scale: {
    color: { type: 'sequential', palette: 'rdYlBu' },
  },
  coordinate: {
    type: 'helix',
    startAngle: 0,              // Start angle, default 0
    endAngle: Math.PI * 6,      // End angle, default 6π (3 turns)
    innerRadius: 0.1,
    outerRadius: 0.9,
  },
  style: { lineWidth: 0 },
  legend: false,
});

chart.render();
```

## Configuration Options

```javascript
coordinate: {
  type: 'helix',
  startAngle: 0,              // Start angle (in radians), default 0
  endAngle: Math.PI * 6,      // End angle, default 6π (3 turns)
  innerRadius: 0,             // Inner radius, default 0
  outerRadius: 1,             // Outer radius ratio, default 1
}
```

## Common Errors and Fixes

### Error: Too Little Data, Too Many Helix Loops—Large Blank Areas
```javascript
// ❌ Only 12 months of data but set to 6π (3 loops), with only 4 points per loop
chart.options({
  data: monthlyData,  // Only 12 entries
  coordinate: { type: 'helix', endAngle: Math.PI * 6 },
});

// ✅ Adjust loops based on data volume: endAngle = number of loops × 2π
chart.options({
  coordinate: {
    type: 'helix',
    endAngle: Math.PI * 2,  // 1 loop, suitable for monthly data
  },
});
```

### Error: Improper Style Settings Causing Invisible or Abnormal Rendering of Graphics
```javascript
// ❌ Using lineWidth: 0 and interval type without setting sufficient width may cause visual "disappearance"
chart.options({
  type: 'interval',
  coordinate: { type: 'helix' },
  style: { lineWidth: 0 },
});

// ✅ Set an appropriate lineWidth or adjust the graphic type, such as point, which is more suitable for fine-grained data
chart.options({
  type: 'point', // More suitable for large amounts of dense data
  style: { lineWidth: 2 },
});
```

### Error: Animation Type Incompatible with Graphic Element Resulting in No Animation Effect
```javascript
// ❌ growInY animation may not be applicable to all interval elements in helix scenarios
chart.options({
  animate: {
    enter: {
      type: 'growInY',
    }
  }
});

// ✅ Use universal animation types like fadeIn to ensure compatibility
chart.options({
  animate: {
    enter: {
      type: 'fadeIn',
      duration: 2000,
    }
  }
});
```