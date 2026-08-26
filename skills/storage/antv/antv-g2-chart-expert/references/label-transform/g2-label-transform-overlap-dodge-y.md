---
id: "g2-label-transform-overlap-dodge-y"
title: "G2 OverlapDodgeY Label Transform"
description: |
  Label Y-direction dodging transform. Automatically adjusts the position of labels when they overlap in the Y direction,
  using an iterative algorithm to avoid label overlap.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "label"
  - "overlap"
  - "dodge"

related:
  - "g2-label-transform-overlap-hide"
  - "g2-label-transform-overflow-hide"
  - "g2-comp-label-config"

use_cases:
  - "Displaying labels for dense data points"
  - "Label dodging in time series charts"
  - "Scenarios requiring all labels to be displayed"

anti_patterns:
  - "May cause layout clutter when there are too many labels"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---
## Core Concepts

The OverlapDodgeY label transform adjusts label positions in the Y direction using an iterative algorithm:
- Detects if adjacent labels overlap in the X direction
- If overlapping, separates them in the Y direction
- Iterates until no overlaps exist or the maximum number of iterations is reached

**Algorithm Features:**
- Time complexity O(n log n)
- Supports setting the maximum number of iterations
- Supports setting the label spacing

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
    { date: '2024-01-01', value: 100, label: 'Event A' },
    { date: '2024-01-02', value: 120, label: 'Event B' },
    { date: '2024-01-02', value: 110, label: 'Event C' },  // Same day, labels may overlap
  ],
  encode: {
    x: 'date',
    y: 'value',
  },
  labels: [
    {
      text: 'label',
      position: 'top',
      transform: [{ type: 'overlapDodgeY' }],
    },
  ],
});

chart.render();
```

## Common Variants

### Custom Spacing

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  labels: [
    {
      text: 'label',
      position: 'top',
      transform: [
        {
          type: 'overlapDodgeY',
          padding: 4,  // Minimum spacing between labels (in pixels)
        },
      ],
    },
  ],
});
```

### Control Iteration Count

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  labels: [
    {
      text: 'label',
      position: 'top',
      transform: [
        {
          type: 'overlapDodgeY',
          maxIterations: 20,  // Maximum iteration count, default is 10
          maxError: 0.1,      // Maximum error, default is 0.1
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
      text: 'label',
      position: 'top',
      transform: [
        { type: 'overlapDodgeY' },
        { type: 'overflowHide' },  // Dodge first, then handle overflow
      ],
    },
  ],
});
```

## Complete Type Reference

```typescript
interface OverlapDodgeYTransform {
  type: 'overlapDodgeY';
  padding?: number;         // Label spacing, default 1
  maxIterations?: number;   // Maximum iterations, default 10
  maxError?: number;        // Maximum error, default 0.1
}
```

## Comparison with Other Label Transforms

| Transform | Function | Advantages | Disadvantages |
|-----------|----------|------------|---------------|
| overlapDodgeY | Y-direction dodging | Retains all labels | May alter layout |
| overlapHide | Hides overlapping labels | Layout stability | Loses some labels |
| overflowHide | Hides overflowing labels | Prevents overflow | May lose labels |

## Diagram of Working Principle

```
Initial State:
  Label A -------- Label B
      ↑ Overlap ↑

After Processing:
  Label B
      ↑
  Label A --------

  (Separated in Y direction)
```

## Common Errors and Fixes

### Error 1: Incorrect transform Format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'overlapDodgeY' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'overlapDodgeY' }] }]
```

### Error 2: Improper Iteration Count Setting

```javascript
// ⚠️ Note: Excessive iterations can impact performance
// When there are many labels, it is recommended to reduce the number of iterations

// Fewer labels
transform: [{ type: 'overlapDodgeY', maxIterations: 20 }]

// More labels
transform: [{ type: 'overlapDodgeY', maxIterations: 5 }]
```

### Error 3: Incorrect Order with Other Transformations

```javascript
// ❌ Incorrect: Hide first, then dodge, poor effect
transform: [
  { type: 'overlapHide' },
  { type: 'overlapDodgeY' },
]

// ✅ Correct: Dodge first, then hide what cannot be handled
transform: [
  { type: 'overlapDodgeY' },
  { type: 'overlapHide' },
]
```