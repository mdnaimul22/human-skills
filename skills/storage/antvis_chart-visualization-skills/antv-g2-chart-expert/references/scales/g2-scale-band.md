---
id: "g2-scale-band"
title: "G2 Band Categorical Scale"
description: |
  Band Scale is a scale in G2 used for categorical x-axes (bar charts, etc.),
  mapping discrete categorical values to equal-width intervals (bands) and supporting the configuration of inner and outer padding.
  It is automatically used when encode.x maps to a string or categorical field.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "band"
  - "categorical scale"
  - "bar chart"
  - "padding"
  - "scale"
  - "ordinal"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-interval-grouped"
  - "g2-comp-axis-config"

use_cases:
  - "Configure the width and spacing of bars in a bar chart"
  - "Specify the display order of a categorical axis"
  - "Control the alignment of categorical data"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/band"
---

## Auto Recognition

When `encode.x` maps to a string type field, G2 automatically uses a Band Scale, typically without requiring explicit configuration:

```javascript
chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
  ],
  encode: { x: 'genre', y: 'sold' },   // 'genre' is a string, automatically uses Band Scale
});
```

## Configure Bar Width (Padding)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  scale: {
    x: {
      type: 'band',
      padding: 0.3,         // Inner spacing between bars (0-1), default 0.1
      // paddingInner: 0.3, // Same as padding
      // paddingOuter: 0.2, // Outer spacing at both ends
    },
  },
});
```

## Customizing Category Order

```javascript
// Specify the display order of categories (not following data order)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  scale: {
    x: {
      type: 'band',
      domain: ['Action', 'Shooter', 'Sports', 'Strategy', 'Other'],  // Explicitly specify the order
    },
  },
});
```

## Heatmap (cell mark)

The `cell` mark also depends on bandwidth. Discrete x/y axes should use `band` (or omit it to let G2 infer automatically). **Do not use the `point` scale**——point's bandwidth=0, making the grid invisible.

```javascript
chart.options({
  type: 'cell',
  data: heatmapData,
  encode: { x: 'date', y: 'month', color: 'value' },
  // ✅ Omit x/y scale, G2 automatically uses band for cell
  scale: {
    color: { type: 'sequential', palette: 'blues' },
  },
});

// ✅ Can also explicitly write band
scale: {
  x: { type: 'band' },
  y: { type: 'band' },
  color: { type: 'sequential', palette: 'blues' },
}

// ❌ Do not use point: bandwidth=0, grid disappears
scale: {
  x: { type: 'point' },  // ❌
  y: { type: 'point' },  // ❌
}
```

## Common Errors and Fixes

### Error: padding exceeds the range [0, 1]
```javascript
// ❌ Error: padding > 1, bar width becomes negative
chart.options({ scale: { x: { padding: 1.5 } } });

// ✅ Correct: padding between 0-1, 0 = no spacing, 0.5 = bar width and spacing each occupy half
chart.options({ scale: { x: { padding: 0.3 } } });
```