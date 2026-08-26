---
id: "g2-core-chart-init"
title: "G2 Chart Initialization and Basic Configuration"
description: |
  Introduces the creation of Chart objects in G2 v5, required and optional parameters,
  adaptive sizing, theme configuration, and lifecycle management.
  Must use declarative Spec syntax (chart.options({})), and chained APIs are prohibited.

library: "g2"
version: "5.x"
category: "core"
tags:
  - "Chart"
  - "Initialization"
  - "Container"
  - "autoFit"
  - "Theme"
  - "Lifecycle"
  - "init"
  - "spec"
  - "options"
  - "padding"
  - "paddingLeft"
  - "paddingTop"
  - "paddingRight"
  - "paddingBottom"
  - "margin"
  - "inset"
  - "Layout"

related:
  - "g2-core-encode-channel"
  - "g2-core-data-binding"
  - "g2-core-lifecycle"
  - "g2-theme-builtin"

use_cases:
  - "Start creating any G2 chart"
  - "Configure chart canvas size and container"
  - "Set global theme and padding"

anti_patterns:
  - "Do not create multiple Chart instances on the same container (this will result in multiple canvases)"
  - "Chained APIs are prohibited (chart.interval().encode()...)"
  - "Do not call chart.options({}) multiple times on the same chart (later calls will completely overwrite earlier ones) — when merging configurations, combine them into a single call; when stacking multiple marks, use type: 'view' + children"

difficulty: "beginner"
completeness: "partial"
created: "2024-01-01"
updated: "2025-03-27"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/chart"
---

## Core Concepts

`Chart` is the top-level container object in G2, responsible for managing the canvas, views, coordinate systems, and rendering.

**Must use Spec mode**: Pass the complete description object at once via `chart.options({})`, ensuring a clear structure that is easy to serialize and dynamically generate.

**Prohibit chained APIs**: Chained calls such as `chart.interval().encode()` are prohibited.

## Minimum Viable Example (Spec Mode)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'line',        // Mark type
  data: [
    { x: 1, y: 10 },
    { x: 2, y: 30 },
    { x: 3, y: 20 },
  ],
  encode: { x: 'x', y: 'y' },
});

chart.render();
```

## Complete Chart Container Configuration Options

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  // ── Required ──────────────────────────────
  container: 'container',        // string | HTMLElement: DOM container

  // ── Dimensions ──────────────────────────────
  width: 640,                    // Canvas width (px), default 640
  height: 480,                   // Canvas height (px), default 480
  autoFit: true,                 // Automatically fit container size (ignores width/height)

  // ── Padding ────────────────────────────
  // padding only accepts number or 'auto', does not support array format
  // Default 'auto': G2 automatically calculates based on axes/legends, no manual setting required
  padding: 'auto',               // 'auto' | number (uniform value for all sides)
  // Use the following individual configurations when directional control is needed (higher priority than padding)
  paddingTop: 40,
  paddingRight: 20,
  paddingBottom: 40,
  paddingLeft: 60,
  inset: 0,                      // Data area inset (prevents data points from touching edges)

  // ── Theme ──────────────────────────────
  theme: 'classic',              // 'classic' | 'classicDark' | 'academy'

  // ── Renderer ────────────────────────────
  renderer: undefined,           // Default Canvas, can pass SVG renderer

  // ── Pixel Ratio ────────────────────────────
  devicePixelRatio: window.devicePixelRatio,
});
```

## Complete Structure of Spec Mode

```javascript
chart.options({
  // Mark type
  type: 'interval',

  // Data, different Marks have structural differences, prioritize using the data structure corresponding to the Mark
  data: [...],

  // Visual channel mapping
  encode: {
    x: 'genre',
    y: 'sold',
    color: 'genre',
  },

  // Data transformation
  transform: [{ type: 'stackY' }],

  // Scale
  scale: {
    y: { domain: [0, 500] },
    color: { range: ['#1890ff', '#52c41a'] },
  },

  // Coordinate system
  coordinate: { transform: [{ type: 'transpose' }] },

  // Style
  style: { radius: 4 },

  // Data labels
  labels: [{ text: 'sold', position: 'outside' }],

  // Tooltip
  tooltip: { title: 'genre', items: [{ field: 'sold', name: 'Sales' }] },

  // Axis
  axis: {
    x: { title: 'Game Type' },
    y: { title: 'Sales' },
  },

  // Legend
  legend: {
    color: { position: 'top' },
  },
});
```

## Spec Mode Standard Writing

```javascript
// ✅ Correct: Spec Mode (the only recommended way)
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  style: { radius: 4 },
});

// ❌ Prohibited: Chained API Mode
chart.interval()
  .data([...])
  .encode('x', 'genre')
  .encode('y', 'sold')
  .encode('color', 'genre')
  .style({ radius: 4 });
```

## Responsive Adaptation

```javascript
// autoFit: Width follows the container, height can be fixed
const chart = new Chart({
  container: 'container',
  autoFit: true,
  height: 400,
});

chart.options({ type: 'line', data: [...], encode: { x: 'x', y: 'y' } });
chart.render();
```

## Lifecycle

```javascript
// Initial rendering
chart.render();

// Re-render after updating Spec (changeData only updates data)
chart.options({ type: 'bar',  newData, encode: { x: 'x', y: 'y' } });
chart.render();

// Update data only (better performance)
chart.changeData(newData);

// Destroy
chart.destroy();

// Event listening
chart.on('afterrender', () => console.log('Rendering complete'));
```

## Layout Model: margin / padding / inset

In G2 v5, the view space is divided into four layers, from outer to inner:

```
View Area (width × height)
  └─ margin (outer margin, default 16, fixed whitespace between View Area and Plot Area)
      └─ Plot Area (drawing area)
          └─ padding (inner margin, default 'auto', automatically calculates space for axis/legend/title, etc.)
              └─ Main Area (main area)
                  └─ inset (breathing space, default 0, prevents data points from touching the edges)
                      └─ Content Area (data mark drawing area)
```

- **`margin`**: outer margin, `number`, default `16`, fixed whitespace between View Area and Plot Area, not directly related to component rendering
- **`padding`**: inner margin, `number | 'auto'`, default `'auto'`, automatically calculated by G2 to reserve space for axis/legend/title, etc.; manual setting disables auto-adaptation
- **`inset`**: breathing space, `number`, default `0`, used in scatter plots, etc., to prevent points from touching the edges

```javascript
const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
  margin: 16,        // default, usually no need to modify
  // padding: 'auto',  // default, usually no need to modify
  paddingLeft: 80,   // set individually when only one side needs adjustment
  inset: 8,          // recommended for scatter plots to prevent data points from being clipped
});
```

## Common Errors and Fixes

### Error 0: Multiple Calls to `chart.options({})`

`chart.options()` is a **complete replacement**, not a merge. The second call will completely overwrite the first, causing all previous configurations to be lost.

**Scenario A: Merging Configurations**
```javascript
// ❌ Error: Second options() call overwrites the first, type/encode lost
chart.options({ type: 'interval', encode: { x: 'genre', y: 'sold' } });
chart.options({ style: { radius: 4 } }); // type/encode is gone!

// ✅ Correct: All configurations merged into a single chart.options({}) call
chart.options({
  type: 'interval',
  encode: { x: 'genre', y: 'sold' },
  style: { radius: 4 },
});
```

**Scenario B: Overlaying Multiple Marks (e.g., Main Chart + Text Annotation)**
```javascript
// ❌ Error: Second options() call overwrites the first, interval replaced by text
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'x', y: 'y' },
});
chart.options({
  type: 'text',
  data: [{ x: 0.5, y: 0.1, text: 'Annotation Text' }],
  encode: { x: 'x', y: 'y', text: 'text' },
}); // interval is gone!

// ✅ Correct: Multiple marks overlaid using type: 'view' + children
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      data: [...],
      encode: { x: 'x', y: 'y' },
    },
    {
      type: 'text',
      data: [{ x: 0.5, y: 0.1, text: 'Annotation Text' }],
      encode: { x: 'x', y: 'y', text: 'text' },
      style: { fill: '#E63946', fontSize: 14, textAlign: 'center' },
    },
  ],
});
```

### Error 1: Container Points to a Non-Existent ID
```javascript
// ❌ Incorrect: DOM is not yet loaded
const chart = new Chart({ container: 'chart' });

// ✅ Correct: Ensure DOM exists
document.addEventListener('DOMContentLoaded', () => {
  const chart = new Chart({ container: 'chart', width: 640, height: 400 });
  chart.options({ type: 'line',  [...], encode: { x: 'x', y: 'y' } });
  chart.render();
});
```

### Error 2: Repeated Initialization of the Same Container
```javascript
// ❌ Incorrect: Creates two overlapping canvases
const chart1 = new Chart({ container: 'container' });
const chart2 = new Chart({ container: 'container' });

// ✅ Correct: Destroy the old instance first
chart1.destroy();
const chart2 = new Chart({ container: 'container' });
```

### Error 3: Mixing autoFit with Fixed Width
```javascript
// ❌ Incorrect: autoFit will override width
const chart = new Chart({ container: 'c', autoFit: true, width: 640 });

// ✅ Correct: Set only height when using autoFit
const chart = new Chart({ container: 'c', autoFit: true, height: 400 });
```

### Error 4: Using Array Form for padding (CSS Shorthand)
```javascript
// ❌ Incorrect: padding does not support arrays, in G2 v5 the type is number | 'auto'
const chart = new Chart({
  container: 'container',
  autoFit: true,
  padding: [40, 30, 40, 50],   // ❌ Invalid, will be ignored or throw an exception
});

// ✅ Correct: Uniform padding on all four sides
const chart = new Chart({ container: 'container', padding: 40 });

// ✅ Correct: Directional control using paddingTop/Right/Bottom/Left
const chart = new Chart({
  container: 'container',
  autoFit: true,
  paddingTop: 40,
  paddingRight: 30,
  paddingBottom: 40,
  paddingLeft: 50,
});
```

### Error 5: Setting padding to 0 causes the axis to be truncated
```javascript
// ❌ Incorrect: padding=0 disables automatic calculation, and the axis/legend may not display fully
const chart = new Chart({ container: 'container', padding: 0 });

// ✅ Correct: Default to 'auto'; adjust only the required direction when needed
const chart = new Chart({ container: 'container', paddingLeft: 80 });
// Or maintain default automatic calculation
const chart = new Chart({ container: 'container' });
```