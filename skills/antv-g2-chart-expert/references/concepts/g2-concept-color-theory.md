---
id: "g2-concept-color-theory"
title: "G2 Color Theory"
description: |
  Three color usage patterns in data visualization: categorical palettes (distinguishing categories),
  sequential color scales (representing numerical magnitudes), and diverging color scales (representing positive and negative deviations).
  Covers G2 scale.color configuration methods and common color misuse.

library: "g2"
version: "5.x"
category: "concepts"
tags:
  - "配色"
  - "color"
  - "色板"
  - "顺序色阶"
  - "发散色阶"
  - "分类色板"
  - "palette"
  - "scale.color"

related:
  - "g2-concept-visual-channels"
  - "g2-core-encode-channel"
  - "g2-theme-builtin"

use_cases:
  - "Selecting the correct color pattern for different data types"
  - "Configuring G2 scale.color to achieve correct color mapping"
  - "Avoiding color-induced data misinterpretation"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
---

## Three Color Usage Modes

### 1. Categorical Palette

**Usage**: Distinguish different categories (qualitative data), colors **do not imply any order**

```javascript
// Scenario: Multi-series line chart, using colors to differentiate product lines
chart.options({
  type: 'line',
  data,
  encode: { x: 'month', y: 'sales', color: 'product' },
  // Categorical palette is the default, no configuration needed
  // For custom palette:
  scale: {
    color: {
      type: 'ordinal',
      range: ['#1890ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1'],
    },
  },
});
```

**Rules**:
- Maximum **8 colors**, exceeding this makes differentiation difficult
- Similar brightness between colors (avoid one category standing out excessively)
- Consider color blindness accessibility (common red-green blindness, avoid using only red/green for differentiation)

### 2. Sequential Scale

**Usage**: Represents values from small to large, with colors ranging from light to dark (or a single hue variation).

```javascript
// Scenario: Color depth in heatmaps, maps, and bubble charts
chart.options({
  type: 'cell',
  data,
  encode: { x: 'weekday', y: 'hour', color: 'count' },
  scale: {
    color: {
      type: 'sequential',     // Sequential scale
      palette: 'blues',        // Monochromatic: whites → blues
      // Common built-in scales: 'blues' | 'greens' | 'oranges' | 'reds' | 'purples'
      // Multichromatic: 'YlOrRd' | 'YlGnBu' | 'BuPu' | 'GnBu'
    },
  },
});
```

**Rules**:
- Larger values → Darker colors (natural perception)
- Use **monochromatic** (same hue with varying shades) or **multichromatic gradients**
- Do not use categorical color palettes to represent numerical values (red/green lacks a sense of magnitude)

### 3. Diverging Scale

**Usage**: Represents positive and negative deviations centered around zero (or a reference value)

```javascript
// Scenario: Profit/Loss Heatmap, YoY Growth/Decline, Difference Comparison
chart.options({
  type: 'cell',
  data,
  encode: { x: 'product', y: 'region', color: 'growth' },
  scale: {
    color: {
      type: 'diverging',      // Diverging scale
      palette: 'RdBu',        // Red (negative) → White (zero) → Blue (positive)
      // Common palettes: 'RdBu' | 'RdYlGn' | 'BrBG' | 'PuOr'
      domain: [-100, 0, 100], // Symmetric range (centered at 0)
    },
  },
});
```

**Rules**:
- Neutral value (zero/average) maps to **white or light gray**
- Colors at both ends have **comparable perceptual intensity** (avoid one end being visually more prominent)
- Define a symmetric domain (e.g., `[-50, 0, 50]`)

## Color Channel and Scale Configuration

```javascript
// G2 Complete Color Configuration
scale: {
  color: {
    // ── Scale Type ────────────────────────
    type: 'ordinal',     // Categorical: 'ordinal'
    // type: 'sequential', // Continuous Sequential
    // type: 'diverging',  // Diverging
    // type: 'threshold',  // Threshold

    // ── Color Range (Categorical Palette) ────────────────
    range: ['#1890ff', '#52c41a', '#fa8c16'],   // Custom color list

    // ── Built-in Palette Name ───────────────────────────
    palette: 'tableau10',   // 'tableau10' | 'category10' | 'blues' etc.

    // ── Domain (Display Order of Categories) ─────────────
    domain: ['Product A', 'Product B', 'Product C'],

    // ── Color for Unknown Values ─────────────────────────
    unknown: '#f0f0f0',
  },
}
```

## Built-in Palette Complete Reference

**⚠️ Important: Only use the names listed in the table below**. G2's `palette` is looked up via d3-scale-chromatic. Names not in this list (e.g., `'blueOrange'`, `'redGreen'`, `'heatmap'`, `'hot'`, `'jet'`) will throw a `Unknown palette` error at runtime, and the chart will fail to render. Names are case-insensitive (both `'blues'` and `'Blues'` are valid).

### Categorical Palette (for ordinal scales, used to distinguish categories)

| Palette Name | Number of Colors | Style |
|--------------|---------------|------|
| `'tableau10'` | 10 | Tableau classic palette (soft, default) |
| `'category10'` | 10 | D3 classic categorical colors |
| `'set2'` | 8 | Pastel style, mild |
| `'paired'` | 12 | Paired colors (light + dark) |
| `'dark2'` | 8 | Dark tones, high contrast |
| `'set1'` | 9 | High saturation |
| `'set3'` | 12 | Medium saturation |
| `'pastel1'` | 9 | Light pastel colors |
| `'pastel2'` | 8 | Light pastel colors |
| `'accent'` | 8 | Accent colors |

### Sequential Scale (for positive value numerical mapping)

| Color Palette Name | Effect |
|-------|------|
| `'blues'` | White → Blue |
| `'greens'` | White → Green |
| `'reds'` | White → Red |
| `'oranges'` | White → Orange |
| `'purples'` | White → Purple |
| `'greys'` | White → Grey |
| `'ylOrRd'` | Yellow → Orange → Red (commonly used in heatmaps) |
| `'ylGnBu'` | Yellow → Green → Blue (default for sequential) |
| `'ylOrBr'` | Yellow → Orange → Brown |
| `'buGn'` | Blue → Green |
| `'buPu'` | Blue → Purple |
| `'gnBu'` | Green → Blue |
| `'orRd'` | Orange → Red |
| `'puBu'` | Purple → Blue |
| `'puBuGn'` | Purple → Blue → Green |
| `'puRd'` | Purple → Red |
| `'rdPu'` | Red → Purple |
| `'ylGn'` | Yellow → Green |
| `'viridis'` | Purple → Blue → Green → Yellow (perceptually uniform, **colorblind-friendly**, recommended) |
| `'plasma'` | Blue-Purple → Orange-Yellow |
| `'magma'` | Black → Purple → Orange → White |
| `'inferno'` | Black → Purple → Red → Yellow |
| `'cividis'` | Blue → Yellow (friendly to all types of colorblindness) |
| `'turbo'` | Blue → Green → Yellow → Red (improved rainbow) |
| `'warm'` | Orange → Red → Purple (warm tones) |
| `'cool'` | Cyan → Blue → Purple (cool tones) |
| `'rainbow'` | Rainbow (perceptually non-uniform, not recommended) |
| `'sinebow'` | Smooth Rainbow |
| `'cubehelixDefault'` | Spiral Gradient |

### Diverging Scale (for contrasting positive and negative values)

| Color Palette Name | Effect |
|-------|------|
| `'rdBu'` | Red → White → Blue (**Most Commonly Used**, Rise/Fall or Positive/Negative) |
| `'rdYlBu'` | Red → Yellow → Blue |
| `'rdYlGn'` | Red → Yellow → Green (Year-over-Year Increase/Decrease) |
| `'rdGy'` | Red → White → Gray |
| `'pRGn'` | Purple → White → Green |
| `'piYG'` | Pink → White → Yellow-Green |
| `'puOr'` | Purple → White → Orange |
| `'brBG'` | Brown → White → Blue-Green |
| `'spectral'` | Red → Orange → Yellow → Green → Blue (Multi-Color Diverging) |

## Colorblind-Friendly Color Schemes

Approximately 8% of males have red-green colorblindness, so avoid using only red/green to differentiate data:

```javascript
// ❌ Unfriendly: Red/Green differentiation (colorblind users cannot distinguish)
scale: { color: { range: ['#ff4d4f', '#52c41a'] } }

// ✅ Friendly: Use Blue/Orange (colorblind users can distinguish)
scale: { color: { range: ['#1890ff', '#fa8c16'] } }

// ✅ Alternatively, use dual-channel encoding with color + shape
chart.options({
  type: 'point',
  encode: {
    color: 'category',
    shape: 'category',   // Also differentiate using shape (not dependent on color)
  },
});
```

## Common Color Errors

### Error 1: Using Categorical Color Palette for Numerical Data (Heatmap)

```javascript
// ❌ Using categorical colors (red/blue/green) to represent numerical values, lacking any pattern
chart.options({
  type: 'cell',
  encode: { color: 'temperature' },
  scale: { color: { type: 'ordinal' } },   // ❌ Numerical data using categorical color palette
});

// ✅ Using sequential color scale for numerical data
chart.options({
  type: 'cell',
  encode: { color: 'temperature' },
  scale: { color: { type: 'sequential', palette: 'YlOrRd' } },   // ✅
});
```

### Error 2: Asymmetric Diverging Scale Domain

```javascript
// ❌ Asymmetric domain, zero point not at the color midpoint
scale: {
  color: {
    type: 'diverging',
    palette: 'RdBu',
    domain: [-20, 100],   // ❌ Small negative range, zero point skewed left
  },
}

// ✅ Symmetric domain, zero point at the center
scale: {
  color: {
    type: 'diverging',
    palette: 'RdBu',
    domain: [-100, 0, 100],   // ✅ Explicitly specify three control points
  },
}
```

### Error 3: Too Many Colors Leading to Confusion

```javascript
// ❌ 12 colors, readers cannot distinguish
chart.options({
  encode: { color: 'province' },   // 31 provinces
});

// ✅ Group or merge, keep ≤ 8 color categories
// Solution: Take Top 7 + "Others"
const processedData = aggregateTopN(data, 'province', 7);
```