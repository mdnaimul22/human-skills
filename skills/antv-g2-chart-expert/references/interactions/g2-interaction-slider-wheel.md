---
id: "g2-interaction-slider-wheel"
title: "G2 SliderWheel Wheel Zoom Interaction"
description: |
  sliderWheel is an interaction in G2 v5 that allows zooming the slider component of a chart using the mouse wheel (or two-finger scrolling on a trackpad).
  Scrolling the mouse wheel up narrows the time window (zoom in), while scrolling down widens it (zoom out).
  The zoom is centered around the mouse position. It must be used in conjunction with the slider component and the sliderFilter interaction.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "sliderWheel"
  - "wheel zoom"
  - "wheel"
  - "zoom"
  - "interaction"
  - "slider"

related:
  - "g2-interaction-slider-filter"
  - "g2-comp-slider"
  - "g2-mark-line-basic"

use_cases:
  - "Quickly zoom time range in time series charts using the wheel"
  - "Replace manual slider dragging with quick zoom operation"
  - "Pinch-to-zoom chart timeline on a trackpad"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/slider-wheel"
---

## Core Concepts

`sliderWheel` listens to the `wheel` event of the chart container, converting the wheel delta into a scaling change within the slider's value range.
- Wheel up (delta < 0): Shrink the window (zoom in on data)
- Wheel down (delta > 0): Expand the window (zoom out on data)
- Scaling is centered around the mouse position, keeping the data point under the mouse stationary

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: { values: [0, 0.3] },   // Initially display the first 30%
  },
  interaction: {
    sliderFilter: true,    // Must enable sliderFilter first
    sliderWheel: true,     // Then enable sliderWheel
  },
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  interaction: {
    sliderWheel: {
      x: true,               // X-axis slider responds to mouse wheel, default is true
      y: true,               // Y-axis slider responds to mouse wheel, default is true
      // x: 'shift',         // Responds only when Shift key is held down
      // y: 'ctrl',          // Responds only when Ctrl key is held down
      wheelSensitivity: 0.05,  // Mouse wheel sensitivity, default is 0.05
      minRange: 0.01,          // Minimum zoom range (prevents excessive magnification), default is 0.01
    },
  },
});
```

## Modifier Key Control (Avoid Conflicts with Page Scrolling)

```javascript
// Zoom the chart only when Ctrl is held down (avoid conflicts with page scrolling)
chart.options({
  interaction: {
    sliderWheel: {
      x: 'ctrl',    // Only Ctrl + wheel triggers X-axis zoom
      y: false,     // Y-axis does not respond to wheel
    },
  },
});
```

## Common Errors and Fixes

### Error: Forgot to Enable `sliderFilter` Simultaneously
```javascript
// ❌ Only `sliderWheel` without `sliderFilter`, wheel scrolling has no effect
chart.options({
  slider: { x: true },
  interaction: {
    sliderWheel: true,   // ❌ Missing `sliderFilter`
  },
});

// ✅ Must be used in conjunction with `sliderFilter`
chart.options({
  slider: { x: true },
  interaction: {
    sliderFilter: true,   // ✅ Enable filtering first
    sliderWheel: true,    // ✅ Then enable wheel zoom
  },
});
```

### Error: No slider component but sliderWheel is enabled
```javascript
// ❌ sliderWheel does not work without a slider component
chart.options({
  // No slider configuration
  interaction: { sliderWheel: true },  // Invalid
});

// ✅ A slider component is required
chart.options({
  slider: { x: { values: [0, 0.5] } },
  interaction: {
    sliderFilter: true,
    sliderWheel: true,
  },
});
```