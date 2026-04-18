---
id: "g2-animation-types"
title: "Detailed Explanation of G2 Built-in Animation Types (fadeIn/scaleIn/growIn/pathIn/waveIn/zoomIn/morphing)"
description: |
  G2 v5 includes multiple built-in animation types, each suitable for different Marks and coordinate systems:
  fadeIn/Out (fade in/out), scaleInX/Y (scale in along X/Y axis), growInX/Y (grow in along X/Y axis),
  pathIn (path drawing), waveIn (polar wave in), zoomIn/Out (zoom in/out), morphing (shape transition).
  These animations can be configured using animate.enter.type and similar settings.

library: "g2"
version: "5.x"
category: "animations"
tags:
  - "fadeIn"
  - "scaleInX"
  - "scaleInY"
  - "growInX"
  - "growInY"
  - "pathIn"
  - "waveIn"
  - "zoomIn"
  - "zoomOut"
  - "morphing"
  - "animation types"

related:
  - "g2-animation-intro"
  - "g2-animation-keyframe"

use_cases:
  - "Selecting the most appropriate entrance animation based on chart type"
  - "Line chart path drawing animation"
  - "Pie/rose chart wave entrance"
  - "Shape transition during data updates"

difficulty: "beginner"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/animate"
---

## Animation Types and Applicable Scenarios

| Animation Name | Direction | Best for Mark | Features |
|----------------|-----------|---------------|----------|
| `fadeIn` | - | All Marks | Fade in, universal, safest |
| `fadeOut` | - | All Marks | Fade out, universal exit |
| `scaleInX` | X-axis | interval (bar chart) | Expands from top-left to right |
| `scaleInY` | Y-axis | interval (bar chart) | Scales up from bottom to top |
| `scaleOutX` | X-axis | interval | Exit version of scaleInX |
| `scaleOutY` | Y-axis | interval | Exit version of scaleInY |
| `growInX` | X-axis | line, area, interval (Cartesian coordinates) | Clips and grows from left to right |
| `growInY` | Y-axis | interval, area (Cartesian coordinates) | Clips and grows from bottom to top; **Disabled for polar/helix coordinates** |
| `pathIn` | Path | line, path, link | Path lines drawn step by step |
| `waveIn` | Wave | interval (polar coordinates) | Polar-specific sector expansion |
| `zoomIn` | Center | point, text | Zooms in from the center |
| `zoomOut` | Center | point, text | Zooms out and disappears into the center |
| `morphing` | Morphing | All Marks | Smooth shape transition |

## fadeIn / fadeOut

```javascript
// The most universal animation, suitable for any mark
chart.options({
  type: 'point',
  data,
  encode: { x: 'x', y: 'y' },
  animate: {
    enter: { type: 'fadeIn', duration: 600 },
    exit: { type: 'fadeOut', duration: 300 },
  },
});
```

## scaleInY / growInY (Bar Chart Entry)

```javascript
// scaleInY: Scale expansion (with a scaling effect)
// growInY: Crop growth (with a "growing from the ground" feel, more natural)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  animate: {
    // Method 1: Scaling
    enter: { type: 'scaleInY', duration: 800, easing: 'ease-out' },
    // Method 2: Growth (recommended)
    // enter: { type: 'growInY', duration: 800 },
  },
});
```

## pathIn (Line Chart Path Drawing)

```javascript
// pathIn: Line/path gradually drawn from left to right
chart.options({
  type: 'line',
  data: timeSeriesData,
  encode: { x: 'date', y: 'value', color: 'type' },
  animate: {
    enter: {
      type: 'pathIn',      // Path drawn gradually
      duration: 1500,
      easing: 'linear',    // Linear easing for better effect
    },
  },
});
```

## waveIn (Exclusive to Polar/Pie Charts)

```javascript
// waveIn: Wave sweep from the outer circle to the inner, specifically designed for polar coordinates
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.8 },
  animate: {
    enter: {
      type: 'waveIn',       // Exclusive to polar coordinates
      duration: 1000,
    },
  },
});
```

## zoomIn / zoomOut (Point Chart Zoom)

```javascript
// zoomIn: Scatter points zoom in from the center
chart.options({
  type: 'point',
  data: scatterData,
  encode: { x: 'x', y: 'y', size: 'value' },
  animate: {
    enter: { type: 'zoomIn', duration: 500 },
    exit: { type: 'zoomOut', duration: 300 },
  },
});
```

## Morphing (Shape Transformation Animation)

```javascript
// morphing: Smooth shape transformation during data updates
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold' },
  animate: {
    update: {
      type: 'morphing',    // Shape transformation transition during data updates
      duration: 600,
    },
  },
});

// Morphing can also be automatically triggered in timingKeyframe
chart.options({
  type: 'timingKeyframe',
  children: [
    { type: 'interval', data, encode: { x: 'x', y: 'y' } },
    { type: 'line',     data, encode: { x: 'x', y: 'y' } },
  ],
});
```
## 按图表类型推荐的动画

```javascript
// 柱状图（推荐 growInY）
{ type: 'interval', animate: { enter: { type: 'growInY', duration: 800 } } }

// 条形图（推荐 growInX）
{ type: 'interval', coordinate: { transform: [{ type: 'transpose' }] },
  animate: { enter: { type: 'growInX', duration: 800 } } }

// 折线图（推荐 pathIn）
{ type: 'line', animate: { enter: { type: 'pathIn', duration: 1200 } } }

// 散点图（推荐 zoomIn 或 fadeIn）
{ type: 'point', animate: { enter: { type: 'zoomIn', duration: 400 } } }

// 饼图/环形图（推荐 waveIn）
{ type: 'interval', coordinate: { type: 'theta' },
  animate: { enter: { type: 'waveIn', duration: 1000 } } }

// 面积图（推荐 fadeIn 或 growInX）
{ type: 'area', animate: { enter: { type: 'fadeIn', duration: 800 } } }

// 螺旋图 helix 坐标系（必须用 fadeIn，禁止用 growInX/Y）
{ type: 'interval', coordinate: { type: 'helix', ... },
  animate: { enter: { type: 'fadeIn', duration: 800 } } }
```

## 常见错误与修正

### 错误 1：在条形图（转置）上用 scaleInY
```javascript
// ❌ 条形图是水平方向，用 scaleInY（竖向缩放）效果不对
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  animate: { enter: { type: 'scaleInY' } },  // ❌ 应该用 growInX 或 scaleInX
});

// ✅ 条形图用 X 方向动画
chart.options({
  animate: { enter: { type: 'growInX', duration: 800 } },  // ✅
});
```

### 错误 2：在 helix（螺旋）坐标系上用 growInX/growInY

`growInX` / `growInY` 的实现是沿直角坐标轴方向做 **clipPath 裁剪**。在 `helix` 坐标系中，坐标轴被重映射为螺旋路径，屏幕上不存在"底部"或"左侧"基线，裁剪矩形会横穿螺旋形，导致部分螺旋区域被切掉或渲染残缺，动画结束后图表也可能显示不完整。

**同样问题适用于所有非直角坐标系**（`polar`、`theta`、`helix`）——这些坐标系均应使用 `waveIn`（极坐标专用）或 `fadeIn`（通用），不能使用 `growInX/Y`。

```javascript
// ❌ 错误：helix 坐标系用 growInY → 裁剪矩形横穿螺旋，图表渲染残缺
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'growInY', duration: 2000 },  // ❌ 螺旋被裁剪，部分区域缺失
  },
});

// ✅ 正确：helix 坐标系用 fadeIn
chart.options({
  type: 'interval',
  coordinate: { type: 'helix', startAngle: 0, endAngle: Math.PI * 6 },
  animate: {
    enter: { type: 'fadeIn', duration: 1000 },   // ✅ 渐显，无裁剪副作用
  },
});

// ✅ 极坐标（theta/polar）用 waveIn
chart.options({
  type: 'interval',
  coordinate: { type: 'theta' },
  animate: {
    enter: { type: 'waveIn', duration: 1000 },   // ✅ 极坐标专用扇形展开
  },
});
```

**根本原因**：`growInX/Y` 假设存在固定的直角基线（X=0 或 Y=0）作为裁剪起点，这在笛卡尔坐标系中成立；但 `helix` / `polar` 将坐标重映射到极坐标或螺旋路径后，该基线不再对应可见边界，裁剪结果是任意截断螺旋形状。
