---
id: "g2-comp-title"
title: "G2 Chart Title Configuration (title)"
description: |
  G2 v5 adds titles and subtitles to charts through the top-level title field.
  It supports customizing title text, font style, alignment, and spacing from the plotting area.
  The title field can be configured in the Chart constructor or options.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "title"
  - "chart title"
  - "subtitle"
  - "title style"

related:
  - "g2-core-chart-init"
  - "g2-comp-axis-config"
  - "g2-comp-legend-config"

use_cases:
  - "Add main title and subtitle to a chart"
  - "Customize title font, color, and size"
  - "Control title alignment (left/center/right)"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/title"
---

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },
  title: {
    title: 'Monthly Sales',        // Main Title
    subtitle: 'Unit: Ten Thousand Yuan', // Subtitle
  },
});

chart.render();
```

## Complete Configuration Options

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },
  title: {
    // ── Text Content ────────────────────────────
    title: 'Monthly Sales Trend Analysis',        // Main title text
    subtitle: 'Data Source: 2024 Annual Report',  // Subtitle text (optional)

    // ── Alignment ─────────────────────────────────
    align: 'left',    // 'left' (default) | 'center' | 'right'

    // ── Spacing ─────────────────────────────────
    spacing: 4,       // Spacing between main title and subtitle, default 2

    // ── Main Title Style ────────────────────────────
    titleFontSize: 16,
    titleFontWeight: 'bold',
    titleFill: '#1d1d1d',
    titleSpacing: 8,     // Spacing between title and chart content area

    // ── Subtitle Style ────────────────────────────
    subtitleFontSize: 12,
    subtitleFill: '#8c8c8c',
    subtitleFontWeight: 'normal',
  },
});
```

## Centered Title

```javascript
chart.options({
  title: {
    title: 'Quarterly Comparison Report',
    subtitle: 'Q1-Q4 Quarterly Sales Data',
    align: 'center',          // Center alignment
    titleFontSize: 18,
    titleFontWeight: 600,
    subtitleFontSize: 13,
    subtitleFill: '#999',
  },
});
```

## Configuration in the Constructor

```javascript
// title can also be configured in the options of the Chart constructor
const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
  title: {
    title: 'Sales Trend',
    align: 'center',
  },
});
```

## Common Errors and Fixes

### Error: title is written as a string instead of an object
```javascript
// ❌ Error: The title field must be a configuration object and cannot be a direct string
chart.options({
  title: 'Monthly Sales',   // ❌ String not supported
});

// ✅ Correct: The title field is an object, with the main title text in title.title
chart.options({
  title: {
    title: 'Monthly Sales',   // ✅ Correct usage
  },
});
```

### Error: Confusing Chart Title with Axis Title
```javascript
// ❌ Incorrect: Placing the overall chart title within the axis
chart.options({
  axis: { x: { title: 'Monthly Sales' } },  // ❌ This is the X-axis title, not the chart title
});

// ✅ Correct: Use the top-level title field for the chart title
chart.options({
  title: { title: 'Monthly Sales' },     // ✅ Chart title
  axis: { x: { title: 'Month' } },       // ✅ X-axis title
});
```