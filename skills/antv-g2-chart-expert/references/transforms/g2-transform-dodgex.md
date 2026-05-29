---
id: "g2-transform-dodgex"
title: "G2 DodgeX Group Transform"
description: |
  DodgeX is a Transform in G2 v5 used for grouped displays,
  arranging multiple series elements at the same x-position in a staggered manner horizontally.
  It is the core dependency for grouped bar charts.

library: "g2"
version: "5.x"
category: "transforms"
tags:
  - "dodgeX"
  - "group"
  - "side-by-side"
  - "transform"
  - "grouped bar chart"
  - "spec"

related:
  - "g2-mark-interval-grouped"
  - "g2-transform-stacky"

use_cases:
  - "Creating grouped bar charts (side-by-side display of multiple series)"
  - "Grouped scatter plots"

difficulty: "beginner"
completeness: "partial"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/transform/dodge-x"
---

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [
    {
      type: 'dodgeX',
      padding: 0,          // Spacing between bars within a group (relative to group width, 0-1), default 0
      paddingOuter: 0.1,   // Outer margin between entire groups and adjacent groups
      reverse: false,      // Whether to reverse the group order
    },
  ],
});
```

## Difference from stackY

```javascript
// dodgeX: Each series is displayed side by side, facilitating direct comparison of absolute values
chart.options({ transform: [{ type: 'dodgeX' }] });

// stackY: Each series is stacked, facilitating comparison of totals and proportions
chart.options({ transform: [{ type: 'stackY' }] });
```

## Common Errors and Fixes

### Error: transform written as an object
```javascript
// ❌ Incorrect
chart.options({ transform: { type: 'dodgeX' } });

// ✅ Correct: must be an array
chart.options({ transform: [{ type: 'dodgeX' }] });
```