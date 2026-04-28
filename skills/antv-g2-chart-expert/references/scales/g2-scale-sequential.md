---
id: "g2-scale-sequential"
title: "G2 Sequential Scale"
description: |
  The sequential scale maps continuous numerical values to color gradients,
  specifically designed for the color channel, often used in conjunction with palette (built-in color boards) or custom color interpolation functions.
  Suitable for heatmaps, map coloring, and continuous numerical color encoding scenarios.
  Difference from linear: sequential is optimized for color output, while linear supports arbitrary numerical output.
  ⚠️ Constraint: Use only when the field mapped by encode.color is of continuous type (numerical).
  Categorical fields (string/enumeration) and discrete fields (ordinal/band) are prohibited from using sequential,
  as they will produce incorrect color gradients; instead, use the ordinal scale.

library: "g2"
version: "5.x"
category: "scales"
tags:
  - "sequential"
  - "sequential scale"
  - "color gradient"
  - "continuous color"
  - "palette"
  - "scale"

related:
  - "g2-scale-linear"
  - "g2-scale-quantile-quantize"
  - "g2-scale-threshold"
  - "g2-mark-cell-heatmap"

use_cases:
  - "Heatmap color gradient (low value → high value)"
  - "Choropleth map coloring by value"
  - "Scatter plot bubble color gradient by value"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/scale/sequential"
---

## ⚠️ Usage Constraints

**sequential is only applicable when the `encode.color` field is of a continuous type (numerical).**

| Field Type | Example | Usable with sequential |
|------------|---------|------------------------|
| Continuous (quantitative) | `temp_max`, `sales`, `score` | ✅ Allowed |
| Categorical (categorical / ordinal) | `city`, `category`, `name` | ❌ Prohibited, use `ordinal` |
| Discontinuous (band / point) | Discrete axis fields | ❌ Prohibited, use `ordinal` |

Using sequential with categorical or discontinuous fields will result in all data being mapped to the two ends of the gradient, leading to extremely poor color differentiation.

## Minimum Viable Example (Heatmap)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 400 });

chart.options({
  type: 'cell',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/seattle-weather.json',
  },
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max',
  },
  transform: [{ type: 'group', color: 'max' }],
  scale: {
    color: {
      type: 'sequential',
      palette: 'gnBu',   // Built-in color palette: from light blue to dark blue
    },
  },
  style: { inset: 0.5 },
});

chart.render();
```

## Complete List of Valid Palettes

G2's `palette` values are looked up via d3-scale-chromatic, and **only the following names are valid** (case-insensitive). Names not in this list (e.g., `'blueOrange'`, `'redGreen'`, `'heatmap'`) will result in a runtime error `Unknown palette`.

### Monochromatic Sequential Gradients (Suitable for Sequential — Positive Data)

| palette Name | Effect |
|------------|------|
| `'blues'` | White → Blue |
| `'greens'` | White → Green |
| `'reds'` | White → Red |
| `'oranges'` | White → Orange |
| `'purples'` | White → Purple |
| `'greys'` | White → Grey |
| `'orRd'` | Orange → Red |
| `'buGn'` | Blue → Green |
| `'buPu'` | Blue → Purple |
| `'gnBu'` | Green → Blue |
| `'puBu'` | Purple → Blue |
| `'puBuGn'` | Purple → Blue → Green |
| `'puRd'` | Purple → Red |
| `'rdPu'` | Red → Purple |
| `'ylGn'` | Yellow → Green |
| `'ylGnBu'` | Yellow → Green → Blue (Sequential default) |
| `'ylOrBr'` | Yellow → Orange → Brown |
| `'ylOrRd'` | Yellow → Orange → Red |

### Multi-Color Perceptually Uniform Gradients (Suitable for Sequential — Colorblind-Friendly Recommended)

| palette Name | Effect |
|--------------|------|
| `'viridis'` | Purple → Blue → Green → Yellow (Perceptually uniform, colorblind-friendly) |
| `'plasma'` | Blue-Purple → Orange-Yellow |
| `'magma'` | Black → Purple → Orange → White |
| `'inferno'` | Black → Purple → Red → Yellow |
| `'cividis'` | Blue → Yellow (Friendly to all types of colorblindness) |
| `'turbo'` | Blue → Green → Yellow → Red (Improved rainbow) |
| `'rainbow'` | Rainbow (Not recommended, perceptually non-uniform) |
| `'sinebow'` | Smooth Rainbow |
| `'warm'` | Warm Colors (Orange → Red → Purple) |
| `'cool'` | Cool Colors (Cyan → Blue → Purple) |
| `'cubehelixDefault'` | Spiral Gradient (Black → White) |

### Diverging Color Scale (Suitable for Diverging — Positive and Negative Value Comparison)

| Palette Name | Effect |
|--------------|------|
| `'rdBu'` | Red → White → Blue (Most Common) |
| `'rdYlBu'` | Red → Yellow → Blue |
| `'rdYlGn'` | Red → Yellow → Green (Rise and Fall Heatmap) |
| `'rdGy'` | Red → White → Gray |
| `'pRGn'` | Purple → White → Green |
| `'piYG'` | Pink → White → Yellow-Green |
| `'puOr'` | Purple → White → Orange |
| `'brBG'` | Brown → White → Blue-Green |
| `'spectral'` | Red → Orange → Yellow → Green → Blue (Multi-Color Diverging) |

```javascript
// ✅ Valid Examples
scale: { color: { type: 'sequential', palette: 'blues' } }
scale: { color: { type: 'sequential', palette: 'viridis' } }
scale: { color: { type: 'sequential', palette: 'ylOrRd' } }
scale: { color: { type: 'diverging',  palette: 'rdBu' } }
scale: { color: { type: 'diverging',  palette: 'rdYlGn' } }

// ❌ Invalid Examples (Non-existent, will throw Unknown palette error)
scale: { color: { type: 'sequential', palette: 'blueOrange' } }  // ❌ Non-existent
scale: { color: { type: 'sequential', palette: 'redGreen' } }    // ❌ Non-existent
scale: { color: { type: 'sequential', palette: 'heatmap' } }     // ❌ Non-existent
scale: { color: { type: 'sequential', palette: 'rainbow2' } }    // ❌ Non-existent
scale: { color: { type: 'sequential', palette: 'blue-orange' } } // ❌ Non-existent
```

## Custom Color Range

```javascript
// Use range to specify start and end colors (interpolation at both ends)
chart.options({
  scale: {
    color: {
      type: 'sequential',
      range: ['#ebedf0', '#196127'],  // From light gray to dark green (GitHub contribution graph style)
    },
  },
});

// Use domain to control the mapping range
chart.options({
  scale: {
    color: {
      type: 'sequential',
      palette: 'blues',
      domain: [0, 100],   // Explicitly specify the numerical range
    },
  },
});
```

## Sequential vs Other Color Scales

```javascript
// sequential: Continuous color gradient (continuous value → continuous color)
scale: { color: { type: 'sequential', palette: 'blues' } }

// quantile: Automatic quantile grouping (continuous value → discrete color, equal frequency grouping)
scale: { color: { type: 'quantile', range: ['#eee', '#aaa', '#666', '#000'] } }

// quantize: Equal interval segmentation (continuous value → discrete color, equal interval grouping)
scale: { color: { type: 'quantize', domain: [0, 100], range: ['#fee', '#f99', '#f00'] } }

// threshold: Manual breakpoint grading (continuous value → discrete color, custom breakpoints)
scale: { color: { type: 'threshold', domain: [25, 75], range: ['#0f0', '#ff0', '#f00'] } }
```

## Common Errors and Fixes

### Error: Using Non-Existent Palette Names

G2's palette values come from d3-scale-chromatic. Non-existent names will throw an `Error: Unknown palette: XxxXxx` at runtime, preventing the chart from rendering.

```javascript
// ❌ These names seem reasonable but do not exist in G2
scale: { color: { type: 'sequential', palette: 'blueOrange' } }   // ❌ → Error: Unknown palette
scale: { color: { type: 'sequential', palette: 'blueGreen' } }    // ❌ → Use 'buGn' or 'gnBu'
scale: { color: { type: 'sequential', palette: 'redBlue' } }      // ❌ → Use 'rdBu' (diverging)
scale: { color: { type: 'diverging',  palette: 'greenRed' } }     // ❌ → Use 'rdYlGn' (note the order)
scale: { color: { type: 'sequential', palette: 'hot' } }          // ❌ → Does not exist, use 'ylOrRd' instead
scale: { color: { type: 'sequential', palette: 'jet' } }          // ❌ → Does not exist, use 'turbo' instead
scale: { color: { type: 'sequential', palette: 'coolwarm' } }     // ❌ → Use 'rdBu' (diverging)

// ✅ When in doubt, choose from the following valid names
// Monochromatic Sequential: 'blues' | 'greens' | 'reds' | 'oranges' | 'purples' | 'ylOrRd' | 'ylGnBu'
// Perceptually Uniform: 'viridis' | 'plasma' | 'magma' | 'inferno' | 'cividis' | 'turbo'
// Diverging:    'rdBu' | 'rdYlGn' | 'rdYlBu' | 'pRGn' | 'brBG' | 'spectral'
```

### Error: Using sequential for categorical data
```javascript
// ❌ sequential is only suitable for continuous numerical data, use ordinal for categorical data
chart.options({
  encode: { color: 'city' },   // city is a categorical field
  scale: { color: { type: 'sequential' } },  // ❌ will produce strange gradients
});

// ✅ Use ordinal for categorical data
chart.options({
  encode: { color: 'city' },
  scale: { color: { type: 'ordinal', range: ['#5B8FF9', '#61DDAA', '#FFD666'] } },  // ✅
});
```

### Error: Abnormal Data Aggregation Due to Unused Transform

When using a `cell` type chart, if the original data contains multiple records with the same `(x, y)` coordinates, you must use `transform` to aggregate them. Otherwise, it may result in inaccurate color mapping or even chart rendering failure.

```javascript
// ❌ No aggregation of temp_max values for identical coordinates
chart.options({
  type: 'cell',
  data: weatherData,
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max',
  },
  scale: { color: { type: 'sequential', palette: 'gnBu' } },
});

// ✅ Using group transform to aggregate data for identical coordinates
chart.options({
  type: 'cell',
  data: weatherData,
  encode: {
    x: (d) => new Date(d.date).getUTCDate(),
    y: (d) => new Date(d.date).getUTCMonth(),
    color: 'temp_max',
  },
  transform: [{ type: 'group', color: 'max' }],  // Take the maximum temp_max value for each cell
  scale: { color: { type: 'sequential', palette: 'gnBu' } },
});
```