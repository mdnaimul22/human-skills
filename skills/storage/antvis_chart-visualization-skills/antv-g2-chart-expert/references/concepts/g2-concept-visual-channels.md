---
id: "g2-concept-visual-channels"
title: "G2 Visual Channels"
description: |
  Visual channels are the mapping methods from data attributes to visual attributes, including position, color, size, shape, direction, etc.
  Understanding the perceptual efficiency and applicable data types of each channel helps in designing more accurate and effective data visualizations.
  This is the theoretical foundation of G2 encode configuration design.

library: "g2"
version: "5.x"
category: "concepts"
tags:
  - "visual channels"
  - "encode"
  - "perceptual efficiency"
  - "data mapping"
  - "visualization design"
  - "color"
  - "size"
  - "position"

related:
  - "g2-core-encode-channel"
  - "g2-concept-color-theory"

use_cases:
  - "Understand the design principles of each channel in G2 encode"
  - "Select appropriate visual channels for different data types"
  - "Avoid misuse of channels with low perceptual efficiency"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
---
## Core Concepts

Visual Channel is the medium that maps **data attributes** to **visual attributes**. In G2, this mapping is achieved through the `encode` field:

```javascript
chart.options({
  encode: {
    x: 'month',      // Position Channel (x-axis) ← Categorical Field
    y: 'revenue',    // Position Channel (y-axis) ← Numerical Field
    color: 'product',// Color Channel ← Categorical Field
    size: 'amount',  // Size Channel ← Numerical Field
  },
});
```

## Main Visual Channels and Their Perceptual Efficiency

### Quantitative Data (Continuous Values)

Sorted by perceptual accuracy from high to low:

| Rank | Channel | G2 Equivalent | Description |
|------|---------|---------------|-------------|
| ★★★★★ | **Position (x/y-axis)** | `encode.x`, `encode.y` | Most accurate, human eyes can compare precisely |
| ★★★★ | **Length/Height** | `encode.y` (bar chart) | Second most accurate, requires a common baseline |
| ★★★ | **Area/Size** | `encode.size` | Moderate, suitable for relative comparisons in bubble charts |
| ★★ | **Color Intensity** | `encode.color` (continuous color gradient) | Difficult to compare precisely, only suitable for rough trends |
| ★ | **Angle** | Pie chart sector angle | Human eyes are not accurate in judging angles, use with caution |

### Categorical Data (Discrete Categories)

| Channel | G2 Equivalent | Applicable Scenarios |
|------|---------|---------|
| **Position Grouping** | `encode.x` (Categorical Axis) | Categorization in bar charts and line charts |
| **Color (Hue)** | `encode.color` | Distinguishing ≤8 categories, more may cause confusion |
| **Shape** | `encode.shape` | Categorization in scatter plots, ≤6 categories |
| **Texture/Pattern** | `encode.shape` (Custom) | Colorless environments or auxiliary differentiation |

## Channel Adaptation Rules

```
Quantitative Data (Numerical) → Priority: Position Axis (x/y) > Size (size) > Color Depth (Continuous Color)
Categorical Data (Category) → Priority: Position Axis (x/y) > Color Hue (color) > Shape (shape)
Ordinal Data (Ranking) → Priority: Position Axis (Order) > Size (Decreasing) > Color (Gradient Color)
```

## Channel Combination Example

### Bubble Chart: 3 Numerical Channels

```javascript
// x position + y position + size = three-dimensional numerical encoding
chart.options({
  type: 'point',
  data,
  encode: {
    x: 'GDP',          // Quantitative → Position (most precise)
    y: 'LifeExpectancy',// Quantitative → Position
    size: 'Population', // Quantitative → Size (third dimension)
    color: 'Region',    // Categorical → Color Hue (fourth dimension)
  },
  scale: {
    size: { range: [4, 40] },   // Bubble size range
  },
});
```

### Heatmap: Color Depth Encoding Values

```javascript
// When color is used for quantitative data, use a sequential color scale (light → dark), not a categorical palette
chart.options({
  type: 'cell',
  data,
  encode: {
    x: 'weekday',
    y: 'hour',
    color: 'value',     // Quantitative → Color Depth (Continuous Scale)
  },
  scale: {
    color: {
      type: 'sequential',
      palette: 'blues',  // Sequential Scale (not a categorical palette)
    },
  },
});
```

## Common Channel Misuses

### Misuse 1: Using Color Hue to Represent Numerical Magnitude

```javascript
// ❌ Misuse: Color hue (red/green/blue) cannot express numerical magnitude relationships
chart.options({
  encode: { color: 'temperature' },   // temperature is numerical, hue cannot represent magnitude
  scale: { color: { type: 'ordinal' } },   // ❌ Categorical palette used for numerical data
});

// ✅ Correct: Numerical data uses a continuous color scale
chart.options({
  encode: { color: 'temperature' },
  scale: {
    color: {
      type: 'sequential',   // Sequential scale
      palette: 'reds',      // Light→Dark sequential color
    },
  },
});
```

### Misuse 2: Too Many Color Categories Leading to Difficulty in Distinguishing

```javascript
// ❌ More than 8 color categories, difficult for the human eye to distinguish
chart.options({
  encode: { color: 'province' },   // If there are 31 provinces, colors cannot effectively distinguish
});

// ✅ Alternatives when exceeding 8 categories:
// 1. Merge minor categories into "Other"
// 2. Switch to position channel (grouped bar chart/facet)
// 3. Use interactive filtering (click legend to show/hide)
```

### Misuse 3: Too Many Sectors in Pie Charts

```javascript
// ❌ Low angle channel perception accuracy, difficult to compare with more than 5 sectors
chart.options({
  type: 'interval',
  coordinate: { type: 'theta' },
  // If there are 10+ categories, the pie chart effect is poor
});

// ✅ Use bar charts instead when there are many categories (position channel perception is more accurate)
chart.options({
  type: 'interval',
  encode: { x: 'category', y: 'value' },
  transform: [{ type: 'sortX', by: 'y', reverse: true }],
});
```