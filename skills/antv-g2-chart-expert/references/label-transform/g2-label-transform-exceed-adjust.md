---
id: "g2-label-transform-exceed-adjust"
title: "G2 ExceedAdjust Label Transform"
description: |
  Label exceed adjustment transform. Automatically adjusts the position of labels when they exceed the specified range,
  ensuring labels are displayed within the visible area.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "标签"
  - "label"
  - "超出"
  - "调整"
  - "exceed"
  - "adjust"

related:
  - "g2-label-transform-overflow-hide"
  - "g2-label-transform-overlap-dodge-y"
  - "g2-comp-label-config"

use_cases:
  - "Chart edge label adjustment"
  - "Small element labels"
  - "Scenarios requiring complete labels"

anti_patterns:
  - "Scenarios where labels can be hidden (use overflowHide instead)"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---
## Core Concepts

ExceedAdjust label transformation detects whether labels exceed the visible area:
- If they do, it automatically adjusts the label position
- Ensures labels are fully displayed

**How it Works:**
1. Calculate the label's bounding box
2. Detect if it exceeds the chart boundaries
3. If it does, adjust the position inward

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'point',
  data: [
    { x: 10, y: 100 },
    { x: 20, y: 150 },
    { x: 30, y: 200 },  // may be at the top edge of the chart
  ],
  encode: {
    x: 'x',
    y: 'y',
  },
  labels: [
    {
      text: 'y',
      position: 'top',
      transform: [{ type: 'exceedAdjust' }],
    },
  ],
});

chart.render();
```

## Common Variants

### Combine with Other Transformations

```javascript
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  labels: [
    {
      text: 'y',
      position: 'top',
      transform: [
        { type: 'exceedAdjust' },
        { type: 'overlapDodgeY' },
      ],
    },
  ],
});
```

## Complete Type Reference

```typescript
interface ExceedAdjustTransform {
  type: 'exceedAdjust';
  // No additional configuration parameters
}
```

## Comparison with Other Label Transforms

| Transform | Function | Handling Method |
|-----------|----------|-------------|
| exceedAdjust | Exceed Adjustment | Move Position |
| overflowHide | Overflow Hide | Hide Label |
| overlapDodgeY | Overlap Dodge | Separate in Y Direction |

## Common Errors and Fixes

### Error 1: Incorrect transform Format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'exceedAdjust' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'exceedAdjust' }] }]
```

### Error 2: Incorrect Order with Other Transformations

```javascript
// ⚠️ Note: Transformation order affects the result
// It is recommended to handle exceed first, then overlap

// ✅ Correct Order
transform: [
  { type: 'exceedAdjust' },
  { type: 'overlapDodgeY' },
]
```