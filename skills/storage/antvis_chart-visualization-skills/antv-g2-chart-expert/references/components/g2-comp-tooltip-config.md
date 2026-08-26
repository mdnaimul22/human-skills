---
id: "g2-comp-tooltip-config"
title: "G2 Tooltip Configuration and Customization"
description: |
  G2 v5 tooltip is enabled via top-level tooltip configuration or interaction: [{ type: 'tooltip' }],
  supporting custom content (items field filtering, render function for complete HTML customization),
  groupKey controls merging rules, and crosshairs display crosshairs.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "tooltip"
  - "tooltip box"
  - "customization"
  - "interaction"
  - "spec"

related:
  - "g2-interaction-tooltip"
  - "g2-mark-line-basic"
  - "g2-mark-interval-basic"

use_cases:
  - "Customize tooltip display fields and format"
  - "Shared tooltip across multiple series (grouped tooltip)"
  - "Completely customize tooltip HTML template"
  - "Display crosshairs for positioning assistance"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/tooltip"
---

## Minimum Viable Example (Enable Default Tooltip)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 600,
  height: 400,
});

const data = [
  { month: 'January', value: 120, type: 'Sales' },
  { month: 'February', value: 180, type: 'Sales' },
  { month: 'March', value: 150, type: 'Sales' },
];

chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  // Tooltip is enabled by default, this configuration can be customized
  tooltip: {
    title: (d) => `${d.month} Data`,   // Custom title
    items: [
      { channel: 'y', name: 'Sales', valueFormatter: (v) => `¥${v}` },
    ],
  },
});

chart.render();
```

## Multi-field tooltip (Displaying multiple information items)

```javascript
const data = [
  { date: '2024-01', revenue: 1200, cost: 800, profit: 400 },
  { date: '2024-02', revenue: 1800, cost: 950, profit: 850 },
  { date: '2024-03', revenue: 1500, cost: 1000, profit: 500 },
];

chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'revenue' },
  tooltip: {
    title: 'date',
    // Each item in items corresponds to one line of displayed content
    items: [
      { field: 'revenue', name: 'Revenue', valueFormatter: (v) => `¥${v}` },
      { field: 'cost', name: 'Cost', valueFormatter: (v) => `¥${v}` },
      { field: 'profit', name: 'Profit', valueFormatter: (v) => `¥${v}` },
    ],
  },
});
```

## Fully Customized HTML (render Function)

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  tooltip: {
    render: (event, { title, items }) => {
      // Return an HTML string, fully customizing the tooltip content
      return `
        <div style="padding: 8px 12px; background: #fff; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
          <div style="font-weight: bold; margin-bottom: 6px;">${title}</div>
          ${items.map(({ name, value, color }) => `
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span style="width: 8px; height: 8px; background: ${color}; border-radius: 50%; display: inline-block;"></span>
              <span>${name}：</span>
              <span style="font-weight: 500;">${value}</span>
            </div>
          `).join('')}
        </div>
      `;
    },
  },
});
```

## Multiple Series Shared Tooltip (groupKey)

```javascript
// Multiple line chart, displaying values of all series simultaneously on mouse hover
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value', color: 'type' },
      tooltip: {
        // groupKey: The field by which multiple series tooltips are merged
        // By default, tooltips are merged by x values, displaying points of all series at the same x value in one tooltip
        title: 'month',
      },
    },
  ],
  interaction: [{ type: 'tooltip', shared: true }],   // shared: true enables shared tooltip
});
```

## Complete Configuration Options

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },

  tooltip: {
    // Title
    title: 'month',               // Field name or function (d) => string

    // Display items
    items: [
      {
        field: 'value',           // Data field name
        channel: 'y',             // Or use channel name ('x' | 'y' | 'color', etc.)
        name: 'Sales',            // Display name (overrides default)
        color: '#1890ff',         // Color block
        // valueFormatter accepts:
        //   function (value) => string   ← Required for concatenating units
        //   d3-format string '.2f'       ← Formats only the number itself, does not support appending text
        valueFormatter: (v) => `${v} ten thousand`, // ✅ Function form, can concatenate units
        // valueFormatter: '.2f',             // ✅ d3-format, formats only the number
        // valueFormatter: '.0f meters',      // ❌ Error! Cannot append text after d3-format
      },
    ],

    // Rendering
    render: (event, { title, items }) => `<div>...</div>`,  // Fully custom HTML

    // Trigger method
    // Configured in interaction
  },

  // Tooltip interaction (additional configuration)
  interaction: [
    {
      type: 'tooltip',
      shared: true,       // Multiple Marks share tooltip
      crosshairs: true,   // Display crosshairs
    },
  ],
});
```

## Crosshairs

Crosshairs are configured through the `tooltip` interaction item in `interaction`:

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value' },
  interaction: [
    {
      type: 'tooltip',
      crosshairs: true,           // Display crosshairs (enabled by default)
      crosshairsStroke: '#aaa',   // Crosshair color
      crosshairsLineWidth: 1,     // Crosshair width
      crosshairsLineDash: [4, 4], // Dashed line style
    },
  ],
});
```

## Customize Tooltip Style via CSS

When the customization of the `render` function is insufficient, you can directly override the default styles using CSS:

```javascript
// Method 1: Override in global page CSS
// .g2-tooltip { background: #1a1a1a; color: #fff; border-radius: 8px; }
// .g2-tooltip-title { font-size: 14px; font-weight: bold; }
// .g2-tooltip-list-item-value { color: #fadb14; }

// Method 2: Override locally via the css parameter in interaction
chart.options({
  interaction: [
    {
      type: 'tooltip',
      css: {
        '.g2-tooltip': {
          background: '#1a1a1a',
          color: '#fff',
          borderRadius: '8px',
          padding: '8px 12px',
        },
        '.g2-tooltip-title': {
          fontSize: '14px',
          fontWeight: 'bold',
          marginBottom: '6px',
        },
        '.g2-tooltip-list-item-value': {
          color: '#fadb14',
        },
      },
    },
  ],
});
```

**Built-in CSS Class Names:**
- `.g2-tooltip` — Tooltip container
- `.g2-tooltip-title` — Title
- `.g2-tooltip-list-item` — Individual data item
- `.g2-tooltip-list-item-name-label` — Data item name
- `.g2-tooltip-list-item-value` — Data item value
- `.g2-tooltip-list-item-marker` — Data item color marker

---

## Common Errors and Fixes

### Error 1: Mismatch between `tooltip.items` field name and data

```javascript
// ❌ Error: Data field is 'revenue' but 'items' is written as 'value'
const data = [{ month: 'January', revenue: 1200 }];
chart.options({
  tooltip: {
    items: [{ field: 'value' }],   // ❌ No 'value' field in the data
  },
});

// ✅ Correct: `field` matches the data field name
chart.options({
  tooltip: {
    items: [{ field: 'revenue', name: 'Revenue' }],   // ✅
  },
});
```

### Error 2: Forgot to Return a String in the render Function

```javascript
// ❌ Wrong: render function lacks a return statement
chart.options({
  tooltip: {
    render: (event, { title, items }) => {
      const html = `<div>${title}</div>`;
      // Forgot to return!
    },
  },
});

// ✅ Correct: Must return an HTML string
chart.options({
  tooltip: {
    render: (event, { title, items }) => {
      return `<div>${title}</div>`;   // ✅
    },
  },
});
```

### Error 3: Using d3-format Strings to Concatenate Units in `valueFormatter`

`valueFormatter` supports two formats: a function `(v) => string` or a d3-format string (e.g., `'.2f'`). **d3-format strings only format the number itself and cannot append text units**——formats with spaces like `'.0f 米'` will be treated as invalid format specifiers, causing display anomalies or direct errors.

```javascript
// ❌ Incorrect: Appending text units to d3-format strings
chart.options({
  tooltip: {
    items: [
      { field: 'distance', name: 'Distance', valueFormatter: '.0f 米' },  // ❌ Invalid format, d3-format does not support concatenating text
      { field: 'price',    name: 'Price', valueFormatter: '.2f 元' },     // ❌ Same issue
    ],
  },
});

// ✅ Correct: Use function format when concatenating units is required
chart.options({
  tooltip: {
    items: [
      { field: 'distance', name: 'Distance', valueFormatter: (v) => `${Math.round(v)} 米` },  // ✅ Function format
      { field: 'price',    name: 'Price', valueFormatter: (v) => `¥${v.toFixed(2)}` },        // ✅ Function format
    ],
  },
});

// ✅ Correct: Use d3-format strings only for formatting numbers (no units needed)
chart.options({
  tooltip: {
    items: [
      { field: 'ratio', name: 'Ratio', valueFormatter: '.1%' },  // ✅ Pure d3-format, no text
      { field: 'value', name: 'Value', valueFormatter: ',.0f' }, // ✅ Comma-separated integer
    ],
  },
});
```
### Error 4: Multiple Series Tooltip Without `shared` Configuration

```javascript
// ❌ Issue: Multi-line chart tooltip only displays the line currently hovered over
chart.options({
  type: 'view',
  children: [
    { type: 'line', encode: { x: 'month', y: 'value', color: 'type' } },
  ],
  // Without shared: true, the tooltip only shows the line directly hovered by the mouse
});

// ✅ Correct: Set `shared: true` to display all series
chart.options({
  type: 'view',
  children: [
    { type: 'line', encode: { x: 'month', y: 'value', color: 'type' } },
  ],
  interaction: [{ type: 'tooltip', shared: true }],   // ✅
});
```