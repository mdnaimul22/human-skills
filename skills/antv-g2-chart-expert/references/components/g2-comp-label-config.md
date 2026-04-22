---
id: "g2-comp-label-config"
title: "G2 Data Label Configuration (labels)"
description: |
  Detailed explanation of the labels field configuration in G2 v5 Spec mode, covering label text, position, formatting,
  selectors (displaying only partial labels), and style customization. Note: Use labels (plural) in Spec mode.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "labels"
  - "label"
  - "data labels"
  - "text labels"
  - "position"
  - "formatter"
  - "spec"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-line-basic"
  - "g2-comp-annotation"

use_cases:
  - "Display values above bars"
  - "Show series names at the end of lines"
  - "Display percentages inside and outside pie sectors"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/label"
---

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  labels: [
    {
      text: 'sold',          // Display the value of which field (field name string or function)
      position: 'outside',   // Label position
    },
  ],
});

chart.render();
```

## Common Position Descriptions

| position Value | Applicable Mark | Effect |
|----------------|-----------------|---------|
| `'outside'`    | interval        | Outside the top of the column (default) |
| `'inside'`     | interval        | Center inside the column |
| `'top'`        | interval        | Top of the column (adjacent to the top) |
| `'right'`      | interval        | Right side of the column |
| `'outside'`    | arc (pie chart) | Lead line outside the sector |
| `'inside'`     | arc (pie chart) | Inside the sector |
| `'top'`        | point           | Above the point |
| `'right'`      | line            | Right side of the line end |

## Formatting Label Text

```javascript
labels: [
  {
    // Function method: Access the complete data row
    text: (d) => `${d.sold.toLocaleString()} million`,

    // Or string field name (automatically retrieves the value of the field)
    // text: 'sold',
  },
],
```
## Complete label configuration

```javascript
labels: [
  {
    text: (d) => d.value.toFixed(1),  // Label text
    position: 'outside',               // Position

    // ── Style ─────────────────────────────────
    style: {
      fontSize: 12,
      fill: '#333',
      fontWeight: 'normal',
      textAlign: 'center',
      dy: -4,                          // y-direction offset (px)
      dx: 0,                           // x-direction offset
    },

    // ── Selector (display only partial labels) ──────────────
    selector: 'last',                  // 'last' | 'first' | (data) => datum
    // Filter (display labels only for data meeting the condition)
    filter: (d) => d.value > 50,

    // ── Connector (commonly used for pie chart external labels) ──────────
    connector: true,
    connectorStroke: '#aaa',
    connectorLineWidth: 1,
  },
],
```

## Line End Labels

```javascript
// Display series name only at the last point of each line
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  labels: [
    {
      text: 'type',         // Display series name
      selector: 'last',     // Show only at the last data point
      position: 'right',
      style: { fontSize: 11 },
    },
  ],
});
```

## Stacked Column Center Labels

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  labels: [
    {
      text: (d) => d.value >= 30 ? d.value : '',  // Do not display when value is too small
      position: 'inside',
      style: { fill: 'white', fontSize: 11 },
    },
  ],
});
```

## Common Errors and Fixes

### Error: Written as label (singular) in Spec Mode
```javascript
// ❌ Incorrect: The chained API is .label(), but in Spec mode, it is labels (plural and an array)
chart.options({ label: { text: 'value' } });

// ✅ Correct: Use the labels array in Spec
chart.options({ labels: [{ text: 'value' }] });
```

### Error: Numeric Constant Passed to `text`
```javascript
// ❌ Error: `text` is a number (0), all labels display '0'
chart.options({ labels: [{ text: 0 }] });

// ✅ Correct: `text` should be a field name string or a function
chart.options({ labels: [{ text: 'value' }] });
chart.options({ labels: [{ text: (d) => d.value.toFixed(1) }] });
```