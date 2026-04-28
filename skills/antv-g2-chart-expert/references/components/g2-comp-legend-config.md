---
id: "g2-comp-legend-config"
title: "G2 Legend Configuration (legend)"
description: |
  Detailed explanation of the legend field configuration in G2 v5 Spec mode,
  covering legend position, layout, title, color legend, filter interaction, and hiding legends.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "legend"
  - "legend"
  - "position"
  - "filter"
  - "color legend"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-interaction-legend-filter"
  - "g2-comp-axis-config"
  - "g2-comp-legend-category"
  - "g2-comp-legend-continuous"

use_cases:
  - "Adjust legend position and layout"
  - "Customize legend title and style"
  - "Hide unnecessary legends"
  - "Configure continuous color legends (color ramps)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/component/legend"
---
## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  legend: {
    color: {               // Corresponds to the legend of the encode.color channel
      position: 'bottom',  // 'top'(default) | 'bottom' | 'left' | 'right'
    },
  },
});

chart.render();
```

---

## Incremental Configuration Modification

If a chart already exists and you only want to modify a specific configuration item (such as the legend position), you can use the following methods:

```javascript
// Method 1: Re-call options, passing only the configuration to be modified
chart.options({
  legend: {
    color: {
      position: 'right',  // Modify only the position
    },
  },
});
chart.render();  // Re-rendering is required

// Method 2: Modify after complete configuration
const options = {
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value', color: 'type' },
  legend: { color: { position: 'top' } },
};
chart.options(options);

// Subsequent modification
options.legend = { color: { position: 'bottom' } };
chart.options(options);
chart.render();
```

---

## Complete Configuration Options Reference

### General Configuration (Categorical Legend & Continuous Legend)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `position` | Legend position | `'top' \| 'right' \| 'left' \| 'bottom'` | `'top'` |
| `orientation` | Legend orientation | `'horizontal' \| 'vertical'` | `'horizontal'` |
| `layout` | Flex layout configuration | `{ justifyContent, alignItems, flexDirection }` | - |
| `size` | Legend container size | `number` | - |
| `length` | Legend container length | `number` | - |
| `crossPadding` | Distance from legend to chart area | `number` | `12` |
| `order` | Layout order | `number` | `1` |
| `title` | Legend title | `string \| string[]` | - |

### Legend Configuration

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `cols` | Number of legend items displayed per row | `number` | - |
| `colPadding` | Horizontal spacing between legend items | `number` | `12` |
| `rowPadding` | Vertical spacing between legend items | `number` | `8` |
| `maxRows` | Maximum number of rows in the legend | `number` | `3` |
| `maxCols` | Maximum number of columns in the legend | `number` | `3` |
| `itemWidth` | Width of each legend item | `number` | - |
| `itemSpan` | Space allocation for icon, label, and value within a legend item | `number \| number[]` | `[1, 1, 1]` |
| `itemSpacing` | Internal spacing within a legend item | `number \| number[]` | `[8, 8, 4]` |
| `focus` | Whether to enable legend focus | `boolean` | `false` |
| `focusMarkerSize` | Size of the focus icon in the legend | `number` | `12` |
| `defaultSelect` | Default selected legend items | `string[]` | - |

### Legend Item Marker Style (itemMarker)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `itemMarker` | Legend item marker | `string \| (datum, index, data) => string` | - |
| `itemMarkerSize` | Marker size | `number` | `8` |
| `itemMarkerFill` | **Marker fill color** | `string` | - |
| `itemMarkerFillOpacity` | Marker fill opacity | `number` | - |
| `itemMarkerStroke` | Marker stroke | `string` | - |
| `itemMarkerStrokeOpacity` | Marker stroke opacity | `number` | - |
| `itemMarkerLineWidth` | Marker stroke width | `number` | - |
| `itemMarkerRadius` | Marker border radius | `number` | - |

### Legend Item Label Style (itemLabel)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `itemLabelFill` | **Label Text Fill Color** | `string` | `#333` |
| `itemLabelFillOpacity` | Label Text Fill Opacity | `number` | - |
| `itemLabelFontSize` | Label Text Size | `number` | `12` |
| `itemLabelFontFamily` | Label Text Font Family | `string` | - |
| `itemLabelFontWeight` | Label Font Weight | `number \| string` | - |
| `itemLabelTextAlign` | Label Horizontal Alignment | `string` | - |
| `itemLabelTextBaseline` | Label Vertical Baseline | `string` | - |
| `itemLabelStroke` | Label Text Stroke | `string` | - |
| `itemLabelLineWidth` | Label Text Stroke Width | `number` | - |
| `itemLabelDx` | Label Horizontal Offset | `number` | - |
| `itemLabelDy` | Label Vertical Offset | `number` | - |

### Legend Item Value Style (itemValue)

An additional "value" column can be displayed on the right side of the legend item (via `formatter` or data field), suitable for displaying auxiliary information such as quantity, percentage, etc.

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `itemValueFill` | Value text fill color | `string` | `#1D2129` |
| `itemValueFillOpacity` | Value text fill opacity | `number` | `0.65` |
| `itemValueFontSize` | Value text font size | `number` | `12` |
| `itemValueFontFamily` | Value text font family | `string` | - |
| `itemValueFontWeight` | Value text font weight | `number \| string` | - |
| `itemValueStroke` | Value text stroke | `string` | - |
| `itemValueLineWidth` | Value text stroke width | `number` | - |

### Legend Item Background Style (itemBackground)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `itemBackgroundFill` | Legend item background fill color | `string` | - |
| `itemBackgroundFillOpacity` | Legend item background fill opacity | `number` | - |
| `itemBackgroundStroke` | Legend item background stroke | `string` | - |
| `itemBackgroundStrokeOpacity` | Legend item background stroke opacity | `number` | - |
| `itemBackgroundLineWidth` | Legend item background stroke width | `number` | - |
| `itemBackgroundRadius` | Legend item background border radius | `number` | - |

### Legend Title Style (title)

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `titleFill` | **Title Fill Color** | `string` | `#666` |
| `titleFillOpacity` | Title Fill Opacity | `number` | - |
| `titleFontSize` | Title Font Size | `number` | `12` |
| `titleFontFamily` | Title Font Family | `string` | - |
| `titleFontWeight` | Title Font Weight | `number \| string` | - |
| `titleStroke` | Title Stroke | `string` | - |
| `titleLineWidth` | Title Stroke Width | `number` | - |
| `titleSpacing` | Spacing Between Title and Legend Items | `number` | - |

### Continuous Legend Configuration

| Property | Description | Type | Default Value |
|------|------|------|--------|
| `color` | Color band colors | `string[]` | - |
| `block` | Whether to display by range | `boolean` | `false` |
| `type` | Continuous legend type | `'size' \| 'color'` | `'color'` |

---

## Common Configuration Examples

### Hide Legend

```javascript
// Hide legend for a specific channel
legend: { color: false }

// Hide all legends (not commonly used)
legend: false
```

### Modify Legend Position and Layout

```javascript
chart.options({
  legend: {
    color: {
      position: 'bottom',
      layout: {
        justifyContent: 'center',  // Horizontally centered
        alignItems: 'center',      // Vertically centered
      },
    },
  },
});
```

### Modify Legend Item Icon Color

```javascript
chart.options({
  legend: {
    color: {
      itemMarkerFill: 'red',       // Icon fill color
      itemMarkerSize: 10,          // Icon size
      itemMarkerStroke: 'darkred', // Icon stroke color
    },
  },
});
```

### Modify Legend Label Color

```javascript
chart.options({
  legend: {
    color: {
      itemLabelFill: '#333',
      itemLabelFontSize: 14,
      itemLabelFontWeight: 'bold',
    },
  },
});
```

### Modify Legend Title Style

```javascript
chart.options({
  legend: {
    color: {
      title: 'Product Type',
      titleFill: '#1D2129',
      titleFontSize: 14,
      titleFontWeight: 'bold',
      titleSpacing: 12,
    },
  },
});
```

### Pie Chart Legend Centered at the Bottom

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
  legend: {
    color: {
      position: 'bottom',
      layout: { justifyContent: 'center' },
    },
  },
});
```

### Continuous Color Legend (Color Ramp)

When the `color` channel is mapped to continuous numerical values, the legend automatically becomes a color ramp.

```javascript
chart.options({
  type: 'cell',
  data,
  encode: { x: 'x', y: 'y', color: 'value' },  // value is a continuous numerical value
  scale: { color: { palette: 'Blues' } },
  legend: {
    color: {
      position: 'right',
      length: 200,
      labelFormatter: (v) => Number(v).toFixed(0),  // Note: v may be a string, so it needs to be converted to a number first
    },
  },
});
```

> **More Continuous Legend Configurations**: [Continuous Legend Detailed Documentation](g2-comp-legend-continuous.md) covers advanced usage such as threshold legends, size channel legends, and custom color ramps.

---

## Common Errors and Fixes

### Error 1: legend Written as an Array

```javascript
// ❌ Incorrect: legend is an object, not an array
chart.options({ legend: [{ color: { position: 'bottom' } }] });

// ✅ Correct
chart.options({ legend: { color: { position: 'bottom' } } });
```

### Error 2: Mismatch between legend.color and encode.color

```javascript
// ❌ Incorrect: encode does not have a color channel, configuring legend.color is invalid
chart.options({
  encode: { x: 'month', y: 'value' },  // No color
  legend: { color: { position: 'bottom' } },
});

// ✅ Correct: legend.color is only effective when encode.color has a mapping
chart.options({
  encode: { x: 'month', y: 'value', color: 'type' },
  legend: { color: { position: 'bottom' } },
});
```

### Error 3: Incorrect Style Property Name

```javascript
// ❌ Incorrect Property Name
legend: { color: { markerFill: 'red' } }  // Does not exist

// ✅ Correct Property Name (with prefix)
legend: { color: { itemMarkerFill: 'red' } }  // Correct
```

### Error 4: Confusing Legend Title with Chart Axis Title

```javascript
// ❌ Legend title written in axis
axis: { x: { title: 'Product Type' } }  // This is the X-axis title

// ✅ Legend title in legend
legend: { color: { title: 'Product Type' } }  // This is the legend title
```