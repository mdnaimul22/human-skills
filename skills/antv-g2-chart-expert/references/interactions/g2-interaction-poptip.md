---
id: "g2-interaction-poptip"
title: "G2 Text Overflow Tooltip (poptip)"
description: |
  The poptip interaction automatically displays a bubble tooltip with the full text when the text of a text element is truncated (overflows the container) and the mouse hovers over it.
  It is suitable for scenarios such as axis labels being too long and truncated, or annotation text not fully displayed, without the need for custom tooltips.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "poptip"
  - "text tooltip"
  - "overflow"
  - "bubble"
  - "truncation"
  - "interaction"

related:
  - "g2-comp-tooltip-config"
  - "g2-comp-axis-config"

use_cases:
  - "Full text tooltip for truncated X-axis category labels"
  - "Hover tooltip for long text annotations within charts"
  - "Automatic handling of text overflow without manual tooltip configuration"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/poptip"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// Data with long axis labels
const data = [
  { category: 'Artificial Intelligence and Machine Learning Algorithm Research', value: 85 },
  { category: 'Cloud Computing Infrastructure Services', value: 72 },
  { category: 'Big Data Analytics and Visualization Platform', value: 68 },
  { category: 'Blockchain and Decentralized Applications', value: 45 },
  { category: 'Internet of Things Device Management System', value: 60 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  axis: {
    x: {
      labelFormatter: (v) => v.length > 6 ? v.slice(0, 6) + '...' : v,  // Truncated display
    },
  },
  interaction: {
    poptip: true,   // When enabled, automatically pops up the full text when hovering over truncated labels
  },
});

chart.render();
```

## Customizing poptip Style

```javascript
chart.options({
  interaction: {
    poptip: {
      offsetX: 8,   // Horizontal offset of the bubble (px), default 8
      offsetY: 8,   // Vertical offset of the bubble (px), default 8
      // Bubble style (CSS properties)
      tip: {
        backgroundColor: 'rgba(0,0,0,0.75)',
        color: '#fff',
        fontSize: '12px',
        padding: '4px 8px',
        borderRadius: '4px',
      },
    },
  },
});
```

## Common Errors and Fixes

### Error: PopTip does not appear when text is not overflowing—this is the correct behavior
```javascript
// ℹ️  PopTip is triggered only when the text is truly overflowing (truncated), non-overflowing text will not pop up
// If all labels are fully displayed, no tooltip will appear on hover
// This is a design behavior, not a bug

// If you need to display a tooltip for all elements, use tooltip instead
chart.options({
  tooltip: {
    items: [{ channel: 'x' }],   // Display full x-axis values
  },
});
```