---
id: "g2-animation-types"
title: "Detailed Explanation of G2 Built-in Animation Types (fadeIn/scaleIn/growIn/pathIn/waveIn/zoomIn/morphing)"
description: |
  G2 v5 includes multiple built-in animation types, each suitable for different Marks and coordinate systems:
  fadeIn/Out (fade in/out), scaleInX/Y (scale in along X/Y axis), growInX/Y (grow in along X/Y axis),
  pathIn (path drawing), waveIn (polar wave in), zoomIn/Out (zoom in/out), morphing (shape transition).
  These animations can be configured using animate.enter.type and similar settings.

library: "g2"
version: "5.x"
category: "animations"
tags:
  - "fadeIn"
  - "scaleInX"
  - "scaleInY"
  - "growInX"
  - "growInY"
  - "pathIn"
  - "waveIn"
  - "zoomIn"
  - "zoomOut"
  - "morphing"
  - "animation types"

related:
  - "g2-animation-intro"
  - "g2-animation-keyframe"

use_cases:
  - "Selecting the most appropriate entrance animation based on chart type"
  - "Line chart path drawing animation"
  - "Pie/rose chart wave entrance"
  - "Shape transition during data updates"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/animate"
---

## Animation Types and Applicable Scenarios

| Animation Name | Direction | Best for Mark | Features |
|----------------|-----------|---------------|----------|
| `fadeIn` | - | All Marks | Fade in, universal, safest |
| `fadeOut` | - | All Marks | Fade out, universal exit |
| `scaleInX` | X-axis | interval (bar chart) | Expands from top-left to right |
| `scaleInY` | Y-axis | interval (bar chart) | Scales up from bottom to top |
| `scaleOutX` | X-axis | interval | Exit version of scaleInX |
| `scaleOutY` | Y-axis | interval | Exit version of scaleInY |
| `growInX` | X-axis | line, area, interval (Cartesian coordinates) | Clips and grows from left to right |
| `growInY` | Y-axis | interval, area (Cartesian coordinates) | Clips and grows from bottom to top; **Disabled for polar/helix coordinates** |
| `pathIn` | Path | line, path, link | Path lines drawn step by step |
| `waveIn` | Wave | interval (polar coordinates) | Polar-specific sector expansion |
| `zoomIn` | Center | point, text | Zooms in from the center |
| `zoomOut` | Center | point, text | Zooms out and disappears into the center |
| `morphing` | Morphing | All Marks | Smooth shape transition |

## fadeIn / fadeOut

```javascript
// The most universal animation, suitable for any mark
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  animate: {
    enter: { type: 'fadeIn', duration: 600 },
    exit: { type: 'fadeOut', duration: 300 },
  },
});
```

## scaleInY / growInY (Bar Chart Entry)

```javascript
// scaleInY: Scale expansion (with a scaling effect)
// growInY: Crop growth (with a "growing from the ground" feel, more natural)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  animate: {
    // Method 1: Scaling
    enter: { type: 'scaleInY', duration: 800, easing: 'ease-out' },
    // Method 2: Growth (recommended)
    // enter: { type: 'growInY', duration: 800 },
  },
});
```

## pathIn (Line Chart Path Drawing)

```javascript
// pathIn: Line/path gradually drawn from left to right
chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  animate: {
    enter: {
      type: 'pathIn',      // Path drawn gradually
      duration: 1500,
      easing: 'linear',    // Linear easing for better effect
    },
  },
});
```

## waveIn (Exclusive to Polar/Pie Charts)

```javascript
// waveIn: Wave sweep from the outer circle to the inner, specifically designed for polar coordinates
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
  animate: {
    enter: {
      type: 'waveIn',       // Exclusive to polar coordinates
      duration: 1000,
    },
  },
});
```

## zoomIn / zoomOut (Point Chart Zoom)

```javascript
// zoomIn: Scatter points zoom in from the center
chart.options({
  type: 'point',
  data: scatterData,
  encode: { x: 'x', y: 'y', size: 'value' },
  animate: {
    enter: { type: 'zoomIn', duration: 500 },
    exit: { type: 'zoomOut', duration: 300 },
  },
});
```

## Morphing (Shape Transformation Animation)

```javascript
// morphing: Smooth shape transformation during data updates
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  animate: {
    update: {
      type: 'morphing',    // Shape transformation transition during data updates
      duration: 600,
    },
  },
});

// Morphing can also be automatically triggered in timingKeyframe
chart.options({
  type: 'timingKeyframe',
  children: [
    { type: 'interval', data, encode: { x: 'x', y: 'y' } },
    { type: 'line',     data, encode: { x: 'x', y: 'y' } },
  ],
});
```

## Recommended Animations by Chart Type

```javascript
// Bar Chart (Recommended: growInY)
{ type: 'interval', animate: { enter: { type: 'growInY', duration: 800 } } }

// Column Chart (Recommended: growInX)
{ type: 'interval', coordinate: { transform: [{ type: 'transpose' }] },
  animate: { enter: { type: 'growInX', duration: 800 } } }

// Line Chart (Recommended: pathIn)
{ type: 'line', animate: { enter: { type: 'pathIn', duration: 1200 } } }

// Scatter Plot (Recommended: zoomIn or fadeIn)
{ type: 'point', animate: { enter: { type: 'zoomIn', duration: 400 } } }

// Pie/Donut Chart (Recommended: waveIn)
{ type: 'interval', coordinate: { type: 'theta' },
  animate: { enter: { type: 'waveIn', duration: 1000 } } }

// Area Chart (Recommended: fadeIn or growInX)
{ type: 'area', animate: { enter: { type: 'fadeIn', duration: 800 } } }

// Helix Coordinate System (Must use fadeIn, growInX/Y is prohibited)
{ type: 'interval', coordinate: { type: 'helix', ... },
  animate: { enter: { type: 'fadeIn', duration: 800 } } }
```

## Common Errors and Fixes

### Error 1: Using scaleInY on a Transposed Bar Chart
```javascript
// ❌ Bar charts are horizontal, so using scaleInY (vertical scaling) is incorrect
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  animate: { enter: { type: 'scaleInY' } },  // ❌ Should use growInX or scaleInX
});

// ✅ Use X-direction animation for bar charts
chart.options({
  animate: { enter: { type: 'growInX', duration: 800 } },  // ✅
});
```

### Error 2: Using growInX/growInY in the helix coordinate system

The implementation of `growInX` / `growInY` involves **clipPath clipping** along the Cartesian coordinate axes. In the `helix` coordinate system, the axes are remapped to a spiral path, and there is no "bottom" or "left" baseline on the screen. The clipping rectangle crosses the spiral, causing parts of the spiral area to be cut off or rendered incompletely. After the animation ends, the chart may also appear incomplete.

**The same issue applies to all non-Cartesian coordinate systems** (`polar`, `theta`, `helix`)—these systems should use `waveIn` (polar-specific) or `fadeIn` (general-purpose) instead of `growInX/Y`.

```javascript
// ❌ Incorrect: Using growInY in helix coordinate system → Clipping rectangle crosses the spiral, causing incomplete rendering
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'growInY', duration: 2000 },  // ❌ Spiral is clipped, some areas are missing
  },
});

// ✅ Correct: Using fadeIn in helix coordinate system
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'fadeIn', duration: 1000 },   // ✅ Fades in without clipping side effects
  },
});

// ✅ Using waveIn in polar coordinates (theta/polar)
chart.options({
  type: 'interval',
  coordinate: { type: 'theta' },
  animate: {
    enter: { type: 'waveIn', duration: 1000 },   // ✅ Polar-specific sector expansion
  },
});
```

**Root Cause**: `growInX/Y` assumes the existence of a fixed Cartesian baseline (X=0 or Y=0) as the clipping starting point, which holds true in the Cartesian coordinate system. However, in `helix` / `polar` systems, where coordinates are remapped to polar or spiral paths, this baseline no longer corresponds to a visible boundary, resulting in arbitrary truncation of the spiral shape.