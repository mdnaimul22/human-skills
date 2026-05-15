---
id: "g2-coord-fisheye"
title: "G2 Fisheye Coordinate System"
description: |
  The fisheye coordinate system magnifies the area near the focus while compressing regions farther away,
  allowing for the simultaneous preservation of local details and a global overview in dense datasets.
  It is typically used in conjunction with fisheye interaction to achieve dynamic magnification effects that follow the mouse.

library: "g2"
version: "5.x"
category: "coordinates"
tags:
  - "fisheye"
  - "fish-eye"
  - "focus+context"
  - "coordinate"
  - "dense data"

related:
  - "g2-mark-point-scatter"
  - "g2-coord-transpose"

use_cases:
  - "Viewing local details in dense scatter plots"
  - "Exploring details in dense areas of time series"
  - "Scenarios requiring both global and local detail views"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/coordinate/fisheye"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data: Array.from({ length: 200 }, (_, i) => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    group: i % 5,
  })),
  encode: { x: 'x', y: 'y', color: 'group', shape: 'point' },
  scale: { color: { type: 'ordinal' } },
  coordinate: {
    transform: [
      {
        type: 'fisheye',
        focusX: 0.5,       // Focus X position (0~1 relative coordinates)
        focusY: 0.5,       // Focus Y position
        distortionX: 2,    // Magnification factor in X direction (larger values result in stronger magnification)
        distortionY: 2,    // Magnification factor in Y direction
      }
    ]
  },
  // Typically used with fisheye interaction to make the focus follow the mouse
  interaction: { fisheye: true },
});

chart.render();
```

## Configuration Options

```javascript
coordinate: {
  transform: [
    {
      type: 'fisheye',
      focusX: 0,        // Focus X (relative coordinate 0~1), default 0
      focusY: 0,        // Focus Y (relative coordinate 0~1), default 0
      distortionX: 2,   // Distortion strength in X direction, default 2
      distortionY: 2,   // Distortion strength in Y direction, default 2
      visual: false,    // Whether to enable visual effects, default false
    }
  ]
}
```

## Fisheye Effect Only in X Direction (Time Series)

```javascript
chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  coordinate: {
    transform: [
      {
        type: 'fisheye',
        distortionX: 3,   // Magnify only in X direction
        distortionY: 0,   // No distortion in Y direction
      }
    ]
  },
  interaction: { fisheye: true },
});
```

## Common Errors and Fixes

### Error: Using Fisheye Coordinate System Alone Without Interaction—Result is Static
```javascript
// ⚠️  Usable, but the focus is fixed and does not respond to mouse movements
chart.options({
  coordinate: {
    transform: [
      {
        type: 'fisheye',
        focusX: 0.3,
        focusY: 0.5,
      }
    ]
  },
  // No interaction.fisheye
});

// ✅ Recommended: Combine with interaction for dynamic fisheye effect
chart.options({
  coordinate: { transform: [ { type: 'fisheye' } ] },
  interaction: { fisheye: true },  // Focus follows the mouse
});
```