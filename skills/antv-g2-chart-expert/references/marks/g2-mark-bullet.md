---
id: "g2-mark-bullet"
title: "G2 Bullet Chart Mark"
description: |
  Bullet Chart Mark. Implemented using a combination of interval and point in a view, it compares actual values with target values.
  Suitable for performance monitoring, KPI display, progress tracking, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "bullet chart"
  - "bullet"
  - "KPI"
  - "progress"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-gauge"

use_cases:
  - "Performance metric monitoring"
  - "KPI dashboard"
  - "Budget execution tracking"

anti_patterns:
  - "Time trend analysis should use line charts"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/bullet"
---

## Core Concepts

A Bullet Chart is a compact visualization for performance metrics, displaying:
- **Actual Value Bar**: The current achieved value
- **Target Marker**: The desired target value
- **Performance Bands**: Background color bands indicating poor/average/good levels

**Applicable Scenarios:**
- Dashboard KPI display
- Performance metric monitoring
- Resource utilization monitoring

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

const data = [
  { title: 'Sales Completion Rate', ranges: 100, measures: 80, target: 85 },
];

chart.options({
  type: 'view',
  coordinate: { transform: [{ type: 'transpose' }] },
  children: [
    {
      type: 'interval',
      data,
      encode: { x: 'title', y: 'ranges', color: '#f0efff' },
      style: { maxWidth: 30 },
    },
    {
      type: 'interval',
      data,
      encode: { x: 'title', y: 'measures', color: '#5B8FF9' },
      style: { maxWidth: 20 },
    },
    {
      type: 'point',
      data,
      encode: {
        x: 'title',
        y: 'target',
        shape: 'line',
        color: '#3D76DD',
        size: 8,
      },
    },
  ],
});

chart.render();
```

## Common Variants

### Multi-Metric Bullet Chart

```javascript
const multiData = [
  { metric: 'CPU Usage', ranges: 100, measures: 65, target: 80 },
  { metric: 'Memory Usage', ranges: 100, measures: 45, target: 70 },
  { metric: 'Disk Usage', ranges: 100, measures: 88, target: 85 },
];

chart.options({
  type: 'view',
  coordinate: { transform: [{ type: 'transpose' }] },
  children: [
    { type: 'interval', data: multiData, encode: { x: 'metric', y: 'ranges', color: '#f5f5f5' } },
    { type: 'interval', data: multiData, encode: { x: 'metric', y: 'measures', color: '#52c41a' } },
    { type: 'point', data: multiData, encode: { x: 'metric', y: 'target', shape: 'line', size: 6 } },
  ],
});
```

### With Performance Range

```javascript
const transformedData = [
  { title: 'Project Progress', value: 40, level: 'Poor' },
  { title: 'Project Progress', value: 30, level: 'Good' },
  { title: 'Project Progress', value: 30, level: 'Excellent' },
];

chart.options({
  type: 'view',
  coordinate: { transform: [{ type: 'transpose' }] },
  children: [
    {
      type: 'interval',
      data: transformedData,
      encode: { x: 'title', y: 'value', color: 'level' },
      transform: [{ type: 'stackY' }],
      scale: {
        color: { domain: ['Poor', 'Good', 'Excellent'], range: ['#ffebee', '#fff3e0', '#e8f5e8'] },
      },
    },
    // ... actual value and target value
  ],
});
```

### Vertical Bullet Chart

```javascript
chart.options({
  type: 'view',
  // Do not use transpose
  children: [
    { type: 'interval', data, encode: { x: 'metric', y: 'ranges', color: '#f0f0f0' } },
    { type: 'interval', data, encode: { x: 'metric', y: 'measures', color: '#52c41a' } },
    { type: 'point', data, encode: { x: 'metric', y: 'target', shape: 'line', size: 6 } },
  ],
});
```

## Complete Type Reference

```typescript
interface BulletData {
  title: string;      // Metric name
  ranges: number;     // Background range (usually 100)
  measures: number;   // Actual value
  target: number;     // Target value
}

// A bullet chart consists of three layers:
// 1. interval - Background range
// 2. interval - Actual value bar
// 3. point (shape: 'line') - Target marker
```

## Bullet Chart vs Gauge

| Feature | Bullet Chart | Gauge |
|---------|----------------|----------------|
| Space Occupancy | Compact | Larger |
| Information Volume | Multi-indicator | Single-indicator |
| Applicable Scenarios | Dashboard | Large Screen Display |

## Common Errors and Fixes

### Error 1: Missing transpose

```javascript
// ❌ Problem: Default is vertical direction
coordinate: {}

// ✅ Correct: Horizontal bullet chart requires transpose
coordinate: { transform: [{ type: 'transpose' }] }
```

### Error 2: Target Value Markers Not Prominent

```javascript
// ❌ Issue: Target value uses default point shape
encode: { shape: 'point' }

// ✅ Correct: Use line shape
encode: { shape: 'line', size: 8 }
```