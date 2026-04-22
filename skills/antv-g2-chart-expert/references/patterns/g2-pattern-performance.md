---
id: "g2-pattern-performance"
title: "G2 Large Dataset Performance Optimization"
description: |
  Performance optimization strategies for G2 when handling large datasets: data pre-aggregation, LTTB downsampling,
  Canvas renderer confirmation, high-frequency real-time data throttling updates, etc.
  Provides data volume thresholds for various scenarios and specific optimization solutions.

library: "g2"
version: "5.x"
category: "patterns"
tags:
  - "performance optimization"
  - "performance"
  - "big data"
  - "Canvas"
  - "downsampling"
  - "aggregation"

related:
  - "g2-core-chart-init"
  - "g2-data-transform-patterns"

use_cases:
  - "Optimization for charts with data exceeding 10,000 entries"
  - "High-frequency update scenarios for real-time data streams"

difficulty: "advanced"
completeness: "full"
---

## Data Volume Threshold Reference

| Scenario | Data Volume | Recommended Solution |
|----------|------------------|---------------------|
| Line Chart | < 1,000 points | Direct Rendering |
| Line Chart | 1,000 ~ 10,000 points | Downsample to within 500 points |
| Line Chart | > 10,000 points | Backend Aggregation + Time Range Filtering |
| Scatter Plot | < 5,000 points | Direct Rendering |
| Scatter Plot | 5,000 ~ 50,000 points | Enable Canvas Rendering + Downsampling |

## Data Pre-Aggregation (The Most Important Optimization)

```javascript
// 100,000 daily granularity data → Aggregated into 365 monthly granularity
function aggregateTimeSeries(data, dateKey, valueKey, granularity = 'month') {
  const getGroupKey = (dateStr) => {
    const d = new Date(dateStr);
    if (granularity === 'month') {
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    }
    if (granularity === 'quarter') {
      return `${d.getFullYear()}-Q${Math.ceil((d.getMonth() + 1) / 3)}`;
    }
    return d.getFullYear().toString();
  };

  const groups = {};
  data.forEach(d => {
    const key = getGroupKey(d[dateKey]);
    if (!groups[key]) groups[key] = { date: key, sum: 0, count: 0, min: Infinity, max: -Infinity };
    groups[key].sum += d[valueKey];
    groups[key].count += 1;
    groups[key].min = Math.min(groups[key].min, d[valueKey]);
    groups[key].max = Math.max(groups[key].max, d[valueKey]);
  });

  return Object.values(groups)
    .map(g => ({ date: g.date, value: g.sum / g.count, min: g.min, max: g.max }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

chart.options({
  data: aggregateTimeSeries(rawData, 'timestamp', 'value'),
  type: 'line',
  encode: { x: 'date', y: 'value' },
});
```

## Line Chart Downsampling (LTTB Algorithm)

```javascript
// Largest Triangle Three Buckets (LTTB) Downsampling
// Retains the visually most important N points while preserving the line shape
function lttb(data, threshold) {
  const dataLength = data.length;
  if (threshold >= dataLength || threshold === 0) return data;

  const sampled = [];
  let sampledIndex = 0;
  const bucketSize = (dataLength - 2) / (threshold - 2);
  let a = 0;
  sampled[sampledIndex++] = data[a];

  for (let i = 0; i < threshold - 2; i++) {
    const rangeStart = Math.floor((i + 1) * bucketSize) + 1;
    const rangeEnd = Math.min(Math.floor((i + 2) * bucketSize) + 1, dataLength);

    let avgX = 0, avgY = 0;
    const avgRangeStart = Math.floor((i + 1) * bucketSize) + 1;
    const avgRangeEnd = Math.min(Math.floor((i + 2) * bucketSize) + 1, dataLength);
    for (let j = avgRangeStart; j < avgRangeEnd; j++) {
      avgX += data[j].x;
      avgY += data[j].y;
    }
    avgX /= (avgRangeEnd - avgRangeStart);
    avgY /= (avgRangeEnd - avgRangeStart);

    let maxArea = -1;
    let nextA = rangeStart;
    const pointAX = data[a].x;
    const pointAY = data[a].y;
    for (let j = rangeStart; j < rangeEnd; j++) {
      const area = Math.abs(
        (pointAX - avgX) * (data[j].y - pointAY) -
        (pointAX - data[j].x) * (avgY - pointAY)
      );
      if (area > maxArea) { maxArea = area; nextA = j; }
    }
    sampled[sampledIndex++] = data[nextA];
    a = nextA;
  }
  sampled[sampledIndex++] = data[dataLength - 1];
  return sampled;
}

// Downsample 10,000 points to 500
const sampledData = lttb(rawData, 500);
chart.options({  sampledData, type: 'line', encode: { x: 'x', y: 'y' } });
```

## Confirm Using Canvas Renderer

```javascript
// G2 defaults to Canvas rendering, which is much faster than SVG
// Confirm that it hasn't been switched to SVG when dealing with large datasets
const chart = new Chart({
  container: 'container',
  renderer: 'canvas',   // default, 5-10x faster than SVG with large datasets
  width: 800,
  height: 400,
});
```

## High-Frequency Real-Time Data Update Optimization

```javascript
// Throttling with requestAnimationFrame (update at most once per frame)
let pendingData = null;
let rafId = null;

function updateChart(newData) {
  pendingData = newData;

  if (!rafId) {
    rafId = requestAnimationFrame(() => {
      if (pendingData) {
        chart.changeData(pendingData);
        pendingData = null;
      }
      rafId = null;
    });
  }
}

// Simulate real-time data stream (new data every 100ms)
setInterval(() => {
  const newPoint = { time: Date.now(), value: Math.random() * 100 };
  updateChart([...currentData.slice(-500), newPoint]);  // Keep only the latest 500 points
}, 100);
```

## Common Errors and Fixes

```javascript
// ❌ Passing 100,000 rows of data directly to G2 causes the page to freeze
chart.options({ data: tenThousandRows });

// ✅ Aggregate or downsample to a reasonable number (< 1000 points) first
chart.options({ data: aggregateTimeSeries(tenThousandRows, 'date', 'value') });
```