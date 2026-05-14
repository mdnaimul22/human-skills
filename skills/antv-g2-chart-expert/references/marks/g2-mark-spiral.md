---
id: "g2-mark-spiral"
title: "G2 Spiral Plot"
description: |
  The spiral plot uses the helix coordinate system (coordinate.type: 'helix') to render time series data in a spiral shape,
  extending outward from the center. It is suitable for displaying the periodic patterns and trends of large amounts of time series data (typically 100+ data points).

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "spiral plot"
  - "spiral"
  - "helix"
  - "time series"
  - "periodicity"
  - "large datasets"

related:
  - "g2-mark-line-basic"
  - "g2-mark-interval-basic"

use_cases:
  - "Trend visualization for large time series datasets (100+ data points)"
  - "Identification of periodic patterns in data (e.g., annual seasonality)"
  - "Gene expression time series"

anti_patterns:
  - "Not suitable for small datasets (< 30 points), use line charts instead"
  - "Not suitable for precise value comparison, as the non-linear spiral coordinates make exact value reading difficult"
  - "animate.enter cannot use growInX/growInY, as it will cause incomplete spiral rendering; must use fadeIn"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/spiral"
---

## Core Concepts

**Helix Chart = interval/line mark + `coordinate: { type: 'helix', startAngle, endAngle }`**

- `coordinate.type: 'helix'`：Archimedean spiral coordinate system
- `startAngle`：Spiral start angle (in radians), `Math.PI / 2` ≈ starts from the top
- `endAngle`：Spiral end angle, larger values result in more spiral loops
- **Data Volume Requirement**：Typically requires 100 or more data points to form a complete spiral

**Relationship Between Angle and Loops**：`loops = (endAngle - startAngle) / (2 * Math.PI)`

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
  height: 500,
});

chart.options({
  type: 'interval',
  data: {
    value: [
      { time: '2025.07.11', value: 35 },
      { time: '2025.07.12', value: 30 },
      { time: '2025.07.13', value: 55 },
      // ... more data (100+ entries)
    ],
  },
  encode: { x: 'time', y: 'value', color: 'value' },
  scale: {
    color: { type: 'linear', range: ['#ffffff', '#1890FF'] },
  },
  coordinate: {
    type: 'helix',
    startAngle: Math.PI / 2,              // Start from the top
    endAngle: Math.PI / 2 + 6 * Math.PI, // Rotate 3 times (2π per rotation)
  },
  animate: { enter: { type: 'fadeIn' } },
  tooltip: { title: 'time' },
});

chart.render();
```

## Common Angle Configurations

```javascript
// Standard Helix (approximately 6 turns, suitable for weekly data over a year)
coordinate: {
  type: 'helix',
  startAngle: 1.5707963267948966,   // Math.PI / 2
  endAngle: 39.269908169872416,     // Math.PI / 2 + 12 * Math.PI (6 turns)
}

// Fewer Turns (approximately 3 turns, suitable for quarterly data)
coordinate: {
  type: 'helix',
  startAngle: Math.PI / 2,
  endAngle: Math.PI / 2 + 6 * Math.PI,
}

// With Inner Radius (Annular Helix)
coordinate: {
  type: 'helix',
  startAngle: 0.2 * Math.PI,
  endAngle: 6.5 * Math.PI,
  innerRadius: 0.1,
}
```

## Grouped Spiral Chart by Category

```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'fetch',
    value: 'url-to-data.json',
  },
  encode: {
    x: 'time',
    y: 'group',     // Use Y-axis to categorize groups
    color: 'value', // Use color to map values
  },
  scale: {
    color: {
      type: 'linear',
      range: ['#fff', '#ec4839'],
    },
  },
  coordinate: {
    type: 'helix',
    startAngle: 0.2 * Math.PI,
    endAngle: 6.5 * Math.PI,
    innerRadius: 0.1,
  },
  tooltip: {
    title: 'time',
    items: [
      { field: 'group', name: 'Group' },
      { field: 'value', name: 'Value' },
    ],
  },
});
```

## Common Errors and Fixes

### Error 1: Insufficient Data Volume

```javascript
// ❌ Issue: 5 data points cannot form a helix, resulting in poor visualization
chart.options({
  type: 'interval',
  data: {
    value: [
      { time: '2025-01', value: 35 },
      { time: '2025-02', value: 50 },
      { time: '2025-03', value: 45 },
      { time: '2025-04', value: 60 },
      { time: '2025-05', value: 40 },
    ],
  },
  coordinate: { type: 'helix', startAngle: Math.PI / 2, endAngle: 40 },
});

// ✅ Use a line chart instead for handling small datasets
chart.options({
  type: 'line',
  data,
  encode: { x: 'time', y: 'value' },
});
```

### Error 2: Incorrect coordinate type name

```javascript
// ❌ Error: No 'spiral' type exists, should be 'helix'
coordinate: { type: 'spiral' }   // ❌ Does not exist

// ✅ Correct: Use helix
coordinate: { type: 'helix', startAngle: Math.PI / 2, endAngle: 40 }  // ✅
```

### Error 3: Confusion Between Angle Units

```javascript
// ❌ Incorrect: Using degrees instead of radians
coordinate: {
  type: 'helix',
  startAngle: 90,   // ❌ 90° is not in radians, should be Math.PI / 2
  endAngle: 2250,   // ❌ Should be in radians
}

// ✅ Correct: Using radians
coordinate: {
  type: 'helix',
  startAngle: Math.PI / 2,           // ✅ 90° = π/2 radians
  endAngle: Math.PI / 2 + 12 * Math.PI,  // ✅ 6 turns
}
```

### Error 4: Incorrect data format (inline data requires value wrapping)

```javascript
// ❌ Incorrect: Inline array data must be placed in data.value
chart.options({
  data: [{ time: '2025.01', value: 35 }, ...],  // ❌ Direct array
  coordinate: { type: 'helix', ... },
});

// ✅ Correct: Inline data wrapped with { value: [...] }
chart.options({
  data: {
    value: [{ time: '2025.01', value: 35 }, ...],  // ✅
  },
  coordinate: { type: 'helix', ... },
});
```

### Error 5: Using growInY/growInX with animate.enter Causes Incomplete Spiral Rendering

`growInX/Y` implements animations by clipping along the axes of a Cartesian coordinate system (clipPath). In the helix coordinate system, coordinates are remapped to a spiral path, and there is no "bottom baseline." The clipping rectangle crosses the spiral, causing parts of the spiral area to be cut off, resulting in an incomplete chart display after the animation ends.

```javascript
// ❌ Error: growInY clips the rectangle across the spiral in helix coordinates → Incomplete chart rendering
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'growInY', duration: 2000 },  // ❌ Spiral is truncated
  },
});

// ✅ Correct: Helix coordinates must use fadeIn (or no animation)
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'fadeIn', duration: 1000 },  // ✅
  },
});
```

## Selection Compared to Line Charts

| Scenario | Recommended Chart |
|------|---------|
| Data volume < 50 entries | Line Chart |
| Data volume 100+ entries, observing trends | Spiral Chart or Line Chart |
| Need to discover periodic patterns | **Spiral Chart** (best when each cycle aligns) |
| Need to precisely read values | Line Chart |
| Visual effect for large screen display | **Spiral Chart** |