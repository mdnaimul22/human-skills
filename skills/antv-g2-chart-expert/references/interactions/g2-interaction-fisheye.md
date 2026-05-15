---
id: "g2-interaction-fisheye"
title: "G2 Fisheye Interaction"
description: |
  The fisheye interaction allows the focal point of the fisheye effect to follow the mouse movement, achieving dynamic focus + context magnification.
  It requires the use of the fisheye coordinate system or can be enabled independently (automatically adds fisheye to coordinate.transform).
  Automatically reverts to the normal view when the mouse leaves the chart area.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "fisheye"
  - "鱼眼"
  - "焦点上下文"
  - "focus context"
  - "interaction"

related:
  - "g2-coord-fisheye"
  - "g2-mark-point-scatter"

use_cases:
  - "Dynamic local magnification of dense scatter plots"
  - "Interactive detail viewing of large data points"
  - "Exploration of dense areas in time series"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/fisheye"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = Array.from({ length: 300 }, (_, i) => ({
  x: Math.random() * 100,
  y: Math.random() * 100,
  group: i % 5,
}));

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'group', shape: 'point' },
  scale: { color: { type: 'ordinal' } },
  coordinate: { transform: [ { type: 'fisheye' } ] },  // Combined with fisheye coordinate system
  interaction: {
    fisheye: true,   // Focus follows mouse
  },
});

chart.render();
```

## Configure Fisheye Intensity

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'group' },
  coordinate: { transform: [ { type: 'fisheye' } ] },
  interaction: {
    fisheye: {
      wait: 30,       // Throttle wait time (milliseconds), default 30, smaller values are more sensitive
      leading: true,  // Throttle leading edge execution, default undefined
      trailing: false, // Throttle trailing edge execution, default false
    },
  },
});
```

## Fisheye Effect Only in X Direction (Exploring Dense Areas in Line Charts)

```javascript
chart.options({
  type: 'line',
  data: denseTimeData,
  encode: { x: 'date', y: 'value', color: 'type' },
  coordinate: {
    transform: [
      {
        type: 'fisheye',
        distortionX: 4,   // Magnification intensity in X direction
        distortionY: 0,   // No distortion in Y direction
      }
    ]
  },
  interaction: { fisheye: true },
});
```

## Common Errors and Fixes

### Error: Only `interaction.fisheye` is set without setting the coordinate system—fisheye effect does not take effect
```javascript
// ⚠️  interaction.fisheye will automatically add fisheye coordinate.transform
// but if coordinate has other settings, explicit configuration may be required
chart.options({
  coordinate: { type: 'cartesian' },  // ⚠️  Explicitly set Cartesian coordinates, fisheye will append transformation
  interaction: { fisheye: true },     // Will automatically insert fisheye in coordinate.transform
});

// ✅ Most concise approach: Directly specify fisheye coordinate system
chart.options({
  coordinate: { transform: [ { type: 'fisheye' } ] },
  interaction: { fisheye: true },
});
```