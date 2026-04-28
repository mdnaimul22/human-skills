

---
id: "g2-animation-intro"
title: "G2 Animation System Overview (animate configuration)"
description: |
 The G2 v5 animation system is configured via the animate property, supporting three timing points: enter, update, and exit.
 Built-in animation types include fadeIn/Out, scaleInX/Y, growInX/Y, waveIn, zoomIn/Out, morphing, pathIn.
 Each animation can be configured with duration (length), delay (latency), easing (easing function).
library: "g2"
version: "5.x"
category: "animations"
tags:
- "animation"
- "animation"
- "animate"
- "enter animation"
- "fadeIn"
- "scaleInX"
- "waveIn"
related:
- "g2-animation-keyframe"
- "g2-core-chart-init"
use_cases:
- "Add enter animation when chart is first rendered to enhance visual experience"
- "Add transition animation when data updates"
- "Add fade out effect when exiting"
difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/animate"
---
## Quick Reference for Built-in Animation Types
| Animation Name | Effect | Suitable Scenario |
|--------|------|---------|
| `fadeIn` | From transparent to opaque | General enter |
| `fadeOut` | From opaque to transparent | General exit |
| `scaleInX` | Scale expand from X axis start | Bar chart enter |
| `scaleInY` | Scale expand from Y axis bottom | Bar chart enter (vertical) |
| `scaleOutX` | Shrink disappear towards X axis | Bar chart exit |
| `scaleOutY` | Shrink disappear towards Y axis | Bar chart exit |
| `growInX` | Grow from left to right | Bar chart, Line chart enter |
| `growInY` | Grow from bottom to top | Bar chart enter |
| `waveIn` | Wave scan enter | Polar chart (Rose chart, Pie chart) |
| `zoomIn` | Scale up from center | Point chart enter |
| `zoomOut` | Shrink disappear towards center | Point chart exit |
| `pathIn` | Path drawing step by step | Line chart, Path chart |
| `morphing` | Shape deformation transition | Chart type switch |
## Minimal Runnable Example
```javascript
import { Chart } from '@antv/g2';
const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480
});
chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports', sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action', sold: 120 },
    { genre: 'RPG', sold: 98 },
  ],
  encode: {
    x: 'genre',
    y: 'sold',
    color: 'genre'
  },
  animate: {
    enter: {
      type: 'growInY', // Enter animation: grow from bottom to top
      duration: 800, // Duration (milliseconds)
      delay: 0, // Delay
      easing: 'ease-out', // Easing function
    },
  },
});
chart.render();
```
## Three Timing Points for Configuring Animations
```javascript
chart.options({
  type: 'interval',
  data,
  encode: {
    x: 'x',
    y: 'y',
    color: 'type'
  },
  animate: {
    // Enter: When chart is first rendered
    enter: {
      type: 'scaleInY',
      duration: 1000,
      easing: 'ease-out-bounce',
    },
    // Update: When data changes
    update: {
      type: 'morphing',
      duration: 500,
    },
    // Exit: When elements are removed
    exit: {
      type: 'fadeOut',
      duration: 300,
    },
  },
});
```
## Disable Animations
```javascript
// Disable all animations
chart.options({
  animate: false,
});
// Disable only enter animation
chart.options({
  animate: {
    enter: false,
  },
});
```
## Recommended Common Animation Combinations
```javascript
// Bar chart: growInY enter
animate: {
  enter: {
    type: 'growInY',
    duration: 800
  }
}
// Line chart: pathIn enter (path drawing effect)
animate: {
  enter: {
    type: 'pathIn',
    duration: 1200
  }
}
// Pie chart (polar): waveIn enter
animate: {
  enter: {
    type: 'waveIn',
    duration: 1000
  }
}
// Scatter plot: zoomIn enter
animate: {
  enter: {
    type: 'zoomIn',
    duration: 600
  }
}
// General fade in
animate: {
  enter: {
    type: 'fadeIn',
    duration: 500
  }
}
```
## Common Errors and Corrections
### Error 1: animate.enter written as string
```javascript
// ❌ Error: enter is not a string, it is an object
chart.options({
  animate: {
    enter: 'fadeIn', // ❌
  },
});
// ✅ Correct
chart.options({
  animate: {
    enter: {
      type: 'fadeIn',
      duration: 600
    }, // ✅
  },
});
```
### Error 2: Using non-polar animations in polar charts
```javascript
// ❌ scaleInX/Y effect is incorrect in polar coordinates
chart.options({
  coordinate: {
    type: 'theta'
  },
  animate: {
    enter: {
      type: 'scaleInY'
    }, // ❌ Pie chart should use waveIn
  },
});
// ✅ Polar charts recommend waveIn
chart.options({
  coordinate: {
    type: 'theta'
  },
  animate: {
    enter: {
      type: 'waveIn',
      duration: 1000
    }, // ✅
  },
});
```