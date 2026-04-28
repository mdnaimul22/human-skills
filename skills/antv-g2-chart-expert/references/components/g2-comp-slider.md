---
id: "g2-comp-slider"
title: "G2 Slider / Thumbnail Axis"
description: |
  The slider (thumbnail axis) allows users to adjust the data display range of a chart by dragging the control handles at both ends.
  Commonly used for time range filtering in time series charts, it can be configured on the x-axis (sliderX) or y-axis (sliderY).
  Supports setting initial values (values) and linked interactions (sliderFilter interaction).

library: "g2"
version: "5.x"
category: "components"
tags:
  - "slider"
  - "thumbnail axis"
  - "sliderX"
  - "sliderY"
  - "time filtering"
  - "range selection"
  - "component"

related:
  - "g2-comp-scrollbar"
  - "g2-interaction-slider-filter"
  - "g2-scale-time"

use_cases:
  - "Time range interactive filtering in time series charts"
  - "Dynamic adjustment and viewing of numerical ranges"
  - "Partial data exploration in large datasets"

anti_patterns:
  - "Thumbnail axes are rarely used with categorical axes"
  - "Thumbnail axes are not needed for small datasets"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/slider"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = Array.from({ length: 200 }, (_, i) => ({
  date: new Date(2020, 0, i + 1).toISOString().split('T')[0],
  value: Math.sin(i / 30) * 50 + 100 + Math.random() * 20,
}));

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: true,   // Enable X-axis slider (default shows full range)
  },
});

chart.render();
```

---

## Incremental Configuration Modification

If you already have a chart and only want to modify a specific configuration item (such as the handle color), you can use the following methods:

```javascript
// Method 1: Re-call options, passing only the configuration to be modified
chart.options({
  slider: {
    x: {
      handleIconFill: 'red',  // Only modify the handle icon fill color
    },
  },
});
chart.render();  // Re-rendering is required

// Method 2: Modify after complete configuration, before render
const options = {
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: { x: true },
};
chart.options(options);

// Subsequent modification
options.slider = { x: { handleIconFill: 'red' } };
chart.options(options);
chart.render();
```

---

## Complete Configuration Options Reference

### Basic Configuration

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `values` | Initial selection range, within the interval 0~1 | `[number, number]` | `[0, 1]` |
| `slidable` | Whether to allow dragging selection and handles | `boolean` | `true` |
| `brushable` | Whether to enable brushing | `boolean` | `true` |
| `labelFormatter` | Handle label formatting during dragging | `(value) => string` | - |
| `showHandle` | Whether to display drag handles | `boolean` | `true` |
| `showLabel` | Whether to display drag handle text | `boolean` | `true` |
| `showLabelOnInteraction` | Display handle text only when adjusting handles or brushing | `boolean` | `false` |
| `autoFitLabel` | Whether to automatically adjust drag handle text position | `boolean` | `true` |
| `padding` | Inner padding of the thumbnail axis | `number \| number[]` | - |

### Selection Style (selection)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `selectionFill` | Selection fill color | `string` | `#1783FF` |
| `selectionFillOpacity` | Selection fill opacity | `number` | `0.15` |
| `selectionStroke` | Selection stroke color | `string` | - |
| `selectionStrokeOpacity` | Selection stroke opacity | `number` | - |
| `selectionLineWidth` | Selection stroke width | `number` | - |
| `selectionLineDash` | Selection stroke dash configuration | `[number, number]` | - |
| `selectionOpacity` | Overall selection opacity | `number` | - |
| `selectionShadowColor` | Selection shadow color | `string` | - |
| `selectionShadowBlur` | Selection shadow blur factor | `number` | - |
| `selectionShadowOffsetX` | Shadow horizontal offset | `number` | - |
| `selectionShadowOffsetY` | Shadow vertical offset | `number` | - |
| `selectionCursor` | Selection cursor style | `string` | `default` |

### Track Style (track)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `trackLength` | Track length | `number` | - |
| `trackSize` | Track size | `number` | `16` |
| `trackFill` | Track fill color | `string` | `#416180` |
| `trackFillOpacity` | Track fill opacity | `number` | `1` |
| `trackStroke` | Track stroke | `string` | - |
| `trackStrokeOpacity` | Track stroke opacity | `number` | - |
| `trackLineWidth` | Track stroke width | `number` | - |
| `trackLineDash` | Track stroke dash configuration | `[number, number]` | - |
| `trackOpacity` | Overall track opacity | `number` | - |
| `trackShadowColor` | Track shadow color | `string` | - |
| `trackShadowBlur` | Track shadow blur factor | `number` | - |
| `trackShadowOffsetX` | Shadow horizontal offset | `number` | - |
| `trackShadowOffsetY` | Shadow vertical offset | `number` | - |
| `trackCursor` | Track cursor style | `string` | `default` |

### Handle Icon Style (handleIcon)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `handleIconSize` | Handle icon size | `number` | `10` |
| `handleIconRadius` | Handle icon border radius | `number` | `2` |
| `handleIconShape` | Handle icon shape | `string \| (type) => DisplayObject` | - |
| `handleIconFill` | **Handle icon fill color** | `string` | `#f7f7f7` |
| `handleIconFillOpacity` | Handle icon fill opacity | `number` | `1` |
| `handleIconStroke` | Handle icon stroke color | `string` | `#1D2129` |
| `handleIconStrokeOpacity` | Handle icon stroke opacity | `number` | `0.25` |
| `handleIconLineWidth` | Handle icon stroke width | `number` | `1` |
| `handleIconLineDash` | Handle icon stroke dash configuration | `[number, number]` | - |
| `handleIconOpacity` | Overall handle icon opacity | `number` | - |
| `handleIconShadowColor` | Handle icon shadow color | `string` | - |
| `handleIconShadowBlur` | Handle icon shadow blur factor | `number` | - |
| `handleIconShadowOffsetX` | Shadow horizontal offset | `number` | - |
| `handleIconShadowOffsetY` | Shadow vertical offset | `number` | - |
| `handleIconCursor` | Handle icon cursor style | `string` | `default` |

### Handle Label Style (handleLabel)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `handleLabelFontSize` | Label font size | `number` | `12` |
| `handleLabelFontFamily` | Label font family | `string` | - |
| `handleLabelFontWeight` | Label font weight | `number` | `normal` |
| `handleLabelLineHeight` | Label line height | `number` | - |
| `handleLabelTextAlign` | Label horizontal alignment | `string` | `start` |
| `handleLabelTextBaseline` | Label vertical baseline | `string` | `bottom` |
| `handleLabelFill` | Label fill color | `string` | `#1D2129` |
| `handleLabelFillOpacity` | Label fill opacity | `number` | `0.45` |
| `handleLabelStroke` | Label stroke color | `string` | - |
| `handleLabelStrokeOpacity` | Label stroke opacity | `number` | - |
| `handleLabelLineWidth` | Label stroke width | `number` | - |
| `handleLabelLineDash` | Label stroke dash configuration | `[number, number]` | - |
| `handleLabelOpacity` | Overall label opacity | `number` | - |
| `handleLabelShadowColor` | Label shadow color | `string` | - |
| `handleLabelShadowBlur` | Label shadow blur | `number` | - |
| `handleLabelShadowOffsetX` | Shadow horizontal offset | `number` | - |
| `handleLabelShadowOffsetY` | Shadow vertical offset | `number` | - |
| `handleLabelCursor` | Label cursor style | `string` | `default` |
| `handleLabelDx` | Label horizontal offset | `number` | `0` |
| `handleLabelDy` | Label vertical offset | `number` | `0` |

### Sparkline Style

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `sparklineType` | Sparkline type | `'line' \| 'column'` | `'line'` |
| `sparklineIsStack` | Whether to stack | `boolean` | `false` |
| `sparklineRange` | Value range | `[number, number]` | - |
| `sparklineColor` | Color | `string \| string[]` | - |
| `sparklineSmooth` | Smooth curve | `boolean` | `false` |
| `sparklineLineStroke` | Line color | `string` | - |
| `sparklineLineStrokeOpacity` | Line opacity | `number` | - |
| `sparklineLineLineDash` | Line dash configuration | `[number, number]` | - |
| `sparklineAreaFill` | Fill area color | `string` | - |
| `sparklineAreaFillOpacity` | Fill area opacity | `number` | - |
| `sparklineColumnFill` | Column color | `string` | - |
| `sparklineColumnFillOpacity` | Column opacity | `number` | - |
| `sparklineIsGroup` | Whether to display in groups | `boolean` | `false` |
| `sparklineSpacing` | Group column spacing | `number` | `0` |

---

## Common Configuration Examples

### Set Initial Display Range

```javascript
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value' },
  slider: {
    x: {
      values: [0.5, 1.0],  // Display the last 50% of the data initially
    },
  },
});
```

### Change the Handle Icon to Red

```javascript
chart.options({
  slider: {
    x: {
      handleIconFill: 'red',
      handleIconStroke: 'darkred',
      handleIconSize: 12,
    },
  },
});
```

### Customizing Handle Icon Shape

```javascript
import { Circle } from '@antv/g';

chart.options({
  slider: {
    x: {
      handleIconShape: (type) => {
        // type is either 'start' or 'end', representing the left or right handle respectively
        return new Circle({
          style: {
            r: 8,
            fill: type === 'start' ? '#FF6B9D' : '#00D9FF',
            stroke: '#fff',
            lineWidth: 2,
          },
        });
      },
      handleIconSize: 16,
    },
  },
});
```

### Complete Style Configuration

```javascript
chart.options({
  slider: {
    x: {
      values: [0.3, 0.7],
      // Selection area style
      selectionFill: '#1890ff',
      selectionFillOpacity: 0.2,
      // Track style
      trackFill: '#f0f0f0',
      trackSize: 20,
      // Handle icon style
      handleIconFill: '#fff',
      handleIconStroke: '#1890ff',
      handleIconSize: 14,
      handleIconRadius: 4,
      // Handle label style
      handleLabelFill: '#333',
      handleLabelFontSize: 12,
    },
  },
});
```

---

## Common Errors and Fixes

### Error 1: values Exceed the [0, 1] Range

```javascript
// ❌ values must be within the [0, 1] range
chart.options({ slider: { x: { values: [50, 100] } } });

// ✅ values represent data proportions (0~1)
chart.options({ slider: { x: { values: [0.5, 1.0] } } });
```

### Error 2: Incorrect Style Property Name

```javascript
// ❌ Incorrect property name
slider: { x: { handleFill: 'red' } }  // Does not exist

// ✅ Correct property name (with prefix)
slider: { x: { handleIconFill: 'red' } }  // Correct
```

### Error 3: Confusion with scrollbar

```javascript
// slider: Handles at both ends can be dragged separately, window size is variable
slider: { x: { values: [0.3, 0.7] } }

// scrollbar: Fixed window size, can only be slid as a whole
scrollbar: { x: { ratio: 0.4 } }
```