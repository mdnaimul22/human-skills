---
id: "g2-comp-timing-keyframe"
title: "G2 timingKeyframe Keyframe Animation Composition"
description: |
  timingKeyframe is a composition type in G2 v5 that plays multiple chart views in sequence to form keyframe animations.
  Each sub-view is rendered in turn, with automatic interpolation transitions between adjacent frames, achieving a data storytelling effect.
  Refer to g2-animation-keyframe for detailed configuration and examples.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "timingKeyframe"
  - "keyframe animation"
  - "data storytelling"
  - "morphing"
  - "composition"
  - "animation composition"

related:
  - "g2-animation-keyframe"
  - "g2-animation-intro"
  - "g2-core-view-composition"

use_cases:
  - "Morphing animations between chart types (bar chart → line chart)"
  - "Animated display of data evolution over time"
  - "Visual data storytelling"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "ant

## Core Concepts

`timingKeyframe` is a composition type, where each child is a "keyframe" view.
The system automatically interpolates data and graphics between adjacent keyframes to create transition animations.

For detailed configuration and examples, please refer to [g2-animation-keyframe](./g2-animation-keyframe.md).

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', value: 83 },
  { month: 'Feb', value: 60 },
  { month: 'Mar', value: 95 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'timingKeyframe',
  duration: 1000,
  iterationCount: 'infinite',
  direction: 'alternate',
  children: [
    {
      type: 'interval',
      data,
      encode: { x: 'month', y: 'value', color: 'month' },
    },
    {
      type: 'line',
      data,
      encode: { x: 'month', y: 'value' },
    },
  ],
});

chart.render();
```

## Configuration Quick Reference

```javascript
chart.options({
  type: 'timingKeyframe',
  duration: 1000,                  // Transition duration between keyframes (milliseconds)
  iterationCount: 1,               // Number of iterations ('infinite' = infinite)
  direction: 'normal',             // 'normal' | 'reverse' | 'alternate' | 'reverse-alternate'
  easing: 'ease-in-out-sine',      // Easing function
  children: [/* Keyframe views */],
});
```