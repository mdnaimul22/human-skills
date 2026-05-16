---
id: "g2-label-transform-contrast-reverse"
title: "G2 ContrastReverse Label Transform"
description: |
  Label contrast reverse transform. Automatically adjusts label color based on the background color,
  ensuring labels display light colors on dark backgrounds and dark colors on light backgrounds.

library: "g2"
version: "5.x"
category: "label-transform"
tags:
  - "label"
  - "contrast"
  - "color"

related:
  - "g2-label-transform-overflow-hide"
  - "g2-comp-label-config"

use_cases:
  - "Bar chart internal labels"
  - "Pie chart labels"
  - "Labels requiring color adjustment based on background"

anti_patterns:
  - "Fixed-color labels do not require this transform"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/label"
---
## Core Concepts

The ContrastReverse label transformation automatically adjusts label colors based on the element's color:
- Dark background → Light label
- Light background → Dark label

**How it works:**
1. Obtain the element's fill color
2. Calculate the color's luminance
3. Select a contrasting color based on the luminance

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
      transform: [{ type: 'contrastReverse' }],
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
        { type: 'contrastReverse' },
        { type: 'overflowHide' },
      ],
    },
  ],
});
```

### Custom Contrast Color

```javascript
// Note: contrastReverse typically uses the default black and white contrast
// If customization is needed, it can be set in the style
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  labels: [
    {
      text: 'value',
      position: 'inside',
      style: {
        fill: '#fff',  // Fixed white
        stroke: '#000',  // Stroke to increase contrast
        lineWidth: 1,
      },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface ContrastReverseTransform {
  type: 'contrastReverse';
  // No additional configuration parameters
}
```

## Comparison with Fixed Colors

| Method | Advantages | Disadvantages |
|--------|------------|---------------|
| contrastReverse | Automatically adapts | May not conform to design style |
| Fixed Color | Consistent style | May lack sufficient contrast |
| Stroke | Increases contrast | May affect clarity |

## Common Errors and Fixes

### Error 1: Incorrect transform Format

```javascript
// ❌ Incorrect: transform should be an array
labels: [{ text: 'value', transform: { type: 'contrastReverse' } }]

// ✅ Correct
labels: [{ text: 'value', transform: [{ type: 'contrastReverse' }] }]
```

### Error 2: Improper position Setting

```javascript
// ⚠️ Note: contrastReverse is primarily used for the inside position
// Labels in the outside position are not on the element and cannot obtain the background color

// ✅ Correct: Used for inside labels
labels: [{
  text: 'value',
  position: 'inside',
  transform: [{ type: 'contrastReverse' }]
}]
```