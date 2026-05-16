---
id: "g2-label-transform-overflow-hide"
title: "G2 OverflowHide Label Transform"
description: |
  Label overflow hide transform. Automatically hides labels when they exceed the boundaries of their associated elements,
  preventing visual clutter caused by label overflow.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "标签"
  - "label"
  - "溢出"
  - "隐藏"
  - "overflow"
  - "hide"

related:
  - "g2-label-transform-overlap-hide"
  - "g2-label-transform-overlap-dodge-y"
  - "g2-comp-label-config"

use_cases:
  - "Pie chart label overflow handling"
  - "Bar chart data labels"
  - "Label display for small-sized elements"

anti_patterns:
  - "Scenarios where labels must be fully displayed"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---
## Core Concepts

The OverflowHide label transformation detects whether a label exceeds the boundaries of its parent element:
- If the label is within the element's boundaries, it is displayed normally
- If the label exceeds the boundaries, it is automatically hidden

**How it Works:**
1. Calculate the bounding box of the element
2. Calculate the bounding box of the label
3. Detect if the label overflows the element's boundaries
4. Hide the label if it overflows

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { category: 'A', value: 10 },
    { category: 'B', value: 50 },
    { category: 'C', value: 5 },  // Small bar, label may overflow
  ],
  encode: {
    x: 'category',
    y: 'value',
  },
  labels: [
    {
      text: 'value',
      position: 'inside',
      transform: [{ type: 'overflowHide' }],
    },
  ],
});

chart.render();
```

## Common Variants

### Pie Chart Label Overflow Handling

```javascript
chart.options({
  type: 'interval',
  coordinate: { type: 'theta' },
  data,
  encode: { y: 'value', color: 'category' },
  labels: [
    {
      text: 'category',
      position: 'inside',
      transform: [{ type: 'overflowHide' }],
    },
  ],
});
```

### Combine with Other Label Transformations

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  labels: [
    {
      text: 'value',
      position: 'inside',
      transform: [
        { type: 'overflowHide' },
        { type: 'overlapHide' },  // Handle overflow first, then handle overlap
      ],
    },
  ],
});
```

## Complete Type Reference

```typescript
interface OverflowHideTransform {
  type: 'overflowHide';
  // No additional configuration parameters
}
```

## Comparison with Other Label Transformations

| Transform | Function | Applicable Scenarios |
|-----------|----------|---------------|
| overflowHide | Hide overflowing labels | Labels exceed element boundaries |
| overlapHide | Hide overlapping labels | Labels overlap each other |
| overlapDodgeY | Dodge in Y direction | Labels overlap vertically |

## Common Errors and Fixes

### Error 1: Incorrect transform Format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'overflowHide' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'overflowHide' }] }]
```

### Error 2: Improper position Setting

```javascript
// ⚠️ Note: Labels in the 'outside' position typically do not overflow
// overflowHide is primarily used for 'inside' positions

// For inside labels
labels: [{
  text: 'value',
  position: 'inside',
  transform: [{ type: 'overflowHide' }]
}]

// For outside labels, consider using overlapHide
labels: [{
  text: 'value',
  position: 'outside',
  transform: [{ type: 'overlapHide' }]
}]
```

### Error 3: Incorrect Order with Other Transformations

```javascript
// ⚠️ Note: Transformation order affects the result

// Recommended: Handle overflow first, then handle overlap
transform: [
  { type: 'overflowHide' },
  { type: 'overlapHide' },
]
```