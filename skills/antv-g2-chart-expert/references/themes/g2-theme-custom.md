---
id: "g2-theme-custom"
title: "G2 Custom Theme Creation (register + create)"
description: |
  G2 v5 supports registering custom themes via `register('theme.xxx', themeConfig)`.
  Custom themes can override color palettes, fonts, default styles for various Marks, etc.
  You can also pass an object through the `theme` field to partially override specific properties of the current theme.
  Built-in themes include `classic`, `classicDark`, `academy` (see `g2-theme-builtin` for details).

library: "g2"
version: "5.x"
category: "themes"
tags:
  - "theme"
  - "custom theme"
  - "register"
  - "theme registration"
  - "colors10"
  - "colors20"
  - "color scheme"

related:
  - "g2-theme-builtin"
  - "g2-core-chart-init"

use_cases:
  - "Corporate brand customized chart themes"
  - "Unified color styles across multiple charts"
  - "Partially override specific default styles"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/theme"
---

## Method 1: Partial Theme Override (theme Object)

The simplest way is to directly pass an object in the theme field of options, overriding some properties:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  theme: {
    // Override categorical color palette
    colors10: [
      '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
      '#8B5CF6', '#F97316', '#06B6D4', '#84CC16',
      '#EC4899', '#6B7280',
    ],
    // Override default color
    defaultColor: '#3B82F6',
  },
});

chart.render();
```

## Method Two: Register Global Custom Theme

```javascript
import { Chart, register } from '@antv/g2';

// Register custom theme (based on classic theme extension)
register('theme.brand', {
  // Base colors
  defaultColor: '#e63946',
  defaultStrokeColor: '#1d1d1d',

  // Categorical color palette (10 colors / 20 colors)
  colors10: [
    '#e63946', '#457b9d', '#1d3557', '#a8dadc',
    '#f1faee', '#e9c46a', '#f4a261', '#e76f51',
    '#264653', '#2a9d8f',
  ],
  colors20: [
    '#e63946', '#457b9d', '#1d3557', '#a8dadc',
    '#f1faee', '#e9c46a', '#f4a261', '#e76f51',
    '#264653', '#2a9d8f',
    // Last 10 colors (gradient or variant)
    '#ff6b6b', '#74b9ff', '#55efc4', '#ffeaa7',
    '#dfe6e9', '#fab1a0', '#fd79a8', '#6c5ce7',
    '#00b894', '#00cec9',
  ],
});

// Use custom theme
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  theme: 'brand',   // Use the registered custom theme name
});

chart.render();
```

## Theme Configuration Quick Reference

```javascript
// The following are the main configuration items that can be overridden
const themeConfig = {
  // ── Base Colors ─────────────────────────────
  defaultColor: '#1890ff',        // Default color (for single series)
  defaultStrokeColor: '#ffffff',  // Default stroke color

  // ── Color Palette ───────────────────────────
  colors10: [...],   // 10-color categorical palette
  colors20: [...],   // 20-color categorical palette

  // ── Background ──────────────────────────────
  background: '#ffffff',    // Chart background color

  // ── Font ────────────────────────────────────
  fontFamily: 'sans-serif',  // Global font family

  // ── Default Animation Durations ─────────────
  enter: { duration: 300 },
  update: { duration: 300 },
  exit: { duration: 300 },
};
```

## Dark Theme (Based on Partial Override of classicDark)

```javascript
// Modify based on classicDark
const chart = new Chart({
  container: 'container',
  theme: 'classicDark',
});

chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value', color: 'type' },
  // Partial override: Modify color palette while retaining dark background
  theme: {
    colors10: ['#60a5fa', '#34d399', '#f87171', '#a78bfa',
               '#fbbf24', '#22d3ee', '#f472b6', '#4ade80',
               '#fb923c', '#e879f9'],
  },
});
```

## Common Errors and Fixes

### Error: Forgot to add 'theme.' prefix to the registered theme name
```javascript
// ❌ Error: Registration must use the 'theme.xxx' format
register('brandTheme', { colors10: [...] });    // ❌
chart.options({ theme: 'brandTheme' });          // Does not take effect

// ✅ Correct: Must add 'theme.' prefix
register('theme.brandTheme', { colors10: [...] });  // ✅
chart.options({ theme: 'brandTheme' });              // ✅ Use without prefix when applying
```

### Error: Mixing theme and style
```javascript
// ❌ Error: Confusing theme colors with individual mark styles
chart.options({
  type: 'interval',
  style: { colors10: [...] },  // ❌ colors10 does not belong in style
});

// ✅ Color theme in the theme field
chart.options({
  type: 'interval',
  theme: { colors10: [...] },  // ✅
  style: { fillOpacity: 0.8 }, // ✅ Individual mark style in style
});
```