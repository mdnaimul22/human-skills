---
id: "g2-interaction-element-select"
title: "G2 Element Select Interaction (elementSelect)"
description: |
  G2 v5 element select interaction is enabled via interaction: [{ type: 'elementSelect' }].
  Clicking on a graphical element toggles its selected state, supporting custom styles for selected/active states.
  It can be combined with elementSelectByX/elementSelectByColor to achieve batch selection.
library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "select"
  - "elementSelect"
  - "interaction"
  - "state"
  - "click"
  - "spec"

related:
  - "g2-interaction-element-highlight"
  - "g2-mark-interval-basic"
  - "g2-interaction-tooltip"

use_cases:
  - "Click on a bar to highlight it, while other bars turn gray"
  - "Click on a legend item to filter the chart"
  - "Link with an external data panel to display selected details"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction"
---

## Basic Usage (Bar Chart Click Selection)

Click on a bar to toggle its selected state, and click again to deselect:

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
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  interaction: [
    { type: 'elementSelect' },   // Click element to toggle selected state
  ],
});

chart.render();
```

## elementSelectByX (Batch Selection by X Value)

Suitable for grouped bar charts or stacked charts, selects all elements at the same x position when any group of elements is clicked:

```javascript
chart.options({
  type: 'interval',
  data: [
    { month: 'Jan', type: 'A', value: 120 },
    { month: 'Jan', type: 'B', value: 80 },
    { month: 'Feb', type: 'A', value: 160 },
    { month: 'Feb', type: 'B', value: 95 },
    { month: 'Mar', type: 'A', value: 140 },
    { month: 'Mar', type: 'B', value: 110 },
  ],
  encode: { x: 'month', y: 'value', color: 'type' },
  transform: [{ type: 'dodgeX' }],
  interaction: [
    { type: 'elementSelectByX' },   // Click any bar to select all bars at the same x position
  ],
});
```

## Customizing Selected State Styles

Use `state.selected` to specify the visual style when an element is selected. The style of unselected elements will be correspondingly reduced:

```javascript
chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
    { genre: 'Shooter',  sold: 350 },
    { genre: 'Other',    sold: 150 },
  ],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  state: {
    selected: {
      fill: '#1890ff',          // Fill color when selected
      fillOpacity: 1,           // Opacity when selected
      stroke: '#003a8c',        // Stroke color when selected
      lineWidth: 2,             // Stroke width when selected
    },
    unselected: {
      fillOpacity: 0.3,         // Semi-transparent for unselected elements
    },
  },
  interaction: [
    { type: 'elementSelect' },
  ],
});
```

## Combined Use of Highlight + Select

Mouse hover triggers highlight, and click triggers selection. Both can be enabled simultaneously:

```javascript
chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
    { genre: 'Shooter',  sold: 350 },
    { genre: 'Other',    sold: 150 },
  ],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  state: {
    active: {
      fill: '#69c0ff',        // Hover highlight color (active state)
      fillOpacity: 0.9,
    },
    selected: {
      fill: '#1890ff',        // Click selection color (selected state)
      fillOpacity: 1,
      stroke: '#003a8c',
      lineWidth: 2,
    },
    unselected: {
      fillOpacity: 0.3,
    },
  },
  interaction: [
    { type: 'elementHighlight' },   // Hover highlight (active state)
    { type: 'elementSelect' },      // Click selection (selected state)
    { type: 'tooltip' },
  ],
});
```

## Listening to Selection Events

```javascript
// Listen to selection and unselection events
chart.on('element:select', (event) => {
  const datum = event.data?.data;
  console.log('Selected element data:', datum);
  // Can interact with external panels, update states, etc., here
});

chart.on('element:unselect', (event) => {
  console.log('Unselected');
});
```

## Common Errors and Fixes

### Error: `interaction` is written as an object instead of an array

```javascript
// ❌ Error: `interaction` must be an array
chart.options({
  interaction: { type: 'elementSelect' },
});

// ✅ Correct
chart.options({
  interaction: [{ type: 'elementSelect' }],
});
```

### Error: Using a Non-existent Interaction Name

```javascript
// ❌ Error: 'elementClick' interaction type does not exist in G2
chart.options({
  interaction: [{ type: 'elementClick' }],
});

// ✅ Correct Name
chart.options({
  interaction: [{ type: 'elementSelect' }],         // Select a single element
  // or
  // interaction: [{ type: 'elementSelectByX' }],   // Batch select by x value
  // interaction: [{ type: 'elementSelectByColor' }], // Batch select by color
});
```

### Error: Selected Style Not Applied (Incorrect State Position)

```javascript
// ❌ Incorrect: state should not be nested inside style
chart.options({
  style: {
    state: { selected: { fill: '#1890ff' } },
  },
});

// ✅ Correct: state should be at the top level of Mark configuration, alongside encode and style
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  state: {
    selected: { fill: '#1890ff', fillOpacity: 1 },
  },
  interaction: [{ type: 'elementSelect' }],
});
```

### Error: Conflict caused by using both elementSelect and elementSelectByX

```javascript
// ❌ Unpredictable behavior when both are enabled, click triggers double selection logic
chart.options({
  interaction: [
    { type: 'elementSelect' },
    { type: 'elementSelectByX' },
  ],
});

// ✅ Choose one based on requirements
// - elementSelect: Select only the clicked single element
// - elementSelectByX: Select all elements with the same x value (suitable for grouped/stacked charts)
// - elementSelectByColor: Select all elements with the same color (series)
chart.options({
  interaction: [{ type: 'elementSelectByX' }],
});
```