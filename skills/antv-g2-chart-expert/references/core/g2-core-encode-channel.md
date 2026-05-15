---
id: "g2-core-encode-channel"
title: "Detailed Explanation of G2 Encode Channel System"
description: |
  Encode is the core data mapping mechanism in G2 v5, mapping data fields to visual channels (position, color, size, shape, etc.).
  In Spec mode, encode is a field in the options object; in the chained API, it is called via the .encode() method.

library: "g2"
version: "5.x"
category: "core"
tags:
  - "encode"
  - "通道"
  - "channel"
  - "数据映射"
  - "x"
  - "y"
  - "color"
  - "size"
  - "shape"
  - "spec"

related:
  - "g2-core-chart-init"
  - "g2-scale-linear"
  - "g2-scale-ordinal"
  - "g2-core-data-binding"

use_cases:
  - "Map data fields to visual attributes of a chart"
  - "Understand the structure of the encode object in Spec mode"
  - "Configure multi-channel mappings"

difficulty: "beginner"
completeness: "partial"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/encode"
---

## Core Concepts

**Channel** is an abstraction of graphical attributes. In Spec mode, `encode` is a field of the `options` object,
where each key is a channel name, and the value is a data field name (string) or a constant.

## General Channel List

| Channel | Description | Common Mark |
|------|------|-----------|
| `x` | X-axis position | All Marks |
| `y` | Y-axis position | All Marks |
| `color` | Color (fill + stroke) | All Marks |
| `size` | Size/Thickness | Point, Link, Line |
| `shape` | Shape | Point, Interval |
| `opacity` | Opacity | All Marks |
| `series` | Series grouping (does not affect color) | Line, Area |
| `key` | Element matching key during animation | All Marks |

## Basic Usage (Spec Mode)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',
  data: [
    { city: 'Beijing', gdp: 3.6 },
    { city: 'Shanghai', gdp: 4.0 },
    { city: 'Guangzhou', gdp: 2.8 },
  ],
  encode: {
    x: 'city',      // Category axis: Automatically uses Band Scale
    y: 'gdp',       // Numerical axis: Automatically uses Linear Scale
    color: 'city',  // Color distinction
  },
});

chart.render();
```

## Typical Scenario Examples

### Time X-Axis (Line Chart)

```javascript
chart.options({
  type: 'line',
  data: [
    { date: new Date('2024-01-01'), value: 100 },
    { date: new Date('2024-02-01'), value: 130 },
    { date: new Date('2024-03-01'), value: 110 },
  ],
  encode: {
    x: 'date',      // Date objects automatically use Time Scale
    y: 'value',
    color: 'series', // Multi-series line
  },
});
```

### Dual Numerical Axes + Bubble Chart (Multi-Channel Mapping)

```javascript
chart.options({
  type: 'point',
  data: [
    { income: 30000, lifeExpect: 72, population: 1400, country: 'China' },
    { income: 60000, lifeExpect: 79, population: 330,  country: 'USA' },
    { income: 45000, lifeExpect: 84, population: 125,  country: 'Japan' },
  ],
  encode: {
    x: 'income',
    y: 'lifeExpect',
    size: 'population',    // Bubble size
    color: 'country',
    shape: 'point',
  },
  scale: {
    size: { range: [10, 60] },
  },
});
```

### Function Mapping (Advanced)

```javascript
chart.options({
  type: 'point',
  data: [...],
  encode: {
    x: 'date',
    y: 'value',
    // When value is a function: Dynamically calculate channel values
    color: (d) => d.value > 100 ? 'red' : 'blue',
    size: (d) => Math.sqrt(d.count),
  },
});
```

## encode Field Value Type Description

| Value Type | Meaning | Example |
|------------|---------|--------|
| `string` (field name) | Maps to a data field | `'genre'` |
| `string` (color/shape constant) | Same value for all elements | `'#1890ff'`, `'circle'` |
| `number` | Same numerical value for all elements | `10` (size constant) |
| `function` | Dynamic calculation | `(d) => d.val * 2` |

> **Judgment Rules**: `encode.color` passed `'genre'` → considered as a field name; passed `'#1890ff'` → considered as a color constant (starts with `#` or a valid CSS color name). `encode.size` passed `10` (number) → considered as a constant.

## G2 v4 → v5 Spec Migration Reference

| G2 v4 Chaining | G2 v5 Spec `encode` Field |
|-----------|------------------------|
| `.position('x*y')` | `encode: { x: 'x', y: 'y' }` |
| `.color('type')` | `encode: { color: 'type' }` |
| `.size('count')` | `encode: { size: 'count' }` |
| `.shape('circle')` | `encode: { shape: 'circle' }` |
| `.opacity('rate')` | `encode: { opacity: 'rate' }` |

## Common Errors and Fixes

### Error 1: encode written in style
```javascript
// ❌ Incorrect: style does not perform data mapping
chart.options({
  type: 'interval',
  data: [...],
  style: { color: 'genre' },  // Invalid! genre is a field name, not a color value
});

// ✅ Correct: Use encode for data mapping, and style for fixed styles
chart.options({
  type: 'interval',
  data: [...],
  encode: { color: 'genre' },   // Data-driven color
  style: { fillOpacity: 0.8 },  // Fixed opacity
});
```

### Error 2: Confusion Between color and series Channels
```javascript
// Explanation: color both groups and changes colors; series only groups without changing colors
// For multi-series line charts, it is recommended to use color:
chart.options({
  type: 'line',
  encode: {
    x: 'month',
    y: 'value',
    color: 'type',    // ✅ Recommended: Each line has a different color
    // series: 'type', // Only groups, same color (less commonly used)
  },
});
```