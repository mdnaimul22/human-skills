---
id: "g2-mark-image"
title: "G2 Image Mark"
description: |
  The image mark renders images at specified positions in a chart, suitable for scenarios such as icon-based scatter plots (replacing points with icons), icon annotations on maps, and labels with images.
  The `src` channel binds the image URL, the `x`/`y` channels determine the position, and the `size` channel controls the size.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "image"
  - "picture"
  - "icon"
  - "icon scatter plot"

related:
  - "g2-mark-point-scatter"
  - "g2-mark-text"

use_cases:
  - "Replace scatter points with brand logos/icons (icon scatter plot)"
  - "Insert explanatory images at specific coordinate positions"
  - "Combine with icon annotations on maps"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/point/#image"
---

## Minimum Viable Example (Icon Scatter Plot)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { country: 'China',    gdp: 17.7, icon: 'https://example.com/flags/cn.png' },
  { country: 'United States',    gdp: 25.5, icon: 'https://example.com/flags/us.png' },
  { country: 'Japan',    gdp: 4.2,  icon: 'https://example.com/flags/jp.png' },
  { country: 'Germany',    gdp: 4.1,  icon: 'https://example.com/flags/de.png' },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'image',
  data,
  encode: {
    x: 'country',  // x position (categorical axis)
    y: 'gdp',      // y position (numerical axis)
    src: 'icon',   // image URL field
    size: 40,      // image size (px), fixed value or field name
  },
});

chart.render();
```

## Image + Point Overlay (Icon + Data Point)

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'image',
      encode: { x: 'x', y: 'y', src: 'icon', size: 32 },
    },
    {
      type: 'text',
      encode: { x: 'x', y: 'y', text: 'label' },
      style: { textAnchor: 'middle', dy: 20, fontSize: 12 },
    },
  ],
});
```

## Configuration Options

```javascript
chart.options({
  type: 'image',
  data,
  encode: {
    x: 'xField',       // x coordinate
    y: 'yField',       // y coordinate
    src: 'imageUrl',   // image URL field (or fixed URL string)
    size: 'sizeField', // image size (px), can be a field name or a fixed value
  },
  style: {
    preserveAspectRatio: 'xMidYMid meet',  // image scaling strategy (SVG standard)
  },
});
```

## Common Errors and Fixes

### Error 1: The `src` channel is written with the image data itself, not the URL
```javascript
// ❌ Incorrect: `src` should be the URL field name, not base64 or blob
chart.options({
  encode: { src: btoa(imageData) },  // ❌ Cannot pass a base64 string (requires a full data: URL)
});

// ✅ Correct: Pass the URL field name, with the data containing the full URL
chart.options({
  encode: { src: 'iconUrl' },  // ✅ The `iconUrl` field in the data is in the format 'https://...'
});
```

### Error 2: Size Not Set—Default Image Size May Be Too Large or Too Small
```javascript
// ❌ Size not set, image may be too large and overlay other elements
chart.options({
  type: 'image',
  encode: { x: 'x', y: 'y', src: 'icon' },  // ❌ No size
});

// ✅ Explicitly set an appropriate size
chart.options({
  encode: { x: 'x', y: 'y', src: 'icon', size: 36 },  // ✅
});
```