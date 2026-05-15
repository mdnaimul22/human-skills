---
id: "g2-theme-builtin"
title: "G2 Built-in Theme Configuration"
description: |
  G2 v5 includes three built-in themes: classic, classicDark, and academy.
  Switch globally using the theme field or the theme parameter in the Chart constructor, or override style variables locally.

library: "g2"
version: "5.x"
category: "themes"
tags:
  - "theme"
  - "主题"
  - "dark"
  - "深色主题"
  - "classicDark"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-mark-interval-basic"

use_cases:
  - "Switch overall chart color style"
  - "Adapt to Dark Mode"
  - "Unify visual style across multiple charts"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/theme"
---

## Built-in Theme List

| Theme Name | Description |
|------------|-------------|
| `'classic'` | Default theme (blue tones, white background) |
| `'classicDark'` | Dark theme (dark background, bright colors) |
| `'academy'` | Academic style theme (gray tones, suitable for papers/reports) |

## Basic Usage (Switching Themes)

```javascript
import { Chart } from '@antv/g2';

// Method 1: Specify in the constructor
const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
  theme: 'classicDark',    // Dark theme
});

chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
  ],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
});

chart.render();
```

```javascript
// Method 2: Specify in options
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  theme: 'academy',        // Academic theme
});

chart.render();
```

## Dark Theme Example

```javascript
const chart = new Chart({
  container: 'container',
  width: 700,
  height: 400,
  theme: 'classicDark',
});

chart.options({
  type: 'view',
  data,
  encode: { x: 'month', y: 'value' },
  children: [
    {
      type: 'area',
      style: { fillOpacity: 0.3 },
    },
    {
      type: 'line',
      style: { lineWidth: 2 },
    },
  ],
});

chart.render();
```

## Runtime Theme Switching

```javascript
const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({ type: 'interval', data, encode: { x: 'x', y: 'y' } });
chart.render();

// Switch to dark theme (re-rendering required)
chart.theme('classicDark');
chart.render();
```

## Partial Override of Theme Variables

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  theme: {
    defaultColor: '#ff6b35',         // Default color (color of the first series)
    defaultStrokeColor: '#333',      // Default stroke color
    // Override color palette
    colors10: [
      '#ff6b35', '#f7c59f', '#efefd0', '#004e89', '#1a936f',
      '#88d498', '#c6dabf', '#eaf4d3', '#7b2d8b', '#ff3a5c',
    ],
  },
});
```

## Custom Theme Registration

```javascript
import { Chart, register } from '@antv/g2';

// Register custom theme
register('theme.myTheme', {
  defaultColor: '#e63946',
  background: '#f8f9fa',
  colors10: ['#e63946', '#457b9d', '#1d3557', '#a8dadc', '#f1faee'],
  // ... other variables
});

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  theme: 'myTheme',   // Use custom theme
});

chart.render();
```

## Common Errors and Fixes

### Error: Non-string/object type passed to theme
```javascript
// ❌ Error: theme value does not exist
chart.options({ theme: 'dark' });   // 'dark' is not a built-in theme name

// ✅ Correct: Using built-in theme names
chart.options({ theme: 'classicDark' });   // Dark theme
chart.options({ theme: 'classic' });       // Default theme
chart.options({ theme: 'academy' });       // Academic theme
```

### Error: Forgot to Re-render After Switching Theme
```javascript
// ❌ Error: Did not re-render after switching theme
chart.theme('classicDark');
// The chart does not change!

// ✅ Correct: Call render() after switching
chart.theme('classicDark');
chart.render();
```