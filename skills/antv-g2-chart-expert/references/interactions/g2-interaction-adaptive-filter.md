---
id: "g2-interaction-adaptive-filter"
title: "G2 AdaptiveFilter Adaptive Filtering Interaction"
description: |
  adaptiveFilter is an interaction in G2 v5 that automatically samples or aggregates data when the dataset is too large, causing chart rendering performance to degrade, thus maintaining smooth chart responsiveness.
  It is suitable for scenarios with large datasets such as line charts and scatter plots, and works best when combined with sliderFilter or scrollbarFilter.

library: "g2"
version: "5.x"
category: "interactions"
tags:
  - "adaptiveFilter"
  - "adaptive filtering"
  - "big data"
  - "performance optimization"
  - "sampling"
  - "interaction"

related:
  - "g2-interaction-slider-filter"
  - "g2-transform-sample"
  - "g2-mark-line-basic"

use_cases:
  - "Automatic downsampling for large dataset line charts to maintain smoothness"
  - "Dynamically adjusting data density during sliding window filtering"
  - "Automatic aggregation for scatter plots when data volume exceeds threshold"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/interaction/adaptive-filter"
---

## Core Concepts

`adaptiveFilter` listens to the chart's viewport changes and data scale. When the visible data volume exceeds the pixel capacity,
it automatically applies a sampling strategy (e.g., LTTB algorithm) to reduce the number of rendering points, avoiding performance issues caused by over-drawing.

It is typically used in conjunction with `sliderFilter` or `scrollbarFilter` to achieve "automatic data volume adaptation during sliding".

## Basic Usage

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'line',
  data: largeDataArray,   // Thousands of data entries
  encode: { x: 'date', y: 'value' },
  interaction: {
    adaptiveFilter: true,   // Enable adaptive filtering
  },
});

chart.render();
```

## Use with sliderFilter

```javascript
chart.options({
  type: 'view',
  data: largeDataArray,
  children: [
    {
      type: 'line',
      encode: { x: 'date', y: 'value' },
    },
  ],
  interaction: {
    sliderFilter: {
      x: { labelFormatter: (v) => new Date(v).toLocaleDateString() },
    },
    adaptiveFilter: true,   // Automatically sample after sliding window filtering
  },
  slider: {
    x: { values: [0, 0.3] },   // Initially display the first 30% of data
  },
});
```

## Configuration Options

```javascript
chart.options({
  interaction: {
    adaptiveFilter: {
      // Data volume threshold for triggering adaptive sampling (default 2000)
      // Sampling begins when the number of visible data points exceeds this value
      maxPoints: 2000,
    },
  },
});
```

## Common Errors and Fixes

### Error: Enabling adaptiveFilter for small datasets causes unexpected data filtering
```javascript
// ❌ Unnecessary: No need to enable for small datasets, may cause data loss misinterpretation
chart.options({
   smallData,   // Only 50 data entries
  interaction: { adaptiveFilter: true },
});

// ✅ Enable only for large datasets
// adaptiveFilter is suitable for scenarios with > 1000 data entries
chart.options({
  data: massiveData,
  interaction: { adaptiveFilter: true },
});
```