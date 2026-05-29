---
id: "g2-transform-stack-enter"
title: "G2 StackEnter Stacked Transform for Entry Animation"
description: |
  stackEnter is a Transform in G2 v5 used for grouped entry animations,
  staggering the entry time (enterDelay) of elements within the same group,
  achieving an "appear group by group" entry animation effect.
  Commonly used in bar charts and line charts for grouped progressive entry display.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "stackEnter"
  - "entry animation"
  - "enterDelay"
  - "grouped animation"
  - "transform"
  - "animation"

related:
  - "g2-animation-intro"
  - "g2-transform-stacky"
  - "g2-mark-interval-grouped"

use_cases:
  - "Bar chart groups entering in batches (X groups appearing sequentially)"
  - "Line chart series drawing one by one"
  - "Progressive data presentation in data storytelling scenarios"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/stack-enter"
---

## Core Concepts

`stackEnter` assigns an `enterDelay` value to each data item:
- Groups data by the `groupBy` channel (default `['x']`)
- Elements within the same group share the same entry delay
- Delay time is accumulated sequentially between different groups

Delay per group = Sum of `enterDuration` of all previous groups.

## Basic Usage (Grouped Bar Chart Entry Animation)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', value: 83 },
    { month: 'Feb', value: 60 },
    { month: 'Mar', value: 95 },
    { month: 'Apr', value: 72 },
    { month: 'May', value: 110 },
  ],
  encode: { x: 'month', y: 'value', color: 'month' },
  transform: [
    {
      type: 'stackEnter',
      groupBy: ['x'],          // Group by x (one batch per month)
      orderBy: null,           // No additional sorting
      duration: 300,           // Animation duration per group (milliseconds), defaults to enterDuration
    },
  ],
  animate: {
    enter: {
      type: 'scaleInY',        // Each group of bars grows from bottom to top
      duration: 300,
    },
  },
});

chart.render();
```

## Multi-series Line Chart Sequential Entry

```javascript
chart.options({
  type: 'line',
  data: multiSeriesData,
  encode: { x: 'date', y: 'value', color: 'series' },
  transform: [
    {
      type: 'stackEnter',
      groupBy: ['color'],    // Group by color (series), each line enters sequentially
      duration: 800,
    },
  ],
  animate: {
    enter: {
      type: 'pathIn',        // Line drawn from left to right
      duration: 800,
    },
  },
});
```

## Configuration Options

```javascript
chart.options({
  transform: [
    {
      type: 'stackEnter',
      groupBy: ['x'],          // Grouping channel, default ['x']
                               // Can be a single string or an array: ['x', 'color']
      orderBy: null,           // Sorting basis between groups: null | 'x' | function
      reverse: false,          // Whether to reverse the order of groups
      duration: undefined,     // Entry duration per group (milliseconds), if not set, uses animate.enter.duration
    },
  ],
});
```

## Common Errors and Fixes

### Error: Forgot to Configure `animate.enter`
```javascript
// ❌ Has `stackEnter` but no `animate.enter`, no animation effect is visible
chart.options({
  transform: [{ type: 'stackEnter', groupBy: ['x'] }],
  // Missing animate configuration!
});

// ✅ Must be used in conjunction with `animate.enter`
chart.options({
  transform: [{ type: 'stackEnter', groupBy: ['x'], duration: 400 }],
  animate: {
    enter: {
      type: 'scaleInY',    // Choose an appropriate entrance animation type
      duration: 400,
    },
  },
});
```

### Error: Inconsistent duration and animate.enter.duration causing disjointed animations
```javascript
// ❌ stackEnter duration does not match animate.enter.duration
chart.options({
  transform: [{ type: 'stackEnter', duration: 500 }],  // 500ms per group
  animate: { enter: { type: 'scaleInY', duration: 200 } },  // ❌ 200ms animation (switches before the group completes)

// ✅ Keep consistent
chart.options({
  transform: [{ type: 'stackEnter', duration: 400 }],
  animate: { enter: { type: 'scaleInY', duration: 400 } },   // ✅ Consistent
});
```