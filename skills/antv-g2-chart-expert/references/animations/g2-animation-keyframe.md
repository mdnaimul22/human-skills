

---
id: "g2-animation-keyframe"
title: "G2 Keyframe Animation (timingKeyframe)"
description: |
  timingKeyframe is a composition type in G2 v5 that plays multiple chart views sequentially to achieve a data storytelling effect.
  Each sub-view is a 'keyframe', and the system automatically interpolates transitions between frames, supporting morphing animation.
library: "g2"
version: "5.x"
category: "animations"
tags:
  - "timingKeyframe"
  - "keyframe"
  - "data story"
  - "keyframe"
  - "morphing"
  - "animation"
  - "composition"
related:
  - "g2-animation-intro"
  - "g2-core-view-composition"
use_cases:
  - "Demonstrate how data changes from one chart type to another (bar chart → line chart)"
  - "Show the evolution of data over time"
  - "Data journalism and visual storytelling"
difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/composition/timing-keyframe"
---
## Minimal Runnable Example (Bar Chart → Line Chart)
```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', value: 83 },
  { month: 'Feb', value: 60 },
  { month: 'Mar', value: 95 },
  { month: 'Apr', value: 72 },
  { month: 'May', value: 110 },
];

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'timingKeyframe', // Keyframe composition type
  duration: 1000, // Transition duration per frame (ms)
  iterationCount: 2, // Iteration count ('infinite' for infinite loop)
  direction: 'alternate', // 'normal' | 'reverse' | 'alternate' | 'reverse-alternate'
  easing: 'ease-in-out-sine',
  children: [ // Keyframe 1: Bar Chart
    {
      type: 'interval',
      data,
      encode: { x: 'month', y: 'value', color: 'month' },
      axis: { y: { title: 'Monthly Sales' } },
    },
    // Keyframe 2: Line Chart (automatically interpolates animation between the two)
    {
      type: 'line',
      data,
      encode: { x: 'month', y: 'value' },
      style: { lineWidth: 3 },
    },
  ],
});

chart.render();
```
## Multiple Keyframes (Data Update Animation)
```javascript
chart.options({
  type: 'timingKeyframe',
  duration: 800,
  iterationCount: 'infinite',
  direction: 'alternate',
  children: [
    // Keyframe 1: 2022 Data
    {
      type: 'interval',
      data: data2022,
      encode: { x: 'city', y: 'gdp', color: 'city' },
      title: '2022 GDP',
    },
    // Keyframe 2: 2023 Data (same fields, automatic morphing transition)
    {
      type: 'interval',
      data: data2023,
      encode: { x: 'city', y: 'gdp', color: 'city' },
      title: '2023 GDP',
    },
  ],
});
```
## Configuration Options
```javascript
chart.options({
  type: 'timingKeyframe',
  duration: 1000, // Transition duration between keyframes (ms), default 1000
  iterationCount: 1, // Iteration count, default 1; 'infinite' for infinite loop
  direction: 'normal', // Playback direction:
  // 'normal' - Forward
  // 'reverse' - Reverse
  // 'alternate' - Alternating forward and reverse
  // 'reverse-alternate' - Alternating reverse and forward
  easing: 'ease-in-out-sine', // Easing function, default 'ease-in-out-sine'
  children: [/* Configuration for each keyframe view */],
});
```
## Common Errors and Fixes
### Error 1: Inconsistent encode field names in children frames — Morphing fails
```javascript
// ❌ Field names inconsistent, correspondence cannot be identified, morphing effect lost
children: [
  { type: 'interval', encode: { x: 'month', y: 'sales' } }, // sales
  { type: 'line', encode: { x: 'month', y: 'revenue' } }, // revenue ❌ Different names
];

// ✅ Same field names required for smooth morphing
children: [
  { type: 'interval', encode: { x: 'month', y: 'value' } },
  { type: 'line', encode: { x: 'month', y: 'value' } }, // ✅ Same named fields
];
```
### Error 2: iterationCount written as a number
```javascript
// ❌ Error: should be string 'infinite', not number
chart.options({ iterationCount: Infinity }); // ❌

// ✅ Correct
chart.options({ iterationCount: 'infinite' }); // ✅
chart.options({ iterationCount: 3 }); // ✅ Or specific number
```