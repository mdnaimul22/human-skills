---
id: "g2-interaction-element-highlight"
title: "G2 Element Highlight Interaction (elementHighlight)"
description: |
  elementHighlight is one of the most commonly used interactions in G2 v5, highlighting the current element on mouse hover,
  while also allowing the option to highlight elements of the same series or link to other views. It supports all Mark types, including bar charts, line charts, scatter plots, and more.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "elementHighlight"
  - "highlight"
  - "interaction"
  - "hover"
  - "interaction"
  - "spec"

related:
  - "g2-interaction-brush"
  - "g2-mark-interval-basic"
  - "g2-mark-line-basic"

use_cases:
  - "Bar chart hover highlights the current bar"
  - "Line chart hover highlights the current series"
  - "Scatter plot hover highlights data points of the same category"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/element-highlight"
---

## Basic Usage (Bar Chart Highlight)

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
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
    { genre: 'Shooter',  sold: 350 },
    { genre: 'Other',    sold: 150 },
  ],
  encode: { x: 'genre', y: 'sold' },
  interaction: { elementHighlight: true },   // Highlight the current bar on hover
});

chart.render();
```

## Highlight Background Color Configuration

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  interaction: {
    elementHighlight: {
      background: true,              // Whether to display the highlight background
      backgroundFill: '#f0f0f0',    // Background fill color
    },
  },
});
```

## Line Chart: Highlight Current Series

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'series' },
  interaction: {
    elementHighlight: true,        // Hover to highlight the current line
  },
});
```

## elementHighlightByColor: Highlight Elements of the Same Color Series

```javascript
// Highlight all elements of the same color (series) on hover
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
  interaction: {
    elementHighlightByColor: true,   // Highlight all bars of the same series
  },
});
```

## elementHighlightByX: Highlight Elements at the Same X Position

```javascript
// Highlight all elements with the same x value on hover (suitable for grouped bar charts)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  interaction: {
    elementHighlightByX: true,    // Highlight all elements in the same group (same x position)
  },
});
```

## Enable Tooltip + Highlight Simultaneously

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'revenue', color: 'product' },
  transform: [{ type: 'dodgeX' }],
  interaction: {
    elementHighlight: true,    // Element Highlight
    tooltip: true,             // Tooltip
  },
  tooltip: {
    title: 'month',
    items: [
      { field: 'revenue', valueFormatter: (v) => `$${v}万` },
    ],
  },
});
```
## Listening to Highlight Events

```javascript
chart.on('element:highlight', (event) => {
  const datum = event.data?.data;
  console.log('Highlighted element data:', datum);
});

chart.on('element:unhighlight', () => {
  console.log('Unhighlighted');
});
```

## Common Errors and Fixes

### Error: interaction written as an object
```javascript
// ❌ Error: interaction must be an array (old syntax)
chart.options({
  interaction: { type: 'elementHighlight' },
});

// ✅ Correct (new version supports object form)
chart.options({
  interaction: { elementHighlight: true },
});
```

### Error: Confusing elementHighlight with elementHighlightByColor
```javascript
// ❌ Using both simultaneously causes duplicate responses
chart.options({
  interaction: {
    elementHighlight: true,
    elementHighlightByColor: true,
  },
});

// ✅ Choose one based on requirements
// - elementHighlight: Highlights only the single element under the mouse cursor
// - elementHighlightByColor: Highlights all elements of the same color (series)
// - elementHighlightByX: Highlights all elements at the same x-position
```

### Error: Nested view in view's children causes a white screen
```javascript
// ❌ Error: Nesting view in children leads to rendering failure
chart.options({
  type: 'view',
  children: [
    {
      type: 'view', // Nested view is not allowed
      children: [...]
    }
  ]
});

// ✅ Correct: Use a top-level container or a single view structure
chart.options({
  type: 'view',
  children: [
    { type: 'interval', ... },
    { type: 'image', ... }
  ]
});
```

### Error: Image Mark Not Displayed Due to Incorrect Configuration
```javascript
// ❌ Error: Missing necessary encode and style configurations
{
  type: 'image',
  data: [{ url: '...' }],
  encode: { x: () => 0, y: () => 0 } // Not suitable for centering
}

// ✅ Correct: Using style to set fixed position and size
{
  type: 'image',
  style: {
    x: '50%', // Centered
    y: '50%',
    width: 80,
    height: 80
  },
  encode: {
    src: 'url'
  }
}
```

</skill>