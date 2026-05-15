---
id: "g2-label-transform-overflow-stroke"
title: "G2 OverflowStroke Label Transform"
description: |
  Label overflow stroke transform. Automatically adds a stroke when the label exceeds the element boundary,
  enhancing label readability.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "标签"
  - "label"
  - "溢出"
  - "描边"
  - "stroke"

related:
  - "g2-label-transform-overflow-hide"
  - "g2-label-transform-contrast-reverse"
  - "g2-comp-label-config"

use_cases:
  - "Pie chart external labels"
  - "Labels requiring enhanced readability"
  - "Label display in complex backgrounds"

anti_patterns:
  - "Stroke not needed in simple scenarios"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---

## Core Concepts

The OverflowStroke label transformation detects whether a label exceeds the element boundaries:
- If it does, a stroke is added to the label
- Enhances label readability on complex backgrounds

**How it Works:**
1. Calculate the bounding boxes of the element and the label
2. Detect if the label exceeds the element boundaries
3. If it exceeds, add a stroke style

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
    { category: 'A', value: 100 },
    { category: 'B', value: 150 },
    { category: 'C', value: 80 },
  ],
  encode: {
    x: 'category',
    y: 'value',
    color: 'category',
  },
  labels: [
    {
      text: 'value',
      position: 'inside',
      transform: [{ type: 'overflowStroke' }],
    },
  ],
});

chart.render();
```

## Common Variants

### Combine with Other Transformations

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  labels: [
    {
      text: 'value',
      position: 'inside',
      transform: [
        { type: 'overflowStroke' },
        { type: 'contrastReverse' },
      ],
    },
  ],
});
```

## Complete Type Reference

```typescript
interface OverflowStrokeTransform {
  type: 'overflowStroke';
  // No additional configuration parameters
}
```

## Comparison with Other Label Transforms

| Transform | Function | Handling Method |
|-----------|----------|-------------|
| overflowStroke | Overflow Stroke | Add Stroke |
| overflowHide | Overflow Hide | Hide Label |
| contrastReverse | Contrast Reverse | Change Color |

## Common Errors and Fixes

### Error 1: Incorrect transform format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'overflowStroke' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'overflowStroke' }] }]
```

### Error 2: Incorrect Order with Other Transformations

```javascript
// ⚠️ Note: Stroke should be applied after color adjustment
// Recommended order: contrastReverse → overflowStroke

// ✅ Correct order
transform: [
  { type: 'contrastReverse' },
  { type: 'overflowStroke' },
]
```