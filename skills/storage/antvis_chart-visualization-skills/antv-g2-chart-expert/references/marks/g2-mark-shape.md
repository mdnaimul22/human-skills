---
id: "g2-mark-shape"
title: "G2 Shape Custom Graphic Mark"
description: |
  The shape mark is a feature in G2 v5 used for drawing fully custom graphics,
  rendering any SVG/Canvas graphics by registering custom Shape functions.
  Unlike the image mark (which uses images), the shape mark draws vector graphics using code,
  and can respond to state changes (highlight, select, etc.).
  It is suitable for visualization scenarios requiring special graphic symbols or custom markers.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "shape"
  - "custom graphic"
  - "register"
  - "custom shape"
  - "vector graphic"

related:
  - "g2-mark-image"
  - "g2-mark-point-scatter"
  - "g2-core-chart-init"

use_cases:
  - "Using custom icons instead of default circles in scatter plots"
  - "Drawing custom landmark symbols on maps"
  - "Customized graphic markers for specific business scenarios"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/extra-topics/custom-mark"
---

## Core Concepts

The `shape` mark requires custom shapes to be registered first using `register('shape.xxx', renderFn)`,
then specify the shape name in `style.shape` of the mark.

The custom Shape rendering function receives `(style, context)` parameters:
- `style`: Contains style properties such as x/y coordinates, color, size, etc.
- `context`: G rendering context, includes document, etc.

## Minimum Viable Example

```javascript
import { Chart, register } from '@antv/g2';
import { Circle } from '@antv/g';

// 1. Register a custom shape (draw a circle with a cross)
register('shape.crossCircle', (style, context) => {
  const { x, y, r = 10, fill, stroke } = style;
  const group = new context.document.createElement('g', {});
  const circle = new Circle({ style: { cx: x, cy: y, r, fill, stroke } });
  group.appendChild(circle);
  return group;
});

// 2. Use the custom shape
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'category', size: 'value' },
  style: {
    shape: 'crossCircle',   // Use the registered custom shape name
  },
});

chart.render();
```

## Fully Custom Shapes (Using @antv/g Graphics)

```javascript
import { Chart, register } from '@antv/g2';
import { Path, Group } from '@antv/g';

// Register star shape
register('shape.star', (style, context) => {
  const { x, y, r = 10, fill = '#1890ff', opacity = 1 } = style;

  // Calculate star path
  const path = [];
  for (let i = 0; i < 5; i++) {
    const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
    const px = x + r * Math.cos(angle);
    const py = y + r * Math.sin(angle);
    path.push(i === 0 ? `M ${px} ${py}` : `L ${px} ${py}`);
  }
  path.push('Z');

  const shape = new Path({
    style: {
      d: path.join(' '),
      fill,
      opacity,
    },
  });
  return shape;
});

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y', color: 'type' },
  style: {
    shape: 'star',
    r: 12,
  },
});

chart.render();
```

## Selection with image mark

```javascript
// Use image file as marker
chart.options({
  type: 'image',
  data,
  encode: { x: 'x', y: 'y', src: 'iconUrl' },  // src is the image URL
  style: { width: 24, height: 24 },
});

// Draw vector graphics using code
register('shape.myIcon', (style) => { /* ... */ });
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  style: { shape: 'myIcon' },
});
```

## Common Errors and Fixes

### Error: Forgot to Register Before Using Custom Shape
```javascript
// ❌ Error: Using without registration, the shape will not render
chart.options({
  type: 'point',
  style: { shape: 'myCustomShape' },  // ❌ myCustomShape is not registered
});

// ✅ Register first, then use
register('shape.myCustomShape', (style) => { /* Return G shape */ });
chart.options({
  type: 'point',
  style: { shape: 'myCustomShape' },  // ✅
});
```