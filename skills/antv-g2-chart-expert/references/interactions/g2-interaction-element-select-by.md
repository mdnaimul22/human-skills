---
id: "g2-interaction-element-select-by"
title: "G2 Group Selection (elementSelectByColor / elementSelectByX)"
description: |
  elementSelectByColor: When clicking on an element, select all elements with the same color (color encode value).
  Commonly used in multi-series line charts to select an entire line by clicking on a single point.
  elementSelectByX: When clicking on an element, select all elements with the same X value.
  Commonly used in grouped bar charts to select all bars under the same X category.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "elementSelectByColor"
  - "elementSelectByX"
  - "group selection"
  - "batch selection"
  - "interaction"

related:
  - "g2-interaction-element-highlight-by"
  - "g2-interaction-element-select"
  - "g2-interaction-legend-filter"

use_cases:
  - "Multi-series line chart: Click a data point to select the entire line"
  - "Grouped bar chart: Click a bar to select all bars under the same X category"
  - "Scatter plot batch selection by color"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"

## elementSelectByColor (Select by Color)

```javascript
import { Chart } from '@antv/g2';

const data = [
  { month: 'Jan', city: 'Beijing', value: 5 },
  { month: 'Feb', city: 'Beijing', value: 8 },
  { month: 'Jan', city: 'Shanghai', value: 12 },
  { month: 'Feb', city: 'Shanghai', value: 15 },
];

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'value', color: 'city' },
  interaction: {
    elementSelectByColor: true,  // Click any data point to select all points of the same color
  },
});

chart.render();
```

## elementSelectByX (Select by X Group)

```javascript
// Grouped bar chart: Click on a bar to select all grouped bars under the same X value
chart.options({
  type: 'interval',
  data: groupedData,
  encode: { x: 'month', y: 'value', color: 'city' },
  transform: [{ type: 'dodgeX' }],
  interaction: {
    elementSelectByX: true,  // Click on a bar to select all grouped bars in the same month
  },
});
```

## Multiple Interaction Combinations

```javascript
// Combine highlight and select: hover to highlight the same color series, click to select
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value', color: 'series' },
  interaction: {
    elementHighlightByColor: true,  // Hover: highlight the same color series
    elementSelectByColor: true,     // Click: select the same color series
  },
});
```

## Get Selected Event

```javascript
chart.on('element:select', (event) => {
  const { data } = event.detail;
  console.log('Selected data:', data.datum);
});

chart.on('element:unselect', (event) => {
  console.log('Unselected');
});
```

## Common Errors and Fixes

### Error: elementSelectByColor is invalid without color encoding
```javascript
// ❌ No color encoding, cannot select by color grouping
chart.options({
  type: 'line',
  encode: { x: 'month', y: 'value' },   // ❌ No color
  interaction: { elementSelectByColor: true },  // Invalid
});

// ✅ Requires color encoding
chart.options({
  type: 'line',
  encode: { x: 'month', y: 'value', color: 'city' },  // ✅
  interaction: { elementSelectByColor: true },
});
```

### Error: Confusion between elementSelectByColor and elementSelect
```javascript
// elementSelect: Selects only the single element that is clicked
chart.options({ interaction: { elementSelect: true } });

// elementSelectByColor: Selects all elements with the same color value (batch selection)
chart.options({ interaction: { elementSelectByColor: true } });
```