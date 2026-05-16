---
id: "g2-label-transform-overlap-hide"
title: "G2 OverlapHide Label Transform"
description: |
  Label overlap hiding transform. Automatically hides some labels when they overlap,
  preventing visual clutter. Supports determining the hiding order based on priority.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "tag"
  - "label"
  - "overlap"
  - "hide"
  - "overlap"

related:
  - "g2-label-transform-overlap-dodge-y"
  - "g2-label-transform-overflow-hide"
  - "g2-comp-label-config"

use_cases:
  - "Label display for dense data points"
  - "Label handling in time series charts"
  - "Scenarios requiring concise display"

anti_patterns:
  - "Scenarios where all labels must be displayed (use overlapDodgeY instead)"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---
## Core Concepts

The OverlapHide label transform hides some labels by detecting label overlaps:
- Detects each label in order to see if it overlaps with already displayed labels
- If overlapping, hides the current label
- Supports setting priorities to determine the hiding order

**How it works:**
1. Get all labels
2. Sort by priority (optional)
3. Check each label in sequence to see if it overlaps with already displayed labels
4. If overlapping, hide; otherwise, display

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'line',
  data: [
    { date: '2024-01-01', value: 100 },
    { date: '2024-01-02', value: 120 },
    { date: '2024-01-03', value: 110 },
    { date: '2024-01-04', value: 130 },
  ],
  encode: {
    x: 'date',
    y: 'value',
  },
  labels: [
    {
      text: 'value',
      position: 'top',
      transform: [{ type: 'overlapHide' }],
    },
  ],
});

chart.render();
```

## Common Variants

### Set Priority

```javascript
chart.options({
  type: 'interval',
  data: [
    { category: 'A', value: 100, priority: 2 },
    { category: 'B', value: 50, priority: 1 },
    { category: 'C', value: 80, priority: 3 },
  ],
  encode: { x: 'category', y: 'value' },
  labels: [
    {
      text: 'value',
      position: 'inside',
      transform: [
        {
          type: 'overlapHide',
          priority: (a, b) => a.priority - b.priority,  // Higher priority displayed first
        },
      ],
    },
  ],
});
```

### Combine with Other Transformations

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  labels: [
    {
      text: 'value',
      position: 'top',
      transform: [
        { type: 'overlapDodgeY' },  // Try dodging first
        { type: 'overlapHide' },    // Hide if dodging is not possible
      ],
    },
  ],
});
```

## Complete Type Reference

```typescript
interface OverlapHideTransform {
  type: 'overlapHide';
  priority?: (a: any, b: any) => number;  // Priority comparison function
}
```

## Comparison with Other Label Transformations

| Transform | Function | Advantages | Disadvantages |
|-----------|----------|------------|---------------|
| overlapHide | Hide overlapping labels | Stable layout | Loss of some labels |
| overlapDodgeY | Dodge in Y direction | Retains all labels | May alter layout |
| overflowHide | Hide overflowing labels | Prevents overflow | May lose labels |

## Priority Sorting Example

```javascript
// Sort by numerical value: larger values displayed first
labels: [{
  text: 'value',
  transform: [{
    type: 'overlapHide',
    priority: (a, b) => b.value - a.value
  }]
}]

// Sort by specific order
labels: [{
  text: 'value',
  transform: [{
    type: 'overlapHide',
    priority: (a, b) => {
      const order = ['A', 'B', 'C', 'D'];
      return order.indexOf(a.category) - order.indexOf(b.category);
    }
  }]
}]
```

## Common Errors and Fixes

### Error 1: Incorrect transform Format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'overlapHide' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'overlapHide' }] }]
```

### Error 2: Incorrect Return Value from Priority Function

```javascript
// ❌ Incorrect: Priority function should return a number
priority: (a, b) => a.value > b.value

// ✅ Correct: Return a positive number to prioritize a, negative for b
priority: (a, b) => b.value - a.value
```

### Error 3: Incorrect Order with Other Transformations

```javascript
// ❌ Incorrect: Hide first, then handle other issues
transform: [
  { type: 'overlapHide' },
  { type: 'overlapDodgeY' },  // Hidden labels cannot dodge
]

// ✅ Correct: Try other solutions first, then hide
transform: [
  { type: 'overlapDodgeY' },
  { type: 'overlapHide' },
]
```