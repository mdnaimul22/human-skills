---
id: "g2-interaction-tooltip"
title: "G2 Tooltip Interaction Configuration"
description: |
  Configure the Tooltip for G2 charts, including content customization, formatting, and custom rendering.
  In Spec mode, the tooltip field at the Mark level controls the content,
  while the interaction field at the chart level controls Tooltip behavior.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "Tooltip"
  - "tooltip"
  - "interaction"
  - "hover"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-interaction-crosshair"

use_cases:
  - "Add data hover tooltip to charts"
  - "Customize the fields and format displayed in the Tooltip"
  - "Disable unnecessary Tooltips"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/tooltip"
---
## Core Concepts

In G2 Spec mode, Tooltip has two configuration locations:
- **Mark-level `tooltip` field**: Controls the display content of the Tooltip for that Mark
- **Chart-level `interaction` field**: Controls the trigger behavior and custom rendering of the Tooltip

G2 has Tooltip enabled by default, displaying the data of the current element when the mouse hovers over it.

## Basic Usage (Spec Mode)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  tooltip: {
    title: 'genre',     // Tooltip title field
    items: [
      { field: 'sold', name: 'Sales', valueFormatter: (v) => `${v} million` },
    ],
  },
});

chart.render();
```

## tooltip Field Detailed Configuration

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'x', y: 'y' },
  tooltip: {
    // title: field name string | fixed string | function
    title: 'name',

    // items: defines the data rows displayed in the Tooltip
    items: [
      // Format 1: field name string (shortcut)
      'value',

      // Format 2: object configuration
      {
        field: 'value',                              // data field
        name: 'Value',                               // display name
        valueFormatter: (v) => `${v.toFixed(2)}%`,  // value formatting
        color: '#1890ff',                            // color marker
      },

      // Format 3: function (fully custom)
      (data) => ({
        name: 'Calculated Value',
        value: data.a + data.b,
      }),
    ],
  },
});
```

## Disable Tooltip

```javascript
// Disable Tooltip for the entire chart
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'x', y: 'y' },
  interaction: { tooltip: false },   // Disable at chart level
});

// Or disable Tooltip for a specific Mark (pass false)
chart.options({
  type: 'interval',
  tooltip: false,   // This Mark does not provide Tooltip content
});
```

## Custom Tooltip Rendering (HTML)

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  interaction: {
    tooltip: {
      render: (event, { title, items }) => `
        <div style="padding: 8px 12px; background: white; border: 1px solid #ddd; border-radius: 4px;">
          <strong>${title}</strong>
          ${items.map(item => `
            <div style="display: flex; justify-content: space-between; gap: 16px; margin-top: 4px;">
              <span style="color: ${item.color}">${item.name}</span>
              <span>${item.value}</span>
            </div>
          `).join('')}
        </div>
      `,
    },
  },
});
```

## Configure Tooltip in the View Container

```javascript
// When multiple Marks are stacked, configure the Tooltip uniformly in the outer view
chart.options({
  type: 'view',
  data: [...],
  interaction: { tooltip: { shared: true } },  // Shared Tooltip (multiple Marks merged display)
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'type' },
      tooltip: { items: [{ field: 'value', name: 'Value' }] },
    },
    {
      type: 'point',
      encode: { x: 'month', y: 'value', color: 'type' },
      tooltip: false,    // Point Mark does not trigger Tooltip separately
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Tooltip written inside style
```javascript
// ❌ Incorrect
chart.options({ type: 'interval',  [...], style: { tooltip: { title: 'name' } } });

// ✅ Correct: Tooltip is a field at the same level as encode/style
chart.options({ type: 'interval',  [...], tooltip: { title: 'name' } });
```

### Error 2: Confusion between interaction.tooltip and mark.tooltip Responsibilities
```javascript
// ❌ Incorrect: Content configuration written in interaction
chart.options({
  interaction: { tooltip: { items: [{ field: 'value' }] } },  // Invalid!
});

// ✅ Correct: Content configuration in the tooltip field of mark; behavior configuration in interaction.tooltip
chart.options({
  type: 'interval',
  tooltip: { items: [{ field: 'value', name: 'Value' }] },  // Content
  interaction: { tooltip: { shared: true } },              // Behavior
});
```