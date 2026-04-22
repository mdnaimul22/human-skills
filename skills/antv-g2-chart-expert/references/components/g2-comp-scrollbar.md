---
id: "g2-comp-scrollbar"
title: "G2 Scrollbar"
description: |
  The scrollbar component allows users to scroll and view data that exceeds the canvas area, making it suitable for browsing large amounts of data entries.
  The scrollbar can be configured in the x-axis (scrollbarX) or y-axis (scrollbarY) direction.
  Unlike the slider, the scrollbar provides fixed-ratio window scrolling, while the slider supports adjustable window sizes.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "scrollbar"
  - "scroll bar"
  - "data browsing"
  - "scrollbarX"
  - "scrollbarY"
  - "component"

related:
  - "g2-comp-slider"
  - "g2-interaction-scrollbar-filter"

use_cases:
  - "Horizontal scrolling for too many categories (> 20 categories)"
  - "Scrolling through time series data that is too long"
  - "Fixed visible window size, scroll to view all data"

anti_patterns:
  - "No scrollbar is needed when there is not much data"
  - "Use slider when adjusting window size is required"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/scrollbar"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

// 50 categorical items
const data = Array.from({ length: 50 }, (_, i) => ({
  category: `Category${i + 1}`,
  value: Math.random() * 100,
}));

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  scrollbar: {
    x: true,   // Enable X-axis scrollbar
  },
  legend: false,
});

chart.render();
```

---

## Incremental Configuration Modification

If you already have a chart and only want to modify a specific configuration item (such as the slider color), you can use the following methods:

```javascript
// Method 1: Re-call options, only pass the configuration that needs to be modified
chart.options({
  scrollbar: {
    x: {
      thumbFill: 'red',  // Only modify the slider fill color
    },
  },
});
chart.render();  // Need to re-render

// Method 2: Modify after complete configuration
const options = {
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  scrollbar: { x: true },
};
chart.options(options);

// Subsequent modifications
options.scrollbar = { x: { thumbFill: 'red' } };
chart.options(options);
chart.render();
```

---

## Complete Configuration Options Reference

### Basic Configuration

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `ratio` | The proportion of the scrollbar, representing the ratio of the data displayed on a single page to the total data volume | `number` | `0.5` |
| `value` | The starting position of the scrollbar (0~1), default horizontal is 0, default vertical is 1 | `number` | - |
| `slidable` | Whether the scrollbar can be dragged | `boolean` | `true` |
| `position` | The position of the scrollbar relative to the chart | `string` | `'bottom'` |
| `isRound` | Whether the scrollbar style has rounded corners | `boolean` | `true` |

### Slider Style (thumb)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `thumbFill` | **Slider Fill Color** | `string` | `#000` |
| `thumbFillOpacity` | Slider Fill Opacity | `number` | `0.15` |
| `thumbStroke` | Slider Stroke Color | `string` | - |
| `thumbLineWidth` | Slider Stroke Width | `number` | - |
| `thumbStrokeOpacity` | Slider Stroke Opacity | `number` | - |
| `thumbLineDash` | Slider Dashed Line Configuration | `[number, number]` | - |
| `thumbOpacity` | Overall Slider Opacity | `number` | - |
| `thumbShadowColor` | Slider Shadow Color | `string` | - |
| `thumbShadowBlur` | Slider Shadow Blur Factor | `number` | - |
| `thumbShadowOffsetX` | Shadow Horizontal Offset | `number` | - |
| `thumbShadowOffsetY` | Shadow Vertical Offset | `number` | - |
| `thumbCursor` | Slider Cursor Style | `string` | `default` |

### Track Style (track)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `trackSize` | Track width | `number` | `10` |
| `trackLength` | Track length | `number` | - |
| `trackFill` | Track fill color | `string` | - |
| `trackFillOpacity` | Track fill opacity | `number` | `0` |
| `trackStroke` | Track stroke color | `string` | - |
| `trackLineWidth` | Track stroke width | `number` | - |
| `trackStrokeOpacity` | Track stroke opacity | `number` | - |
| `trackLineDash` | Track dashed line configuration | `[number, number]` | - |
| `trackOpacity` | Overall track opacity | `number` | - |
| `trackShadowColor` | Track shadow color | `string` | - |
| `trackShadowBlur` | Track shadow blur factor | `number` | - |
| `trackShadowOffsetX` | Shadow horizontal offset | `number` | - |
| `trackShadowOffsetY` | Shadow vertical offset | `number` | - |
| `trackCursor` | Track cursor style | `string` | `default` |

---

## Common Configuration Examples

### Configure Scrollbar Style and Initial Position

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'date', y: 'value' },
  scrollbar: {
    x: {
      ratio: 0.2,      // Ratio of the visible window to the entire data
      value: 0,        // Initial scroll position (0=leftmost, 1=rightmost)
      // Track style
      trackSize: 14,
      trackFill: '#f0f0f0',
      trackFillOpacity: 1,
      // Thumb style
      thumbFill: '#5B8FF9',
      thumbFillOpacity: 0.5,
    },
  },
});
```

### Change the Slider Color to Red

```javascript
chart.options({
  scrollbar: {
    x: {
      thumbFill: 'red',
      thumbFillOpacity: 0.3,
      thumbStroke: 'darkred',
      thumbLineWidth: 1,
    },
  },
});
```

### Y-axis Scrollbar

```javascript
chart.options({
  type: 'interval',
  data: manyRowsData,
  encode: { x: 'value', y: 'category' },
  coordinate: { transform: [{ type: 'transpose' }] },
  scrollbar: {
    y: {
      ratio: 0.3,   // Display only 30% of the data at a time
      value: 0.5,   // Start from the middle
    },
  },
});
```

### Configure X and Y Scrollbars Simultaneously

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'letter', y: 'frequency' },
  scrollbar: {
    x: {
      ratio: 0.2,
      trackSize: 14,
      trackFill: '#000',
      trackFillOpacity: 1,
    },
    y: {
      ratio: 0.5,
      trackSize: 12,
      value: 0.1,
      trackFill: '#000',
      trackFillOpacity: 1,
    },
  },
});
```

---

## Common Errors and Fixes

### Error 1: Incorrect Style Property Name

```javascript
// ❌ Incorrect property name
scrollbar: { x: { fill: 'red' } }  // Does not exist

// ✅ Correct property name (with prefix)
scrollbar: { x: { thumbFill: 'red' } }  // Modify thumb color
scrollbar: { x: { trackFill: '#f0f0f0' } }  // Modify track color
```

### Error 2: Confusion with Slider

```javascript
// scrollbar: Fixed window size, can only be moved, cannot be scaled
scrollbar: { x: { ratio: 0.2 } }  // Always displays 20% of the data

// slider: Can drag both ends to adjust the display range
slider: { x: { values: [0, 0.2] } }  // Can be dragged to adjust to any range
```

### Error 3: Using Scrollbar for Small Datasets

```javascript
// ❌ Only 10 categories, no need for scrollbar
chart.options({ scrollbar: { x: true } });  // Redundant

// ✅ Typically consider when > 20 categories or longer time-series data
// For small datasets, recommend directly adjusting chart.width or axis label rotation
```

### Error 4: scrollbar written in style

```javascript
// ❌ Incorrect: Style properties are directly written in the configuration options, not in the style object
scrollbar: { x: { style: { thumbFill: 'red' } } }

// ✅ Correct: Style properties are directly written in the configuration options
scrollbar: { x: { thumbFill: 'red' } }
```